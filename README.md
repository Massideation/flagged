# 📬 Flagged

**Your inbox, filtered by what actually matters. Local AI. Zero cloud. Telegram alerts.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![LM Studio](https://img.shields.io/badge/LM%20Studio-compatible-green.svg)](https://lmstudio.ai/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

> *"I missed an Arbitrum event invite because it was buried in 300 unread emails. I built this so it never happens again."*
> — Stack ([@MSanchezWorld](https://github.com/MSanchezWorld))

---

## What It Does

Flagged monitors your Gmail accounts every few minutes, scores every unread email 1–10 using a **local AI model running on your own machine**, and fires a Telegram alert when something scores above your threshold.

**You stay in the loop. You respond in Gmail. Flagged just makes sure nothing important gets buried.**

```
🔴 URGENT — Main Inbox

🎟 INVITE
From: events@arbitrum.foundation
Subject: You're invited to Arbitrum Dev Day
Score: 9/10 — Direct event invite with RSVP deadline from known crypto project

"Join us on March 15th. We'd love for you to speak..."
```

---

## Why Flagged?

| Feature | Flagged | Zapier/email tools | SaaS AI email |
|---|---|---|---|
| **Your data stays local** | ✅ | ❌ | ❌ |
| **No subscription fee** | ✅ | ❌ | ❌ |
| **Tunable to your world** | ✅ | Limited | Limited |
| **Works across multiple inboxes** | ✅ | Paid tier | Paid tier |
| **Runs 24/7 on your own machine** | ✅ | Cloud-dependent | Cloud-dependent |
| **No vendor lock-in** | ✅ | ❌ | ❌ |

---

## Privacy Model

Flagged is built local-first by design:

- **Your email body never leaves your machine.** Only the sender name, subject line, and a 400-character preview snippet are passed to the AI model — and that model runs locally.
- **LM Studio runs entirely on your hardware.** GLM-4, Phi-3, Llama — whatever you choose, it never phones home.
- **Gmail OAuth is read-only.** Flagged cannot send, delete, or modify emails. It can only read.
- **The only outbound connection is your Telegram bot firing alerts.** That's it.

---

## Requirements

- **Mac, Linux, or Windows** with Python 3.9+
- **[LM Studio](https://lmstudio.ai/)** with a model loaded (see recommendations below)
- **Gmail account(s)** — up to as many as you want
- **Telegram bot** — takes 2 minutes to create via [@BotFather](https://t.me/botfather)
- **Google Cloud project** (free) for Gmail API access

---

## Install

**Mac / Linux — one line:**
```bash
curl -fsSL https://raw.githubusercontent.com/MSanchezWorld/flagged/main/install.sh | bash
```

**Windows — one line (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/MSanchezWorld/flagged/main/install.ps1 | iex
```

The installer clones the repo, installs dependencies, and launches an **interactive setup wizard** that walks you through every step — Telegram bot, Gmail API, model selection, and background service — no manual config editing required.

**Manual install:**
```bash
git clone https://github.com/MSanchezWorld/flagged
cd flagged
pip install -r requirements.txt
python setup_wizard.py
```

Full walkthrough → [SETUP.md](SETUP.md)

---

## Model Recommendations

Flagged works with any OpenAI-compatible local model via LM Studio. For email classification, **smaller is better** — you want fast and accurate, not large and slow.

| Model | RAM | Speed | Notes |
|---|---|---|---|
| **Qwen2.5 3B Instruct** ⭐ | ~2GB | ⚡⚡⚡ | **Default — best-in-class for classification at this size** |
| **Qwen3 4B Instruct** | ~3GB | ⚡⚡⚡ | Slightly more capable, still very fast |
| **Phi-3.5 Mini** | ~2.5GB | ⚡⚡⚡ | Excellent reasoning, great JSON output |
| **Llama 3.2 3B Instruct** | ~2GB | ⚡⚡⚡ | Reliable fallback, strong instruction following |
| **SmolLM3 3B** | ~2GB | ⚡⚡⚡ | Newest option, outperforms Llama 3.2 3B on benchmarks |
| **GLM-4.7 / LFM** | ~5-8GB | ⚡ | Works, but overkill — wastes RAM you need for other work |

**On a 16GB machine:** use Qwen2.5 3B. It uses ~2GB RAM, classifies emails in under a second, and leaves your machine free for everything else.

---

## Tuning Flagged to Your World

The `PRIORITIES.md` file is Flagged's brain. It tells the AI model who you are, what you care about, and what should wake you up vs. what should stay quiet.

Edit it to match your life:

```markdown
## Raise to 9-10 (Drop everything)
- Event invites with RSVP deadlines
- Direct outreach from [your key contacts/orgs]
- Speaking or podcast requests
- Term sheets or partnership proposals

## Keep at 1-4 (Do not alert)
- Marketing newsletters
- Automated platform notifications
```

Changes apply on the next poll — no restart needed.

---

## Running as a Background Service

**macOS (always-on, survives reboots):**
```bash
cp com.flagged.emailmonitor.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.flagged.emailmonitor.plist
```

**Linux (systemd):**
```bash
# See SETUP.md for systemd service setup
```

**Windows (Task Scheduler):**
```bash
# See SETUP.md for Windows setup
```

---

## Multiple Inboxes

Flagged supports unlimited Gmail accounts. Add as many as you want in `config.json`:

```json
"accounts": [
  { "label": "Personal", "credentials_path": "credentials.json", "token_path": "token_personal.pkl" },
  { "label": "Work",     "credentials_path": "credentials.json", "token_path": "token_work.pkl" },
  { "label": "Projects", "credentials_path": "credentials.json", "token_path": "token_projects.pkl" }
]
```

One `credentials.json` works for all accounts. Each account gets its own token file after a one-time browser authorization.

---

## Telegram Alert Format

```
🔴 URGENT — Personal

🤝 PARTNERSHIP
From: founder@coolproject.xyz
Subject: Collab idea — would love to chat
Score: 8/10 — Direct personal outreach, specific ask, no template language

"Hey, I've been following your work on Stackit and wanted to..."
```

Emoji legend:
- 🔴 `9-10` Urgent
- 🟠 `7-8` Priority
- 🟡 `5-6` Worth reviewing (if you lower your threshold)

---

## Contributing

Pull requests welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

Ideas for contributions:
- **Outlook / Microsoft 365 support** — big one
- **Slack / Discord notification support** (alongside Telegram)
- **Web dashboard** for viewing scored email history
- **Webhook support** for custom integrations
- **Linux systemd service template**
- **Docker container**
- **Support for more email providers** (Fastmail, ProtonMail bridge)

---

## Built By

Flagged was built by **Stack** — a creative entrepreneur building at the intersection of AI, crypto, and media.

- 🌐 [Stackit.ai](https://flagged.email) — BTC/ETH treasury management for AI-native businesses
- 🐦 Follow the build in public: [@MSanchezWorld](https://twitter.com/MSanchezWorld)
- 📺 Live coding & AI experiments on YouTube

---

## License

MIT — use it, fork it, build on it. See [LICENSE](LICENSE).
