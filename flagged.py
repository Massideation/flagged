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
ALERT_HISTORY_PATH = BASE_DIR / "alert_history.json"
FEEDBACK_PATH = BASE_DIR / "feedback.json"

DEFAULT_ALERT_CHANNELS = {
    "opportunities": {
        "label": "Opportunity Radar",
        "mode": "immediate",
        "min_score": 7,
        "description": "Actual people, customers, friends, partnerships, paid work, and asks worth deciding on."
    },
    "money_admin": {
        "label": "Money/Admin",
        "mode": "digest",
        "min_score": 9,
        "description": "Bills, receipts, refunds, affiliate payouts, account notices, and other admin."
    },
    "learning_events": {
        "label": "Learning/Events",
        "mode": "digest",
        "min_score": 8,
        "description": "Newsletters, webinars, launches, and event blasts that may be useful later."
    },
    "sales_pitches": {
        "label": "Sales Pitches",
        "mode": "mute",
        "min_score": 10,
        "description": "People or companies selling you something."
    },
    "muted": {
        "label": "Muted",
        "mode": "mute",
        "min_score": 10,
        "description": "Low-value noise."
    }
}

# ── Config ────────────────────────────────────────────────────────────────────
def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            "config.json not found. Copy config.example.json to config.json and fill in your values."
        )
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    config.setdefault("alert_channels", DEFAULT_ALERT_CHANNELS)
    return config

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

def load_alert_history():
    if ALERT_HISTORY_PATH.exists():
        with open(ALERT_HISTORY_PATH) as f:
            return json.load(f)
    return {}

def save_alert_history(history: dict):
    with open(ALERT_HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2)

def load_feedback():
    if FEEDBACK_PATH.exists():
        with open(FEEDBACK_PATH) as f:
            return json.load(f)
    return {"telegram_update_offset": None, "items": []}

def save_feedback(feedback: dict):
    with open(FEEDBACK_PATH, "w") as f:
        json.dump(feedback, f, indent=2)

def remember_alert(email: dict, score_data: dict, account_label: str) -> str:
    """Store a compact local record so Telegram feedback buttons have an id."""
    import hashlib

    alert_id = hashlib.sha1(f"{account_label}:{email['id']}".encode()).hexdigest()[:12]
    history = load_alert_history()
    history[alert_id] = {
        "account": account_label,
        "email_id": email["id"],
        "from": email["from"],
        "subject": email["subject"],
        "score_data": score_data,
        "created_at": int(time.time())
    }
    save_alert_history(history)
    return alert_id

# ── Gmail Auth ────────────────────────────────────────────────────────────────
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_gmail_service(credentials_path: str, token_path: str, label: str):
    """
    Authenticate with Gmail using OAuth2.
    One credentials.json works for all accounts — each gets its own token file.
    First run opens a browser window to authorize. Subsequent runs are silent.
    """
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

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

    alert_channels = json.dumps(config.get("alert_channels", DEFAULT_ALERT_CHANNELS), indent=2)

    prompt = f"""You are Flagged, a local opportunity-radar classifier for a specific person.

Your job is not to surface every important-looking email. Your job is to decide whether this email creates a choice or opportunity the person may want to see.

Core rule:
- Immediate alerts are for actual people reaching out: customers, friends, warm contacts, partners, prospects, speaking/media requests, paid work, or direct asks that likely need a response.
- Do NOT immediately alert for bills, receipts, Uber/travel receipts, newsletters, event blasts, affiliate payouts, automated account updates, generic promotions, or people selling the person something.
- Money/admin and affiliate messages can be useful, but usually belong in a digest unless they require urgent action.

Here is their priority context:

{priorities_context}

Alert channel settings:
{alert_channels}

─────────────────────────────
Classify this incoming email:

From: {email['from']}
Subject: {email['subject']}
Has attachment: {email['has_attachment']}
Preview: {email['snippet']}
─────────────────────────────

Score this email from 1-10 for whether it deserves attention based on the person's priorities above.

Return ONLY a raw JSON object. No explanation. No markdown. No backticks.

{{
  "score": <integer 1-10>,
  "reason": "<one concise sentence>",
  "category": "<one of: customer|friend|opportunity|partnership|media|speaking|meeting|money_admin|affiliate|learning_event|newsletter|sales_pitch|notification|other>",
  "sender_type": "<one of: person|company|automated|newsletter|sales>",
  "relationship": "<one of: knows_me|customer|friend|prospect|partner|vendor|platform|unknown>",
  "ask_type": "<one of: needs_reply|decision|fyi|payment|promo|sales|none>",
  "alert_channel": "<one of: opportunities|money_admin|learning_events|sales_pitches|muted>",
  "alert_mode": "<one of: immediate|digest|mute>",
  "confidence": <integer 1-10>
}}"""

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

        return normalize_score_data(json.loads(raw), config)

    except requests.exceptions.ConnectionError:
        log.error("Cannot reach LM Studio. Is the Local Server running?")
        return normalize_score_data({"score": 5, "reason": "LM Studio unreachable", "category": "other"}, config)
    except Exception as e:
        log.warning(f"Scoring failed: {e}")
        return normalize_score_data({"score": 5, "reason": "Classification error", "category": "other"}, config)

