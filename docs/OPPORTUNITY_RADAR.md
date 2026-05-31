# Important Email Highlighter

Flagged's core product promise:

> Highlight the important emails I would otherwise miss, without making me pay for a premium email client or sort through newsletters, bills, receipts, and sales pitches.

Flagged is not trying to become a full email client. It is a model-flexible important-email highlighter that works with the inbox you already use.

The model layer should stay flexible: local open-source models for private, cheap classification by default; frontier models when a user chooses higher accuracy and accepts sending the minimal email metadata/snippet to that provider.

## What Should Alert Immediately

Immediate alerts should be reserved for email that looks like:

- A real person reaching out directly.
- A customer or user asking a question.
- A friend, warm contact, founder, partner, or known person opening a door.
- A paid-work, client, partnership, media, podcast, speaking, investor, or collaboration opportunity.
- A school/family email that is specific to the user's child, schedule, event, form, deadline, or action required.
- A time-sensitive opportunity where missing it would matter.

The alert should explain why it matters and what kind of choice it creates. It should also include a short plain-English gist so the user can quickly tell whether it is a real opportunity without opening Gmail.

## What Should Not Alert Immediately

These should be muted or moved to digest:

- Uber, travel, food, retail, and app receipts.
- Bills, invoices, refunds, bank notices, and account admin.
- Affiliate payouts or earnings updates unless unusually large or action-required.
- Newsletters, webinar invites, event blasts, launch announcements, and generic promos.
- Cold sales pitches, lead-gen offers, agency pitches, course offers, SaaS demos, and vendor outreach.
- Automated platform notifications.

## Required Code Changes

### 1. Fetch Better Metadata

The current Gmail fetch should include more signals than sender, subject, date, and snippet:

- List-Unsubscribe
- List-Id
- Auto-Submitted
- Precedence
- Reply-To
- Message-ID
- Gmail labels and categories where available
- thread id
- internal date

These let Flagged identify newsletters, automated mail, receipts, and list blasts before asking the LLM.

### 2. Add A Deterministic Noise Gate

Before the LLM runs, Flagged should cheaply classify obvious noise:

- newsletter/list mail
- receipts and bills
- affiliate/admin notifications
- automated platform messages
- cold sales/vendor pitches

If the gate is confident, route the message to digest or mute without spending model time.

### 3. Keep The LLM For Ambiguous Opportunity Judgment

The LLM should focus on the hard question:

> Is this an important email from a real person or important institution that the user should see now?

It should return:

- score
- category
- sender type
- relationship
- ask type
- alert channel
- alert mode
- confidence
- reason
- why flagged
- why it is not just newsletter/admin/sales noise

### 4. Make Feedback Change Future Results

Telegram buttons should not just record feedback. They should update a local learning file:

- positive_examples: emails that were good alerts
- negative_examples: emails that should be muted
- digest_examples: useful but not immediate
- sender_rules: always alert / always digest / always mute

That file should be injected into the classifier prompt on every run. After a button tap, the Telegram bot should ask for an optional short reason so the user can teach the system why the alert was good, bad, or digest-only.

### Alert Scope Management

Users need a visible control surface for what gets alerted. The first version is a terminal command:

    python flagged.py scope show
    python flagged.py scope set opportunities --mode immediate --min-score 7
    python flagged.py scope set money_admin --mode digest
    python flagged.py scope set learning_events --mode mute

This should later become a small web/OpenClaw surface where a user can see and edit:

- immediate alert categories
- digest categories
- muted categories
- examples that taught the system
- sender-specific rules

### 5. Add Digest Delivery

Digest-mode messages should not disappear. They should be batched:

- daily digest by default
- optional command to ask for "what did I miss?" through the active delivery channel
- grouped by Money/Admin, Learning/Events, Sales Pitches, Other

The immediate channel stays clean.

### 6. Add An Evaluation Harness

Flagged needs a small local test set:

- obvious customer email -> immediate
- friend/warm intro -> immediate
- partnership inquiry -> immediate
- Uber receipt -> mute
- bill/invoice -> digest or mute
- affiliate payout -> digest
- newsletter -> digest
- cold vendor pitch -> mute
- event blast -> digest

Every bug Miguel catches should become a fixture.

### 7. OpenClaw Companion Layer

OpenClaw should handle actions after an alert, not replace the classifier:

- pull the link from an email
- summarize the thread
- draft a reply only when asked
- create a reminder/follow-up
- mark feedback from Telegram

Longer term, Flagged should expose a local event file or webhook that OpenClaw can subscribe to.

Telegram is the v1 delivery path, not the product boundary. Slack, Discord, webhooks, and OpenClaw-native delivery should be treated as channel adapters around the same important-email classifier.

## Dogfood Loop

The fastest path is to use Miguel's inbox as the calibration loop:

1. Flagged alerts.
2. Miguel says good / bad / digest.
3. Bad alerts become negative examples.
4. Good alerts become positive examples.
5. Weekly, examples get distilled into default rules.

This creates both the product and the marketing proof.

## Marketing Proof

The public demo should show the contrast:

- Uber receipt: muted.
- Newsletter: digest.
- Cold sales pitch: muted.
- Customer question: immediate alert.
- Warm opportunity: immediate alert.
- User taps "Mute type" and the system improves.
- Every immediate alert explains why it fired and why it was not treated as newsletter/admin/sales noise.

The message:

> Stop paying for a full premium inbox just to highlight the emails you cannot afford to miss.
