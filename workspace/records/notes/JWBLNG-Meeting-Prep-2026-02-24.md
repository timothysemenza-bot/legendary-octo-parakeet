# JWBLNG Meeting Prep (2026-02-24)

## What We Know (from intake + SOW)

- Core blocker is not content creation; it is an unclear member journey and inconsistent communication operations.
- Main friction points:
  - No single trusted join link/path to share at networking events.
  - Ambiguity between Kajabi tools (products/events/campaigns/newsletters).
  - Mixed website architecture (Wix + Kajabi) causing confusion and duplicated effort.
  - Prior consultant trust gap around scope transparency and billable outcomes.
- Strategic context:
  - Membership fees were removed; organization is shifting to fundraising.
  - Team capacity is limited; repeatable low-overhead operations matter more than advanced features.

## Jessica's Original Ask (Anchor Requirements)

- Platform context:
  - Main site is on Wix.
  - >$10k already invested in Kajabi.
  - Model shifted from paid membership to free membership.
- Active Kajabi use cases:
  - Meetups/events and speaker series
  - Monthly book club
  - Classes/programming
  - Recording/storage for member content
- Three explicit decision questions:
  1. Should Wix move to Kajabi (including donations + membership access)?
  2. What should the new free-member onboarding experience be?
  3. Which Kajabi marketing tools should be used for newsletters/updates/reminders?

## Initial Positioning for Today

Use this framing in the call:

"We should treat this as a funnel and operations design problem first, and a platform decision second."

This keeps the discussion outcome-focused and avoids a platform argument early.

## Two Practical MVP Paths

### Path A: Kajabi-First MVP (recommended for fastest wins)

- Keep current stack for now.
- Build one canonical "Join JWBLNG" entry point.
- Standardize onboarding automation and event/newsletter cadence.
- Hide/remove legacy paid-tier artifacts and confusing old offers.
- Add simple KPI tracking around join flow and event participation.

Why now:
- Fastest path to operational clarity.
- Minimal migration risk.
- Protects sunk costs while proving demand and process.

### Path B: Custom Stack MVP (parallel discovery, not immediate migration)

- Build a lightweight custom front-end + CRM/email backend in phases.
- Start with intake form, member directory permissions, event calendar, and automated email workflows.
- Keep Kajabi operational while custom system proves parity.

Why later:
- Greater long-term control.
- Better fit if Kajabi constraints block strategy.
- Higher initial build/maintenance burden for a small team.

## Decision Rule (to align Jessica + Marcy)

Recommend this explicit rule in the meeting:

- Run Path A for 30-45 days.
- If Kajabi cannot support 3 critical outcomes (clean join flow, reliable comms cadence, and low admin overhead), approve migration planning to Path B.

This makes "custom vs SaaS" a measured decision with evidence, not opinion.

## Concrete 30-Day MVP Backlog

1. Journey Mapping (Day 1-3)
- Define single prospect path from outreach -> join -> onboarding -> first event.
- Define owner for each step (Jessica/Marcy/ops).

2. Kajabi IA Cleanup (Week 1)
- Consolidate/rename products/offers/events.
- Archive or hide legacy paid-membership artifacts.
- Publish one canonical join destination.

3. Automation Baseline (Week 1-2)
- Welcome email sequence (D0, D2, D7).
- Event reminder sequence (T-7d, T-24h, T-2h).
- Monthly newsletter template + send checklist.

4. Messaging & Assets (Week 2)
- Create 3 reusable outreach templates:
  - "Met you at event" follow-up
  - "Join JWBLNG" invite
  - Monthly programming digest

5. Metrics (Week 3-4)
- Track:
  - Join link clicks
  - Join completions
  - First-event attendance
  - Newsletter open/click rates
- Weekly 20-minute review and iteration.

## Questions to Drive the Meeting

1. What is the single action we want every new prospect to take within 5 minutes?
2. Which 3 member experiences must feel "professional and effortless" by end of March 2026?
3. Which current Kajabi features are mandatory vs optional?
4. What reporting does Marcy need weekly to feel confidence in progress?
5. What budget/time threshold would justify a custom build decision?

## Direct Answers to Jessica's 3 Questions (for live call)

1. Should Wix move to Kajabi now?
- Recommendation: not yet.
- Reason: first prove one clean member funnel and comms operations in Kajabi before full-site migration.
- Next step: keep Wix as public marketing shell, link to one canonical Kajabi join path.

2. What should membership look like now that it is free?
- Recommendation: one-click path: outreach link -> simple signup -> instant welcome sequence -> event/calendar onboarding.
- Next step: implement and test with 3 external users before broad promotion.

3. How should marketing run inside Kajabi?
- Recommendation: separate by purpose:
  - Campaigns: nurture and onboarding sequences
  - Event emails: event-specific reminders/updates
  - Newsletter: monthly digest and programming highlights
- Next step: define a 30-day cadence and a send checklist owned by one person.

## Live Call Recording + Real-Time MVP Iteration

### Goal

Capture the call, transcribe quickly, convert into action items and updated MVP scope the same day.

### Practical Workflow (today)

1. Record the call in Microsoft Teams/Zoom with consent at start.
2. Save recording file to local `recordings/`.
3. Transcribe locally using the existing repo workflow (`marketing-agents/scripts/install-transcription-engine.ps1` if needed).
4. Use transcript to generate:
   - Scope deltas
   - Accepted decisions
   - New risks/open questions
   - Updated 2-week implementation backlog

### Suggested opening consent line

"I want to record this so I can accurately capture your requirements and turn this into a concrete execution backlog right after the call. Is that okay with both of you?"

### Real-time collaboration setup

- Keep one shared running note during the call with 4 headings:
  - Decisions
  - Open Questions
  - Risks
  - Action Items + Owner + Due Date
- At end of call, read back decisions live for confirmation.

## Website Status Note for Call

As of 2026-02-24, `jwblng.org` is reachable from this machine:

- HTTPS: HTTP 200
- DNS resolves to: `15.197.148.33`, `3.33.130.190`
- TCP/443 connectivity: successful

If Jessica/Marcy still see downtime, likely causes are local caching, DNS propagation/caching, or a path-level issue rather than total domain outage.

## Recommended Ask at End of Meeting

Request explicit approval for:

- 2-week Kajabi-first sprint.
- Weekly 20-minute decision checkpoint with Marcy.
- A go/no-go migration checkpoint after measurable results.