def normalize_score_data(score_data: dict, config: dict) -> dict:
    """Backfill newer opportunity-radar fields when older models omit them."""
    channels = config.get("alert_channels", DEFAULT_ALERT_CHANNELS)
    category = score_data.get("category", "other")

    category_to_channel = {
        "customer": "opportunities",
        "friend": "opportunities",
        "opportunity": "opportunities",
        "partnership": "opportunities",
        "media": "opportunities",
        "speaking": "opportunities",
        "meeting": "opportunities",
        "money_admin": "money_admin",
        "affiliate": "money_admin",
        "learning_event": "learning_events",
        "newsletter": "learning_events",
        "sales_pitch": "sales_pitches",
        "notification": "muted",
        "other": "muted",
    }

    channel = score_data.get("alert_channel") or category_to_channel.get(category, "muted")
    channel_config = channels.get(channel, channels.get("muted", DEFAULT_ALERT_CHANNELS["muted"]))

    score_data["score"] = int(score_data.get("score", 1))
    score_data["category"] = category
    score_data["sender_type"] = score_data.get("sender_type", "unknown")
    score_data["relationship"] = score_data.get("relationship", "unknown")
    score_data["ask_type"] = score_data.get("ask_type", "none")
    score_data["alert_channel"] = channel
    score_data["alert_mode"] = score_data.get("alert_mode") or channel_config.get("mode", "mute")
    score_data["confidence"] = int(score_data.get("confidence", 5))
    return score_data

def alert_decision(score_data: dict, config: dict) -> dict:
    """Return how this email should be handled: immediate, digest, or mute."""
    channels = config.get("alert_channels", DEFAULT_ALERT_CHANNELS)
    channel_name = score_data.get("alert_channel", "muted")
    channel = channels.get(channel_name, channels.get("muted", DEFAULT_ALERT_CHANNELS["muted"]))
    mode = score_data.get("alert_mode") or channel.get("mode", "mute")
    min_score = int(channel.get("min_score", config.get("score_threshold", 7)))
    score = int(score_data.get("score", 1))

    # Immediate alerts are deliberately stricter than generic importance:
    # they need an opportunity channel and the configured threshold.
    should_send = mode == "immediate" and score >= min_score
    return {
        "mode": mode,
        "channel": channel_name,
        "channel_label": channel.get("label", channel_name),
        "min_score": min_score,
        "send_now": should_send,
    }

