# JWBLNG Phase 1 Launch Checklist
Date: 2026-02-28
Scope basis:
- `jwblng-mvp/JWBLNG-Donated-Scope-One-Pager.md`
- `jwblng-mvp/SCOPE_DECISION_LOCK.md`
- `jwblng-mvp/SCOPE_EXECUTION_STATUS.md`

## A) Pre-Launch (T-48h to T-24h)
- [ ] Confirm approved decision lock is current.
- [ ] Confirm canonical join CTA copy is live:
  - Primary: `Join JWBLNG`
  - Secondary: `View Events`
  - Post-join: `Register for Your First Event`
- [ ] Confirm Zeffy donation mode is external-link path and link target is correct.
- [ ] Confirm Wix preserve list is finalized (legal/compliance only).
- [ ] Capture current-state screenshots:
  - Homepage
  - Join flow entry
  - Event page
  - Donation CTA surface

## B) Technical Validation (T-24h)
- [ ] Run read-only audit:
  - `powershell -ExecutionPolicy Bypass -File jwblng-mvp/playwright/scripts/run-flow.ps1 -Flow audit -Mode plan`
- [ ] Run public verify:
  - `powershell -ExecutionPolicy Bypass -File jwblng-mvp/playwright/scripts/run-flow.ps1 -Flow verify -Mode plan`
- [ ] Run write-flow plan checks:
  - `join` plan
  - `event` plan
  - `approve` plan
- [ ] Run write-flow apply checks:
  - `join` apply
  - `event` apply
  - `approve` apply
- [ ] Confirm latest artifacts exist in `jwblng-mvp/playwright/artifacts`.

## C) Content and Ops Validation (T-24h to T-12h)
- [ ] Welcome email template reviewed and links verified.
- [ ] Event reminder template reviewed and links verified.
- [ ] Monthly digest template reviewed and links verified.
- [ ] One internal seed test sent for each template.
- [ ] Contact approval tags confirmed:
  - `approved-member`
  - `needs-follow-up`
  - `declined`

## D) Launch Window Readiness (T-4h)
- [ ] Confirm operators available:
  - Timmy
  - Jessica
  - Marcy
- [ ] Confirm MFA overlap window and fallback contact method.
- [ ] Confirm rollback checklist owner is assigned.
- [ ] Confirm comms channel for go/no-go call.

## E) Go/No-Go Gate (T-0h)
- [ ] Canonical join path works from homepage and event pages.
- [ ] Event registration flow works end-to-end.
- [ ] Donation CTA path works and is clearly labeled.
- [ ] No critical defects in latest QA artifacts.
- [ ] Go decision recorded (name/date/time).

## F) Post-Launch (T+2h to T+24h)
- [ ] Monitor join submissions and event registrations.
- [ ] Confirm no broken links reported.
- [ ] Confirm communication sends completed as scheduled.
- [ ] Log issues as Phase 1 hotfix vs Phase 2 backlog.

## Sign-off
- Launch approved by:
  - Name:
  - Role:
  - Date/Time:
