# Flagged + OpenClaw

Flagged is currently a standalone important-email highlighter that can run on the same machine as OpenClaw.

## What Works Now

- Gmail is read through the Gmail API with read-only OAuth scopes.
- Email metadata and snippets are classified through the configured model provider: local open-source models by default, or a frontier model endpoint if the user chooses that tradeoff.
- V1 Telegram alerts can be delivered to the same chat or channel OpenClaw monitors.
- OpenClaw can then help with follow-up tasks when the user asks, such as pulling a link from an email, summarizing the thread, drafting a reply, or adding a follow-up reminder.

In this mode, Flagged is the watcher and classifier. OpenClaw is the operator the user can call on after an alert.

## Current Install Shape

Users install Flagged as a normal local Python service:

\`\`\`bash
git clone https://github.com/Massideation/flagged
cd flagged
pip install -r requirements.txt
python setup_wizard.py
\`\`\`

The setup wizard configures Gmail, alerts, the model provider, and the background service.

## OpenClaw Plugin Roadmap

The next step is to make Flagged installable as a first-class OpenClaw companion:

- Add an OpenClaw plugin manifest.
- Provide a setup command that reuses OpenClaw's local configuration where possible.
- Let alerts route through OpenClaw's message delivery layer instead of requiring a separate Telegram bot token.
- Add Slack, Discord, webhook, and other delivery targets without changing the core classifier.
- Add OpenClaw actions for approved follow-ups: summarize thread, pull links, draft response, create reminder, and classify feedback.
- Keep Gmail read-only by default. Sending email should remain an explicit supervised feature, not part of the default install.

## Product Boundary

Flagged should not become a generic email client. Its job is important-email highlighting:

- Immediate alerts: real people, customers, friends, school/family logistics, warm opportunities, direct asks.
- Digest: bills, admin, affiliate payouts, newsletters, and events.
- Muted: sales pitches, promos, receipts, and low-value automated noise.

OpenClaw should handle what happens after the alert, only when the user asks or has explicitly approved a workflow.