def process_telegram_feedback(config: dict):
    """Collect Telegram button feedback into feedback.json for tuning."""
    telegram_config = config.get("telegram", {})
    if telegram_config.get("feedback_buttons", True) is False:
        return

    bot_token = telegram_config["bot_token"]
    feedback = load_feedback()
    params = {"timeout": 1}
    if feedback.get("telegram_update_offset") is not None:
        params["offset"] = feedback["telegram_update_offset"]

    try:
        r = requests.get(
            f"https://api.telegram.org/bot{bot_token}/getUpdates",
            params=params,
            timeout=5,
        )
        r.raise_for_status()
        updates = r.json().get("result", [])
    except Exception as e:
        log.warning(f"Telegram feedback check failed: {e}")
        return

    history = load_alert_history()
    changed = False

    for update in updates:
        feedback["telegram_update_offset"] = update["update_id"] + 1
        callback = update.get("callback_query")
        if not callback:
            changed = True
            continue

        data = callback.get("data", "")
        if not data.startswith("fb:"):
            changed = True
            continue

        _, action, alert_id = data.split(":", 2)
        alert = history.get(alert_id, {})
        feedback.setdefault("items", []).append({
            "created_at": int(time.time()),
            "action": action,
            "alert_id": alert_id,
            "account": alert.get("account"),
            "from": alert.get("from"),
            "subject": alert.get("subject"),
            "score_data": alert.get("score_data", {}),
        })

        try:
            requests.post(
                f"https://api.telegram.org/bot{bot_token}/answerCallbackQuery",
                json={
                    "callback_query_id": callback["id"],
                    "text": "Feedback saved",
                    "show_alert": False,
                },
                timeout=5,
            )
        except Exception:
            pass

        changed = True
        log.info(f"Feedback saved: {action} for {alert_id}")

    if changed:
        save_feedback(feedback)

# ── Telegram Alert ────────────────────────────────────────────────────────────
CATEGORY_EMOJI = {
    "customer": "💬",
    "friend": "👋",
    "opportunity": "⭐",
    "meeting": "📅",
    "media": "📺",
    "speaking": "🎙",
    "partnership": "🔗",
    "money_admin": "💵",
    "affiliate": "💸",
    "learning_event": "🎟",
    "newsletter": "📰",
    "sales_pitch": "🚫",
    "notification": "🔔",
    "other": "📧"
}

def send_telegram(email: dict, score_data: dict, account_label: str, config: dict, decision: dict):
    """Send a Telegram alert for a high-priority email."""
    bot_token = config["telegram"]["bot_token"]
    chat_id = config["telegram"]["chat_id"]

    alert_id = remember_alert(email, score_data, account_label)
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
        f"{urgency_badge} — {decision['channel_label']} ({account_label})\n\n"
        f"{cat_emoji} {category.upper()}{attachment_note}\n"
        f"From: {email['from']}\n"
        f"Subject: {email['subject']}\n"
        f"Score: {score}/10 — {reason}\n"
        f"Sender: {score_data.get('sender_type')} / {score_data.get('relationship')}\n"
        f"Ask: {score_data.get('ask_type')}\n\n"
        f"“{preview}...”"
    )

    try:
        payload = {
            "chat_id": chat_id,
            "text": message,
        }
        if config.get("telegram", {}).get("feedback_buttons", True) is not False:
            payload["reply_markup"] = {
                "inline_keyboard": [[
                    {"text": "Good alert", "callback_data": f"fb:good:{alert_id}"},
                    {"text": "Mute type", "callback_data": f"fb:mute:{alert_id}"},
                    {"text": "Digest only", "callback_data": f"fb:digest:{alert_id}"}
                ]]
            }

        r = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json=payload,
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
        process_telegram_feedback(config)

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
                    decision = alert_decision(result, config)
                    score = result["score"]
                    log.info(
                        f"  [{score}/10 {decision['mode']}:{decision['channel']}] "
                        f"{email['subject'][:55]} | {result['reason']}"
                    )

                    if decision["send_now"]:
                        send_telegram(email, result, label, config, decision)
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
