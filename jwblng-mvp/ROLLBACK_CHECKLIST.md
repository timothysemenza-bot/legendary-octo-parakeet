# JWBLNG Phase 1 Rollback Checklist
Date: 2026-02-28

Use this checklist if launch introduces critical issues in join, events, or donation paths.

## Trigger Conditions
- [ ] Canonical join path is broken or submissions fail.
- [ ] Event registration links fail or route incorrectly.
- [ ] Donation CTA routes to invalid or unintended destination.
- [ ] Unauthorized access risk is detected.
- [ ] Critical communication template sends with broken links.

## Immediate Containment (First 15 Minutes)
- [ ] Pause any pending outbound sends tied to affected links.
- [ ] Revert homepage primary CTA to last-known-good destination.
- [ ] Revert event CTA(s) to last-known-good destination.
- [ ] Disable/undo the most recent risky automation change.
- [ ] Notify ops channel: issue detected, rollback in progress.

## Technical Reversion Steps
- [ ] Restore previous nav/CTA configuration in Kajabi.
- [ ] Restore previous join path if latest page variant is failing.
- [ ] Re-point donation CTA to previously validated Zeffy link.
- [ ] Re-run read-only audit and verify checks:
  - `audit` plan
  - `verify` plan
- [ ] Capture rollback-state screenshots in `jwblng-mvp/playwright/artifacts`.

## Validation After Rollback
- [ ] Homepage CTA is functional.
- [ ] Join flow reaches expected confirmation path.
- [ ] Event page registration path is functional.
- [ ] Donation path resolves correctly.
- [ ] Contact approval workflow still operational.

## Incident Record
- Incident start (date/time):
- Trigger condition:
- Changes reverted:
- Operator:
- Validation completed by:
- Residual risk:
- Next-step recommendation:

## Escalation and Follow-up
- [ ] Classify issue as:
  - [ ] Phase 1 hotfix
  - [ ] Phase 2 enhancement
- [ ] Schedule remediation window.
- [ ] Update `jwblng-mvp/SCOPE_EXECUTION_STATUS.md` with incident notes.
