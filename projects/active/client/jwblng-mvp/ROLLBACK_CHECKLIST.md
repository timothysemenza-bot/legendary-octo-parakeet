# JWBLNG Phase 1 Rollback Checklist
Date: 2026-03-17

Use this checklist if a Phase 1 closeout or launch change breaks the approved public journey.

## Last-Known-Good Public State
- Homepage: `https://www.jwblng.org/`
- Canonical join target: `https://www.jwblng.org/#block-1772192187104_0`
- Compatibility bridge: `https://www.jwblng.org/join`
- Events hub: `https://www.jwblng.org/events`
- Program pages:
  - `https://www.jwblng.org/speaker-series`
  - `https://www.jwblng.org/book-club`
  - `https://www.jwblng.org/halacha-circle`
- Donation surface: `https://www.jwblng.org/support-jwblng`

## Trigger Conditions
- [ ] Homepage join CTAs stop scrolling or routing into the approved join flow.
- [ ] `/join` stops acting as a simple bridge.
- [ ] Event/program page join CTAs route to the wrong destination.
- [ ] Donation CTA routes to an invalid or unintended destination.
- [ ] Approval workflow grants the wrong offer or wrong access level.
- [ ] Outbound email drafts contain broken public links.

## Immediate Containment
- [ ] Pause any pending sends that contain affected links.
- [ ] Revert homepage CTAs to the last-known-good join/event paths.
- [ ] Revert event/program page CTAs to `/join` if any direct link has broken.
- [ ] Revert donation CTA to the previously validated Zeffy URL.
- [ ] Notify operators that rollback is in progress.

## Technical Reversion Steps
- [ ] Restore prior Kajabi copy/CTA configuration from the last saved good state.
- [ ] Re-confirm homepage join button target.
- [ ] Re-confirm `/join` bridge behavior.
- [ ] Re-confirm support-page donation button target.
- [ ] Re-run:
  - `npm run pw:jwblng:verify`
  - `npm run pw:jwblng:homeqa`
  - `npm run pw:jwblng:eventqa`
- [ ] Save rollback screenshots/artifacts in `projects/active/client/jwblng-mvp/playwright/artifacts`.

## Validation After Rollback
- [ ] Homepage hero CTA is functional.
- [ ] Homepage join form is reachable and submittable.
- [ ] Event and program pages route back into the approved join path.
- [ ] Donation path resolves correctly.
- [ ] Approval workflow still applies only the intended free community access.

## Incident Record
- Incident start:
- Trigger condition:
- Changes reverted:
- Operator:
- Validation completed by:
- Residual risk:
- Next-step recommendation:

## Follow-up
- [ ] Classify issue as Phase 1 hotfix or later-phase work.
- [ ] Update `projects/active/client/jwblng-mvp/SCOPE_EXECUTION_STATUS.md`.
- [ ] Add note to `projects/active/client/jwblng-mvp/HANDOFF_NOTES.md` if the issue impacts client training or launch timing.
