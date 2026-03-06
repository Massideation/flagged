#!/usr/bin/env python3
"""
Flagged — Local AI Email Monitor
─────────────────────────────────────────────────────────
Monitors 3 Gmail accounts, scores importance via LM Studio (local, private),
fires Telegram alerts for emails scoring above your threshold.

Read-only. No auto-reply. Just surfaces what matters.
Data stays on your Mac Mini — only Gmail OAuth touches the internet.
"""

import os
import json
import time
import pickle
import logging
from pathlib import Path

import requests
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(Path(__file__).parent / "flagged.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"
PRIORITIES_PATH = BASE_DIR / "PRIORITIES.md"
SEEN_PATH = BASE_DIR / "seen_emails.json"

# ── Config ────────────────────────────────────────────────────────────────────
def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            "config.json not found. Copy config.example.json to config.json and fill in your values."
        )
    with open(CONFIG_PATH) as f:
        return json.load(f)

def load_priorities():
    """Load your personal context window for the classifier prompt."""
    if PRIORITIES_PATH.exists():
        with open(PRIORITIES_PATH) as f:
            return f.read()
    return ""

# ── Seen email tracker ────────────────────────────────────────────────────────
def load_seen():
    if SEEN_PATH.exists():
        with open(SEEN_PATH) as f:
            return set(json.load(f))
    return set()

def save_seen(seen: set):
    with open(SEEN_PATH, "w") as f:
        json.dump(list(seen), f)

# ── Gmail Auth ────────────────────────────────────────────────────────────────
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_gmail_service(credentials_path: str, token_path: str, label: str):
    """
    Authenticate with Gmail using OAuth2.
    One credentials.json works for all accounts — each gets its own token file.
    First run opens a browser window to authorize. Subsequent runs are silent.
    """
    creds = None
    token_file = Path(token_path)

    if token_file.exists():
        with open(token_file, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            log.info(f"Refreshing token for: {label}")
            creds.refresh(Request())
        else:
            log.info(f"Opening browser to authorize Gmail account: {label}")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_file, "wb") as f:
            pickle.dump(creds, f)
        log.info(f"Token saved for: {label}")

    return build("gmail", "v1", credentials=creds)

# ── Gmail Fetch ───────────────────────────────────────────────────────────────
def fetch_unread_emails(service, max_results=20):
    """
    Fetch recent unread inbox emails.
    Only retrieves metadata (headers + snippet) — never the full body.
    """
    result = service.users().messages().list(
        userId="me",
        labelIds=["INBOX", "UNREAD"],
        maxResults=max_results
    ).execute()

    messages = result.get("messages", [])
    emails = []

    for msg in messages:
        data = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["From", "Subject", "Date", "To"]
        ).execute()

        headers = {h["name"]: h["value"] for h in data["payload"]["headers"]}
        has_attachment = any(
            p.get("filename") for p in data["payload"].get("parts", [])
        )

        emails.append({
            "id": msg["id"],
            "from": headers.get("From", "Unknown"),
            "subject": headers.get("Subject", "(no subject)"),
            "date": headers.get("Date", ""),
            "to": headers.get("To", ""),
            "snippet": data.get("snippet", "")[:400],
            "has_attachment": has_attachment,
        })

    return emails

# ── LM Studio Classifier ──────────────────────────────────────────────────────
def score_email(email: dict, priorities_context: str, config: dict) -> dict:
    """
    Score email importance using your local LM Studio model.
    Sends: sender, subject, 400-char preview, attachment flag.
    Never sends the full email body.
    Everything stays on your Mac Mini.
    """
    lm_url = config["lm_studio"]["url"]
    model = config["lm_studio"]["model"]

    prompt = f"""You are an email classifier for a specific person. Here is their priority context:

{priorities_context}

─────────────────────────────
Classify this incoming email:

From: {email['from']}
Subject: {email['subject']}
Has attachment: {email['has_attachment']}
Preview: {email['snippet']}
─────────────────────────────

Score this email from 1-10 for urgency based on the person's priorities above.

Return ONLY a raw JSON object. No explanation. No markdown. No backticks.

{{"score": <integer 1-10>, "reason": "<one concise sentence>", "category": "<one of: invite|deal|deadline|media|partnership|intro|inquiry|newsletter|notification|other>"}}"""

    try:
        response = requests.post(
            f"{lm_url}/v1/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 150
            },
            timeout=45
        )
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"].strip()

        # Strip markdown fences if model adds them
        raw = raw.replace("```json", "").replace("```", "").strip()

        # Find the JSON object if there's any preamble
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            raw = raw[start:end]

        return json.loads(raw)

    except requests.exceptions.ConnectionError:
        log.error("Cannot reach LM Studio. Is the Local Server running?")
        return {"score": 5, "reason": "LM Studio unreachable", "category": "other"}
    except Exception as e:
        log.warning(f"Scoring failed: {e}")
        return {"score": 5, "reason": "Classification error", "category": "other"}

# ── Telegram Alert ────────────────────────────────────────────────────────────
CATEGORY_EMOJI = {
    "invite": "🎟",
    "deal": "🤝",
    "deadline": "⏰",
    "media": "📺",
    "partnership": "🔗",
    "intro": "👋",
    "inquiry": "💬",
    "newsletter": "📰",
    "notification": "🔔",
    "other": "📧"
}

def send_telegram(email: dict, score_data: dict, account_label: str, config: dict):
    """Send a Telegram alert for a high-priority email."""
    bot_token = config["telegram"]["bot_token"]
    chat_id = config["telegram"]["chat_id"]

    score = score_data["score"]
    reason = score_data["reason"]
    category = score_data.get("category", "other")
    cat_emoji = CATEGORY_EMOJI.get(category, "📧")

    if score >= 9:
        urgency_badge = "🔴 URGENT"
    elif score >= 7:
        urgency_badge = "🟠 PRIORITY"
    else:
        urgency_badge = "🟡 HEADS UP"

    preview = email["snippet"][:180]
    attachment_note = " 📎" if email.get("has_attachment") else ""

    message = (
        f"{urgency_badge} — *{account_label}*\n\n"
        f"{cat_emoji} *{category.upper()}*{attachment_note}\n"
        f"*From:* {email['from']}\n"
        f"*Subject:* {email['subject']}\n"
        f"*Score:* {score}/10 — {reason}\n\n"
        f"_{preview}..._"
    )

    try:
        r = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            },
            timeout=10
        )
        r.raise_for_status()
        log.info(f"✅ Telegram alert sent: [{score}/10] {email['subject'][:60]}")
    except Exception as e:
        log.error(f"Telegram failed: {e}")

def send_startup_message(config: dict):
    """Send a message when the monitor boots up."""
    try:
        accounts = [a["label"] for a in config["accounts"]]
        requests.post(
            f"https://api.telegram.org/bot{config['telegram']['bot_token']}/sendMessage",
            json={
                "chat_id": config["telegram"]["chat_id"],
                "text": (
                    f"✅ *Email Monitor running*\n"
                    f"Watching: {', '.join(accounts)}\n"
                    f"Threshold: {config.get('score_threshold', 7)}/10\n"
                    f"Checking every {config.get('poll_interval_seconds', 300) // 60} min"
                ),
                "parse_mode": "Markdown"
            },
            timeout=10
        )
    except:
        pass

# ── Main Loop ─────────────────────────────────────────────────────────────────
def run():
    config = load_config()
    priorities = load_priorities()
    seen = load_seen()
    threshold = config.get("score_threshold", 7)
    interval = config.get("poll_interval_seconds", 300)
    max_emails = config.get("max_emails_per_check", 20)

    if not priorities:
        log.warning("PRIORITIES.md not found — using generic scoring. Edit PRIORITIES.md to tune alerts.")

    log.info(f"Starting Email Monitor — {len(config['accounts'])} accounts, threshold {threshold}/10, every {interval}s")
    send_startup_message(config)

    while True:
        for account in config["accounts"]:
            label = account["label"]
            try:
                log.info(f"Checking: {label}")
                service = get_gmail_service(
                    credentials_path=account["credentials_path"],
                    token_path=account["token_path"],
                    label=label
                )
                emails = fetch_unread_emails(service, max_results=max_emails)
                new_count = 0

                for email in emails:
                    key = f"{label}:{email['id']}"
                    if key in seen:
                        continue

                    seen.add(key)
                    new_count += 1

                    result = score_email(email, priorities, config)
                    score = result["score"]
                    log.info(f"  [{score}/10] {email['subject'][:55]} | {result['reason']}")

                    if score >= threshold:
                        send_telegram(email, result, label, config)
                        time.sleep(1)  # Telegram rate limit buffer

                if new_count:
                    save_seen(seen)
                    log.info(f"  {new_count} new emails processed for {label}")
                else:
                    log.info(f"  No new emails for {label}")

            except Exception as e:
                log.error(f"Error on account {label}: {e}", exc_info=True)

        log.info(f"Cycle complete. Next check in {interval}s...")
        time.sleep(interval)

if __name__ == "__main__":
    run()
