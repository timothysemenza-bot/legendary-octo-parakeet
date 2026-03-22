# JWBLNG Scope Execution Status
Date: 2026-03-17

## Source of Truth
- `projects/active/client/jwblng-mvp/JWBLNG-Donated-Scope-One-Pager.md`
- `projects/active/client/jwblng-mvp/SCOPE_DECISION_LOCK.md`
- `projects/active/client/jwblng-mvp/notes/meeting-notes-2026-03-17-jessica-follow-up.md`
- `projects/active/client/jwblng-mvp/transcripts/jwblng-meeting-2026-03-16-transcript-extract.md`
- `projects/active/client/jwblng-mvp/backlog/tasks.yaml`
- Live Wix site copy review completed on 2026-03-17 for mission, membership-benefit, and contact-language migration.

## Scope Objective
Close the constrained Phase 1 MVP with:
- one clear public member journey,
- a usable public Kajabi website footprint,
- repeatable communication and approval operations,
- launch and handoff materials that match the live site.

## Phase 1 Live State
- Public navigation is simplified to `About Us`, `Events`, and `Donate`, with Kajabi `Log In` retained.
- The homepage join form remains the canonical Phase 1 join target at `/#block-1772192187104_0`.
- `/join` is live as a compatibility bridge only and routes visitors back to the homepage join form.
- Homepage, About, and Contact copy were refreshed on 2026-03-17 using the March 16 transcript, March 17 notes, and selected Wix language.
- Public event discovery is live at `/events` with supporting program pages for Speaker Series, Book Club, and Halacha Circle.
- Support and donation traffic route through `/support-jwblng`, with Zeffy as the live online path plus visible charity/contact details and a contact-led check-giving fallback.
- A homepage-form smoke submission was completed on 2026-03-17 using `JWBLNG Smoke Test 2026-03-17` / `jwblng-smoke-20260317@example.com`.
- Jessica's March 17 source material is preserved in:
  - `projects/active/client/jwblng-mvp/notes/meeting-notes-2026-03-17-jessica-follow-up.md`
  - `projects/active/client/jwblng-mvp/transcripts/jwblng-meeting-2026-03-16-transcript-extract.md`
  - `projects/active/client/jwblng-mvp/source-material/2026-03-17/JWBLNG Website Meeting_Transcript.docx`

## Status by Backlog Item
### Complete or Functionally Complete
- `OPS-002` Baseline current-state audit
  - Playwright audit/verify scaffolding and artifact locations are established.
- `OPS-003` Lock canonical member journey
  - The Phase 1 path is now consistent: discover -> homepage form -> approval review -> free community access -> event participation -> ongoing email updates.
- `OPS-004` Rework navigation and homepage CTA structure
  - Public nav and homepage CTA structure are aligned to the approved Phase 1 path.
- `OPS-005` Build canonical join page and onboarding entry
  - Canonical join target is the homepage form.
  - `/join` remains the compatibility bridge for secondary pages where Kajabi strips homepage hash fragments.
- `OPS-006` Standardize event publishing template
  - Events hub and program-page surfaces are live and routed into the approved join path.
- `OPS-008` Configure donation CTA path with Zeffy
  - Donation routing is live on the support page and aligned to the approved external-link decision.
  - The public donation page now explains impact, keeps Zeffy primary, and surfaces contact-led check-giving guidance without inventing a mailing address.

### In Progress During Closeout
- `OPS-001` Validate platform access and MFA operating window
  - Core Kajabi execution is working.
  - Remaining closeout dependency is documenting any external-owner items still needed for sender/domain setup.
- `OPS-007` Implement communication starter pack
  - Copy, audience rules, and send calendar are now documented in `projects/active/client/jwblng-mvp/COMMUNICATION_STARTER_PACK.md`.
  - Existing Kajabi communication assets confirmed on 2026-03-17:
    - `JWBLNG Welcome Sequence`
    - `JWBLNG Upcoming Events` (draft)
    - `JWBLNG Monthly Digest` (draft)
  - One seed test was completed for `JWBLNG Monthly Digest`.
  - Welcome and event-reminder seed-test capture remain the final operator step.
- `OPS-009` Execute QA automation and manual UAT
  - Manual public verification is logged in `projects/active/client/jwblng-mvp/QA_LOG.md`.
  - Final artifact reruns should be captured immediately before handoff/go-live sign-off.
- `OPS-010` Launch readiness and cutover checklist
  - Checklist set is updated to the current live state.
  - Final approver names, timing, and go/no-go record are still open.
- `OPS-011` Admin SOP handoff and sign-off
  - SOP and runbook are updated.
  - The supervised walkthrough with Jessica and Marcy still needs to be completed and recorded.

## Deferred or Asset-Blocked Items
- Board bios and headshots
- Testimonials and rabbinic endorsements
- Final mailing address for check donations if JWBLNG wants static by-mail instructions published
- Podcast/resources/public archive expansion
- Visual/image-guidance refinements requiring new approved assets

Tracked in:
- `projects/active/client/jwblng-mvp/PHASE1_CLIENT_INPUT_GAPS.md`

## Closeout Artifacts
- Launch checklist: `projects/active/client/jwblng-mvp/LAUNCH_CHECKLIST.md`
- Rollback checklist: `projects/active/client/jwblng-mvp/ROLLBACK_CHECKLIST.md`
- QA log: `projects/active/client/jwblng-mvp/QA_LOG.md`
- Communication starter pack: `projects/active/client/jwblng-mvp/COMMUNICATION_STARTER_PACK.md`
- Handoff notes: `projects/active/client/jwblng-mvp/HANDOFF_NOTES.md`
- Admin SOP: `projects/active/client/jwblng-mvp/JWBLNG-Admin-SOP-One-Page.md`
- Runbook: `projects/active/client/jwblng-mvp/RUNBOOK.md`

## Remaining Dependencies Before Formal Closeout
No additional net-new public-site build is required to close the donated Phase 1 scope once the items below are completed.

1. Run seed tests for `JWBLNG Welcome Sequence` and `JWBLNG Upcoming Events`, then capture proof alongside the completed monthly-digest test.
2. Confirm whether sender/domain setup requires an external owner and record the owner plus ETA.
3. Hold the supervised handoff session with Jessica and Marcy and record sign-off.

## Paid Follow-On Direction
- Phase 1 transcript requests that exceed donated scope are compared in `projects/active/client/jwblng-mvp/PHASE1_SCOPE_VS_TRANSCRIPT.md`.
- A draft paid follow-on proposal is prepared in:
  - `projects/active/client/jwblng-mvp/JWBLNG-NEXT-PHASES-PROPOSAL.md`
  - `projects/active/client/jwblng-mvp/next-phases-proposal.html`

## Canonical Join Configuration
- Canonical join target: `/#block-1772192187104_0`
- Secondary-page compatibility bridge: `/join`
