# JWBLNG Scope Decision Lock
Date: 2026-02-28
Status: Approved

Purpose: Freeze the remaining business decisions required to close donated Phase 1 scope.

## Decision 1: Canonical Member Journey Copy
- Scope reference: Member Journey Blueprint (`discover -> join -> onboard -> first event -> ongoing communications`)
- Decision needed:
  - Final CTA labels for homepage, event pages, and onboarding success state.
- Recommended default:
  - Primary CTA: `Join JWBLNG`
  - Secondary CTA: `View Events`
  - Post-join next step: `Register for Your First Event`
- Owner: Jessica / Marcy
- Status: Approved

## Decision 2: Donation CTA Mode (Zeffy)
- Scope reference: one donation CTA path
- Decision needed:
  - `embed` vs `external link` from onboarding/event pages.
- Recommended default:
  - `external link` in Phase 1 for lower implementation risk and easier rollback.
- Owner: Jessica / Marcy
- Status: Approved

## Decision 3: Wix Preserve List (Cutover Safety)
- Scope reference: Wix likely retired after equivalent Kajabi flows are in place.
- Decision needed:
  - Explicit list of Wix pages that must remain reachable at cutover.
- Recommended default:
  - Preserve only legal/compliance pages not yet mirrored in Kajabi.
- Owner: Jessica / Marcy
- Status: Approved

## Decision 4: Communication Starter Pack Sign-off
- Scope reference: welcome/reminder/digest + monthly calendar
- Decision needed:
  - Approve final template copy and owner checklist.
- Recommended default:
  - Run one internal seed-test for each template before sign-off.
- Owner: Jessica / Marcy
- Status: Approved

## Decision 5: Handoff Session Date and Approvers
- Scope reference: 60-90 minute handoff session
- Decision needed:
  - Session date/time and required attendees for final acceptance.
- Recommended default:
  - Include Jessica + Marcy + operator; record session and action list.
- Owner: Timmy + Jessica/Marcy
- Status: Approved

## Sign-off Block
- Decision lock approved by:
  - Name: Timmy Semenza
  - Role: Operator / Implementation Lead
  - Date: 2026-02-28
