# Flagged — Product Roadmap
## From Email Monitor to Autonomous Email Agent

**Domain:** flagged.email  
**Repo:** github.com/MSanchezWorld/flagged  
**Core principle:** Test first, earn trust, then automate. Never give an agent permissions you haven't watched it earn.

---

## The Philosophy

Every action the agent takes autonomously is one you've already approved manually dozens of times. The roadmap is about moving things from "you decide" to "agent decides" only after the pattern is proven reliable.

```
v1  Watch and tell you
v2  Propose and you approve with one tap
v3  Act automatically on patterns you've pre-approved
```

---

## Stage 1 — Monitor (Now)
**Tagline:** *Your inbox, filtered by what actually matters.*

### What it does
- Watches all Gmail accounts every 5 minutes
- Scores every unread email 1–10 using local LLM (no data leaves your machine)
- Fires Telegram alert for anything above your threshold
- Alert includes: sender, subject, score, reason, 400-char preview

### What you do after the alert
Everything. You open Gmail and respond manually.

### Goal of this stage
Run it for 2–4 weeks. Watch whether the scores make sense. Edit PRIORITIES.md to tune it. Build trust in the model's judgment before giving it any actions.

### Success metric
You catch things you would have missed. Scores feel right 80%+ of the time.

---

## Stage 2 — Supervised Actions (v2)
**Tagline:** *One tap to act. You stay in control.*

### How it works
Agent proposes an action alongside every high-score alert. You approve with a single Telegram button tap. Nothing happens without your explicit OK.

### Telegram alert format
```
🔴 URGENT — Main Inbox

🎟 INVITE
From: events@arbitrum.foundation
Subject: You're invited to Arbitrum Dev Day
Score: 9/10 — Direct invite, RSVP deadline, known sender

📎 Suggested action:
"Send calendar link + express interest"

──────────────────────────────
[✅ Send]  [✏️ Edit First]  [❌ Skip]
```

### Action types to build (in order of priority)

**1. Send calendar link**
Triggered by: meeting requests, event invites, "would love to connect" emails
Action: Sends your cal.com or Calendly link with a short personalized opener
Template: *"Hey [name], happy to connect — here's my calendar: [link]"*

**2. Add to calendar**
Triggered by: event invites with a parseable date/time/location
Action: Creates Google Calendar event, sends Telegram confirmation
You tap confirm. Done.

**3. Standard inquiry response**
Triggered by: recognized email patterns (Stackit.ai questions, media kit requests, partnership intros)
Action: Pulls matching response template, personalizes the opener
Templates you write once, agent uses forever

**4. Express interest + request details**
Triggered by: speaking opportunities, podcast invites, collaboration proposals
Action: Sends a short reply expressing interest and asking for more details
Template: *"Thanks for reaching out — this sounds interesting. Can you share more details on [X]?"*

**5. Decline politely**
Triggered by: requests that don't match your criteria but came from a real person
Action: Sends a short, warm decline
Template: *"Thanks for thinking of me — not the right fit right now, but appreciate the outreach."*

### Response template library
Start building this now during Stage 1. Every time you respond to an email, ask: *"Would I say the same thing to the next 10 people who send this?"* If yes, write it down. By the time v2 is ready, you'll have a full library.

Template categories to build:
- Meeting / calendar request response
- Event invite acceptance
- Event invite decline  
- Stackit.ai partnership inquiry
- Media / press inquiry
- Speaking / podcast request
- General "not right now" decline
- Intro acknowledgment
- Follow-up request

---

## Stage 3 — Autonomous Agent (v3)
**Tagline:** *Set the rules once. Let it work.*

### How it works
For categories you've already approved many times in Stage 2, the agent acts without asking. You define which patterns are fully autonomous. Everything else still asks first.

### Example autonomy rules (you configure these)
```
IF category = "meeting_request"
AND score >= 8
AND sender is in contacts
THEN send calendar link automatically

IF category = "event_invite"  
AND score >= 9
AND location = "virtual" OR city = "your city"
THEN add to calendar + send RSVP automatically

IF category = "standard_inquiry"
AND matched_template exists
AND score < 7
THEN send template response automatically
```

### What stays supervised forever
- Any email from a new sender you've never interacted with
- Anything involving money, contracts, or legal language
- Press and media — always want eyes on these
- Emails where the agent confidence is below a threshold
- Anything you manually flag as "always ask me first"

### Context enrichment (runs before every alert)
Before alerting you on a high-score email, the agent:
- Searches the sender's name + company
- Checks if they've mentioned Flagged, Stackit.ai, or your name publicly
- Pulls their Twitter/LinkedIn summary
- Includes a 2-line brief in the Telegram alert

Result: You know who someone is before you decide whether to respond.

### Thread catch-up
For email threads that got buried and are now flagged late:
- Agent summarizes the entire thread in 3 bullet points
- Includes what the last ask was
- Proposes a response based on thread context

### Follow-up loop
You reply "follow up in 3 days" to a Telegram alert.
Agent re-surfaces the email automatically if no reply has come in within that window.
Closes the loop without you tracking it manually.

---

## Monetization Path

| Tier | What it includes | Price |
|---|---|---|
| **Open Source** | Stage 1 monitor, self-hosted | Free |
| **Flagged Pro** | Hosted monitor, no Mac Mini needed | ~$12/mo |
| **Flagged Agent** | Stage 2 supervised actions, template library | ~$29/mo |
| **Flagged Autonomous** | Stage 3 full agent, context enrichment | ~$59/mo |

The free tier does the marketing. Pro converts the non-technical audience. Agent tiers are where recurring revenue compounds.

---

## Tech Stack for Agent Features

Everything you need is already in the current codebase:

| Feature | What to add |
|---|---|
| Telegram button taps | Telegram Bot callback_query API |
| Send email responses | Gmail API (add send scope) |
| Add to calendar | Google Calendar API |
| Context enrichment | Web search tool in LM Studio |
| Template matching | Simple JSON template library |
| Follow-up tracking | Add follow_ups.json alongside seen_emails.json |

GLM-4.7 already supports tool-use / function calling — the model can handle all of this without upgrading.

---

## Launch Sequence

1. ✅ **Now** — Push v1 to github.com/MSanchezWorld/flagged
2. **Week 1-2** — Run it yourself, tune PRIORITIES.md, collect response templates
3. **Week 3-4** — Post launch on Twitter/X, r/LocalLLaMA, ProductHunt
4. **Month 2** — Build Stage 2 supervised actions (calendar link + template responses first)
5. **Month 3** — Launch flagged.email Pro (hosted version, waitlist → paid)
6. **Month 4-6** — Stage 3 autonomous rules engine, context enrichment

---

## The North Star

Someone misses a $50K partnership opportunity because it got buried in their inbox. That person finds Flagged, sets it up in 10 minutes, and never misses one again. That's the product. Everything in this roadmap is in service of that outcome.
