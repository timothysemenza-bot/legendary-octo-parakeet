# JWBLNG Phase 1 Launch Checklist
Date: 2026-03-17
Scope basis:
- `projects/active/client/jwblng-mvp/JWBLNG-Donated-Scope-One-Pager.md`
- `projects/active/client/jwblng-mvp/SCOPE_DECISION_LOCK.md`
- `projects/active/client/jwblng-mvp/SCOPE_EXECUTION_STATUS.md`
- `projects/active/client/jwblng-mvp/QA_LOG.md`

## A) Phase 1 Live-State Freeze
- [x] Decision lock reflects the approved Phase 1 journey.
- [x] Canonical join target is the homepage form `/#block-1772192187104_0`.
- [x] `/join` is live as a compatibility bridge only.
- [x] Homepage, About, Contact, Events, Speaker Series, Book Club, Halacha Circle, and Support pages are publicly reachable.
- [x] Donation path is Zeffy-based and presented from `/support-jwblng`.
- [x] March 16 transcript extract and March 17 notes are stored in-repo.

## B) Technical Validation
- [x] Run fresh read-only audit:
  - `npm run pw:jwblng:audit`
- [x] Run fresh public-journey verify:
  - `npm run pw:jwblng:verify`
- [x] Run fresh homepage QA:
  - `npm run pw:jwblng:homeqa`
- [x] Run fresh event-page QA:
  - `npm run pw:jwblng:eventqa`
- [x] Confirm latest artifacts exist in `projects/active/client/jwblng-mvp/playwright/artifacts`.
- [x] Confirm homepage form still uses `name`, `email`, `interest`.
- [x] Confirm homepage smoke submission reaches the Kajabi thank-you state.

## C) Content and Communication Validation
- [x] Homepage explanatory copy reflects the March 16 transcript direction.
- [x] About page reflects migrated mission/member-benefit language from Wix.
- [x] Contact page includes current email, phone, and charity number.
- [x] Welcome/approval communication asset exists in Kajabi (`JWBLNG Welcome Sequence` / `JWBLNG Free Membership Email`).
- [x] Event reminder draft exists in Kajabi (`JWBLNG Upcoming Events`).
- [x] Monthly digest draft exists in Kajabi (`JWBLNG Monthly Digest`).
- [ ] One internal seed test has been sent for each draft.
- [x] Monthly digest seed test was sent to `timmy@bosskeyops.com` on 2026-03-17.
- [x] Communication operating rules are documented in `projects/active/client/jwblng-mvp/COMMUNICATION_STARTER_PACK.md`.

## D) Ops and Handoff Validation
- [x] Approval workflow guardrails are documented:
  - `pending-review`
  - `approved-member`
  - `needs-follow-up`
  - `declined`
- [x] Free community-access-only rule is documented.
- [x] Launch and rollback checklists reflect the current Phase 1 architecture.
- [ ] Jessica and Marcy have completed one supervised contact-approval walkthrough.
- [ ] Jessica and Marcy have completed one supervised event-update walkthrough.
- [ ] Jessica and Marcy have completed one supervised email-draft walkthrough.

## E) External Dependencies
- [ ] Sender/domain setup status is confirmed and documented.
- [ ] Any MFA or external-owner dependencies are assigned by name.
- [ ] Deferred client-input items are acknowledged from `projects/active/client/jwblng-mvp/PHASE1_CLIENT_INPUT_GAPS.md`.

## F) Go/No-Go Record
- [ ] Final QA pass reviewed.
- [ ] Open issues classified as Phase 1 hotfix or later-phase backlog.
- [ ] Go decision recorded.

Go/no-go notes:
- Date/time:
- Approver(s):
- Decision:
- Notes:
