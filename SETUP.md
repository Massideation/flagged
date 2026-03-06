# Setup Guide

## Step 1 — Dependencies

```bash
pip3 install -r requirements.txt
```

---

## Step 2 — LM Studio

1. Open LM Studio on your Mac Mini
2. Click **Local Server** in the left sidebar
3. Load your model (GLM-4.7 or Phi-3 Mini recommended)
4. Click **Start Server** — runs at `http://localhost:1234`
5. Copy the exact model name string shown and paste it into `config.json` under `lm_studio.model`

---

## Step 3 — Telegram Bot Token + Chat ID

You already have a bot. Get the two values you need:

**Bot Token:**
Open Telegram → search `@BotFather` → `/mybots` → select your bot → copy the API Token
Looks like: `7123456789:AAHxxxxxxx`

**Your Chat ID:**
Open Telegram → search `@userinfobot` → start it → it replies with your ID
Looks like: `123456789`

Add both to `config.json`.

---

## Step 4 — Google Cloud Setup (One-Time)

You only need ONE Google Cloud project for all 3 Gmail accounts.

**4a. Create project:**
1. Go to https://console.cloud.google.com
2. Create new project → name it "Email Monitor"
3. Enable Gmail API: APIs & Services → Enable APIs & Services → search "Gmail API" → Enable

**4b. Create OAuth credentials:**
1. APIs & Services → Credentials → Create Credentials → OAuth Client ID
2. If prompted, configure the consent screen first:
   - User type: External
   - App name: Email Monitor
   - Add your email as a test user
3. Application type: **Desktop App**
4. Name it anything → Create
5. Download the JSON → rename it `credentials.json`
6. Copy `credentials.json` into your `email_monitor/` folder

**That one file works for all 3 accounts.**

---

## Step 5 — Config

```bash
cp config.example.json config.json
```

Edit `config.json`:
- Set your Telegram `bot_token` and `chat_id`
- Set `lm_studio.model` to match exact model name from LM Studio
- Update account `label` names to match your actual accounts
- All three accounts share the same `credentials.json` — only the `token_path` differs per account

---

## Step 6 — First Run (Authorize Gmail Accounts)

```bash
python3 flagged.py
```

A browser window opens for each Gmail account asking you to sign in and grant read-only access. After authorizing all three, token files are saved and the monitor starts polling. You won't need to do this again unless tokens expire.

---

## Step 7 — Run as Background Service (Always On)

```bash
# Update the path in the plist if your username isn't 'stack'
nano com.flagged.emailmonitor.plist
# Change /Users/stack/email_monitor to your actual path

# Install and start
cp com.flagged.emailmonitor.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.flagged.emailmonitor.plist
launchctl start com.flagged.emailmonitor
```

**Check it's running:**
```bash
launchctl list | grep stack
```

**Restart after config changes:**
```bash
launchctl stop com.flagged.emailmonitor
launchctl start com.flagged.emailmonitor
```

**Remove the service:**
```bash
launchctl unload ~/Library/LaunchAgents/com.flagged.emailmonitor.plist
```

---

## Step 8 — Push to GitHub

```bash
cd email_monitor
git init
git add .
git status  # Verify: config.json and credentials.json should NOT appear
git commit -m "init email monitor"
git remote add origin https://github.com/yourname/email_monitor.git
git push -u origin main
```

The `.gitignore` prevents secrets from ever being committed. Only safe files go to GitHub.

---

## Updating PRIORITIES.md

Edit `PRIORITIES.md` anytime to tune what gets surfaced. Examples of things to add:
- Known high-priority sender domains (e.g., `arbitrum.foundation`)
- New projects you're working on
- Specific keywords that should always trigger an alert

Changes apply on the next poll — no restart needed.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `config.json not found` | `cp config.example.json config.json` and fill in values |
| LM Studio not responding | Open LM Studio → confirm Local Server is running and model is loaded |
| Gmail auth error | Delete `token_ACCOUNTNAME.pkl` and re-run to re-authorize |
| Wrong model name | Check LM Studio Local Server tab → copy exact model string |
| Telegram not sending | Verify bot token and chat ID; make sure you've started the bot in Telegram |
| High CPU on Mac Mini | Switch to Phi-3 Mini or Llama 3.2 3B — much faster for classification |
