# Boss Key Review-First Growth OS

This layer turns the Boss Key marketing workspace into one review-first operating loop across:

- website publishing to `bosskeyops.com/insights/`
- RSS generation at `bosskeyops.com/insights/feed.xml`
- LinkedIn relationship maintenance
- meeting recommendations
- Competitive Price to Win analysis
- pre-consult proposal drafting

Nothing is auto-sent through LinkedIn in v1. The only automatic external behavior is still the approved website-to-RSS-to-LinkedIn Company Page share after deploy.

## Operating model

The flow now runs in this order:

1. source notes and research are synced into the content queue
2. relationship rows are evaluated for PTW eligibility
3. qualified relationships get an active PTW record and PTW brief
4. the PTW record shapes meeting drafts, LinkedIn tone, and proposal pricing
5. all drafts land in one review packet and one decision file
6. approvals unlock publishing, send-ready messages, meeting packets, and send-ready proposals

## PTW model

The pricing layer now follows an APMP-style competitive PTW structure instead of a pure internal modifier model.

- `market-assessment`
  - early top-down view
  - generates `price_to_compete_usd`
  - used when budget, buyer, and competitor data are still incomplete
- `opportunity-analysis`
  - later bottom-up refinement
  - generates `price_to_win_usd`
  - used when buyer priorities, evaluation logic, and likely competitor posture are clearer

Starter-first shaping is the default. If a narrower entry offer is more winnable than the original offer hypothesis, the OS recommends the narrower entry offer and keeps the larger offer as the expansion path.

## Core files

- Content sources: `marketing-agents/data/boss_key_content_sources.csv`
- Content queue: `marketing-agents/data/boss_key_content_queue.csv`
- Relationship queue: `marketing-agents/data/boss_key_relationship_queue.csv`
- Conversation memory: `marketing-agents/data/boss_key_conversation_memory.csv`
- Meeting queue: `marketing-agents/data/boss_key_meeting_queue.csv`
- PTW queue: `marketing-agents/data/boss_key_ptw_queue.csv`
- Pre-consult proposals: `marketing-agents/data/boss_key_preconsult_proposals.csv`
- Competitive knowledge base: `marketing-agents/data/boss_key_competitive_kb.csv`
- PTW outcomes / calibration log: `marketing-agents/data/boss_key_ptw_outcomes.csv`
- Private price book: `marketing-agents/data/boss_key_private_price_book.csv`
- Price modifiers: `marketing-agents/data/boss_key_price_modifiers.csv`

## Source of Truth

Boss Key relationship state and competitive evidence now live primarily in `proposal-ops`, not in the CSV queue files.

- ProposalOps CRM backbone:
  - `proposal-ops` contractors hold the account record
  - `proposal-ops` contacts and touchpoints hold the live conversation history
  - `proposal-ops` opportunities and commercials hold the advisory pursuit and value framing
  - `proposal-ops` growth relationship profiles and growth market evidence hold the Boss Key-specific queue fields that were previously drifting in CSVs
- Queue projection files:
  - `marketing-agents/data/boss_key_relationship_queue.csv`
  - `marketing-agents/data/boss_key_conversation_memory.csv`
  - `marketing-agents/data/boss_key_competitive_kb.csv`
  These files are now hydrated from `proposal-ops` before a build and persisted back after build/apply so the review workflow still works without maintaining a second CRM.
- Pricing model notes: `marketing-agents/BOSS-KEY-PRICING-MODEL.md`
- Unified decisions: `marketing-agents/data/boss_key_review_decisions.csv`
- Review packet: `marketing-agents/briefs/boss-key-review-packet-latest.md`

## Scripts

- Sync source inputs into the content queue:
  - `powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\sync-boss-key-content-queue.ps1`
- Build the review packet plus all pending drafts:
  - `powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\build-boss-key-growth-review.ps1`
- Apply approvals and refresh the public insights site/feed:
  - `powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\apply-boss-key-growth-review.ps1`
- Run the default full loop:
  - `powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\run-boss-key-growth-os.ps1`

## Review items and approval behavior

- `content`
  - `approve`: publish to the Insights hub and include in RSS
  - `revise`: hold for revision
  - `hold`: keep out of public outputs
  - `reject`: remove from publish path
- `linkedin-touch`
  - `approve`: mark `ready-to-send`
  - no auto-send
- `ptw-analysis`
  - `approve`: marks the active PTW analysis approved
  - does not send anything by itself
  - unlocks meeting/proposal readiness checks
- `meeting`
  - `approve`: generates the invite packet and can mark the booking message `ready-to-send`
  - a `no-bid` PTW posture blocks the meeting
  - no auto-booking
- `proposal`
  - `approve`: can mark the proposal packet `ready-to-send`
  - proposal readiness is still blocked by `needs-ptw-input`, `market-assessment-only`, `owner-escalation-required`, or `no-bid`
  - no auto-send

## PTW statuses

- `needs-ptw-input`
  - there is not enough structured evidence yet for a credible PTW view
- `market-assessment-only`
  - there is enough evidence for `price_to_compete`, but not enough for a credible `price_to_win`
- `pending-ptw-review`
  - a usable PTW draft exists and is waiting on owner review
- `approved`
  - PTW is approved and can unlock downstream readiness
- `owner-escalation-required`
  - likely winning price falls below the configured offer floor
- `no-bid`
  - the current market position is not attractive enough to pursue under the current offer shape

## Knowledge-base behavior

The competitive knowledge base stores reusable customer, buyer, budget, and competitor context. Generated PTW model rows are written back into the knowledge base for continuity, but they are not treated as primary evidence on the next run. That keeps the system from inflating confidence by recycling its own prior outputs as market proof.

## Calibration

Closed opportunity outcomes can be logged in `boss_key_ptw_outcomes.csv`. Those rows are synced into the competitive knowledge base so the PTW layer can compare:

- prior `price_to_compete`
- prior `price_to_win`
- actual quoted or awarded price
- known winner or substitute path

This is intentionally lightweight in v1. The goal is to improve future pricing judgment without building a full reporting stack.
