# JWBLNG Communication Starter Pack
Date: 2026-03-17

Purpose: Give Jessica and Marcy a Phase 1-safe set of Kajabi email drafts, send rules, and a simple monthly cadence.

## Current Kajabi Asset Inventory
- Welcome / approval:
  - `JWBLNG Welcome Sequence`
  - supporting prior send: `JWBLNG Free Membership Email`
- Event reminder draft:
  - `JWBLNG Upcoming Events`
- Monthly digest draft:
  - `JWBLNG Monthly Digest`

Status note:
- The asset inventory exists in Kajabi as of 2026-03-17.
- `JWBLNG Monthly Digest` was refreshed on 2026-03-17 with an updated internal title, subject, preview text, and opening copy.
- A monthly-digest seed test was sent to `timmy@bosskeyops.com` on 2026-03-17.
- The lower body sections of `JWBLNG Monthly Digest` still need a final content cleanup before client-facing use.
- Seed-test proof still needs to be captured for the welcome and event-reminder assets before formal sign-off.

## Draft Set
### 1) Welcome / Approval
- Audience: approved contacts only
- Goal: confirm approval, set expectations, point members to the next useful action
- Suggested subject: `Welcome to JWBLNG`
- Preview text: `You are in. Here is how to get connected and what to do next.`
- Primary CTA: `View Upcoming Events` -> `/events`
- Secondary CTA: `Support JWBLNG` -> `/support-jwblng`

Suggested body:
```text
Hi {{ first_name | default: "there" }},

Welcome to JWBLNG. We are so glad you are here.

JWBLNG is a professional home for Orthodox Jewish women in business. In Phase 1, your community access includes event updates, speaker series announcements, book club invitations, and opportunities to connect with other women growing with integrity.

Start here:
- See the latest public events
- Watch for upcoming member communications
- Reply if there is a program or topic you especially want to see

We are excited to welcome you.

Warmly,
JWBLNG
```

### 2) Event Reminder
- Audience: approved members or invited registrants
- Goal: remind members about one specific upcoming program
- Suggested subject: `Reminder: {{ event_title }}`
- Preview text: `Details and next steps for the upcoming JWBLNG event.`
- Primary CTA: event-specific URL or RSVP path
- Secondary CTA: `/events`

Suggested body:
```text
Hi {{ first_name | default: "there" }},

This is a reminder about {{ event_title }}.

We are looking forward to gathering for another JWBLNG program focused on practical learning, thoughtful conversation, and community.

Please review the event details and RSVP information here:
{{ event_link }}

If you have any questions, reply to this email and we will help.

Warmly,
JWBLNG
```

### 3) Monthly Digest
- Audience: approved members and community-access recipients
- Goal: keep members warm between events and reinforce the value of staying engaged
- Suggested subject: `What's New at JWBLNG This Month`
- Preview text: `Upcoming events, highlights, and ways to stay connected.`
- Primary CTA: `/events`
- Secondary CTA: `/support-jwblng`

Suggested body:
```text
Hi {{ first_name | default: "there" }},

Here is what is new at JWBLNG this month.

- Upcoming events and conversations
- Community highlights
- New opportunities to learn, connect, and grow

See the latest events:
{{ events_link | default: "https://www.jwblng.org/events" }}

Thank you for being part of this community.

Warmly,
JWBLNG
```

## Send Rules
- Keep one primary objective per email.
- Keep public emails on public links unless the audience is explicitly approved.
- Do not include member-only WhatsApp links on public or broad-segment sends.
- Seed-test every email internally before scheduling.
- If sender/domain setup is incomplete, use draft-only mode and record the blocker in `HANDOFF_NOTES.md`.

## Monthly Send Calendar
- Week 1: Monthly digest
- Week 2: Event reminder if a live event is upcoming
- Week 3: Optional follow-up or highlight email only if there is a clear program objective
- Week 4: No filler send; skip if there is nothing useful to communicate

## Operator Checklist
- Pick the correct audience
- Confirm subject line and preview text
- Verify the primary CTA
- Verify the sender identity
- Send internal seed test
- Review mobile rendering
- Schedule or send
- Log any issue or dependency

## Phase 1 Links
- Homepage: `https://www.jwblng.org/`
- Events: `https://www.jwblng.org/events`
- Support: `https://www.jwblng.org/support-jwblng`
- Compatibility join bridge: `https://www.jwblng.org/join`
