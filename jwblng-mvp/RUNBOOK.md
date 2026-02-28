# RUNBOOK - JWBLNG Kajabi Ops Agent

## Scope
This runbook covers Phase 1 execution for JWBLNG's constrained Kajabi MVP.
It is aligned to:
- `jwblng-mvp/JWBLNG-Donated-Scope-One-Pager.md`
- `jwblng-mvp/transcripts/meeting-2026-02-26-notes-action-plan.md`
- `jwblng-mvp/backlog/tasks.yaml`

## Operating Principles
- Use one canonical join path.
- Keep membership free in Phase 1; design for future paid upsells.
- Keep public brand anchored to `jwblng.org`.
- Prefer simple operator workflows over technical complexity.
- No production write changes without snapshot + rollback notes.

## Access and Security
### Required systems
- Kajabi (admin/operator)
- Domain DNS owner (Kajabi-managed Cloudflare or registrar)
- Zeffy
- Zoom (when available)

### Access control rules
- Credentials live in 1Password only.
- MFA codes are approved by designated owner in agreed overlap window.
- Never share passwords or MFA codes in chat/email.

### Pre-change safety checklist
1. Confirm current-state snapshots exist (pages, nav, offers, automations, DNS).
2. Confirm rollback path for planned edits.
3. Confirm whether write actions are enabled in automation (`ALLOW_KAJABI_WRITES=1`).

## Standard Workflows
### 1) Contact approval workflow
1. Open Kajabi Contacts segment `pending-review`.
2. Validate legitimacy and referral context.
3. Approve: add `approved-member` tag.
4. Hold/reject: add `needs-follow-up` or `declined`.
5. Confirm only intended access offer is granted.

### 2) Event publishing workflow
1. Create event with title, date/time/timezone, and summary.
2. Set visibility (community vs insider).
3. Add RSVP path and meeting link process.
4. Trigger reminder communication.
5. Validate public and member-facing links.

### 3) Communication workflow
1. Use approved template (welcome, reminder, digest).
2. Select correct audience segment.
3. Send internal seed test.
4. Verify links, formatting, and sender identity.
5. Schedule/send and log campaign intent.

### 4) Join-flow governance
1. Keep one canonical join URL.
2. Route homepage and event CTAs to that URL.
3. Capture intent fields needed for segmentation.
4. Confirm success page gives clear next action.

## Automation Operations (Local Playwright)
Path: `jwblng-mvp/playwright`

### Setup
1. `npm install`
2. `npx playwright install chromium`
3. Populate root `.env` values from `jwblng-mvp/playwright/.env.example`
4. Save authenticated state:
   `npx playwright codegen "https://app.kajabi.com/login" --save-storage="jwblng-mvp/playwright/.auth/kajabi-admin.json"`

### Commands
- Read-only audit: `npm run pw:jwblng:audit`
- Public journey verify: `npm run pw:jwblng:verify`
- Write-gated join draft: set `ALLOW_KAJABI_WRITES=1` then run `npm run pw:jwblng:join`
- Write-gated event draft: set `ALLOW_KAJABI_WRITES=1` then run `npm run pw:jwblng:event`
- Persistent event loop (no browser relaunch): set `ALLOW_KAJABI_WRITES=1` then run `npm run pw:jwblng:event:persistent`

### Artifact locations
- `jwblng-mvp/playwright/artifacts`
- `jwblng-mvp/playwright/test-results`
- `jwblng-mvp/playwright/playwright-report`

## Launch Readiness
### Go/No-Go checks
- Canonical join path is working from homepage, event pages, and email templates.
- RSVP + reminder flow passes internal test.
- Donation CTA path works without redirect issues.
- Admin team can execute contact, event, and communication workflows.
- Rollback notes are current.

### Rollback triggers
- Broken join path or failed submissions.
- Unauthorized access exposure risk.
- Event or email links routing incorrectly.

### Rollback action
- Revert nav/CTA changes to last-known-good paths.
- Disable failing automations.
- Restore previous public links until issue is fixed.

## Handoff
1. Run 60-90 minute walkthrough with Jessica/Marcy.
2. Execute one supervised run of each core workflow.
3. Log unresolved issues and classify as Phase 1 fix or Phase 2 scope.
4. Record sign-off decision.

## Checkpoint Log
- 2026-02-28: Kajabi automation baseline stabilized.
- 2026-02-28: Audit paths updated to tenant-valid routes (`website_pages`, `contacts`, `email_campaigns`).
- 2026-02-28: Join flow aligned to Kajabi modal sequence (`New Website Page` -> `Name` -> `Customize Page`).
- 2026-02-28: Event flow implemented (standard and persistent runner), including draft field-fill and artifacts.
