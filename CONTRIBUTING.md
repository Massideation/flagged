# Contributing to Flagged

Thanks for wanting to contribute. Flagged is intentionally simple — keep PRs focused.

---

## What We're Looking For

**High-value contributions:**
- Outlook / Microsoft 365 email provider support
- Slack or Discord notification channel support
- systemd service template for Linux
- Docker container with docs
- Web dashboard for scored email history
- ProtonMail Bridge / Fastmail support
- Windows Task Scheduler setup guide
- Webhook support for custom notification targets

**Good first issues:**
- Improve SETUP.md clarity for any platform
- Add a `--dry-run` flag that scores emails without sending alerts
- Add a `--test` flag that sends a test Telegram message
- Better error messages when LM Studio isn't running

---

## How to Contribute

1. **Fork** the repo
2. **Create a branch** — `git checkout -b feature/outlook-support`
3. **Make your changes**
4. **Test it** — make sure it runs without errors
5. **Open a PR** with a clear description of what you changed and why

---

## Code Style

- Python 3.9+ compatible
- Keep it readable — this is a tool people customize and maintain themselves
- No new required dependencies without strong justification
- Secrets never hardcoded — always via `config.json`
- New email providers should follow the same pattern as Gmail (auth → fetch metadata → return list of dicts)

---

## Privacy Principle

Flagged's core promise is local-first. Any contribution that requires sending email body content to a remote API should be opt-in and clearly documented.

---

## Bug Reports

Open an issue with:
- Your OS and Python version
- Your LM Studio model
- The full error message from the log
- What you expected to happen

---

## Questions

Open a Discussion on GitHub or reach out to [@MSanchezWorld](https://twitter.com/MSanchezWorld).
