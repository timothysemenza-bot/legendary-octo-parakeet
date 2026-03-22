# RUNBOOK - JWBLNG Kajabi Ops Agent

## Scope
This runbook covers Phase 1 execution and closeout for JWBLNG's constrained Kajabi MVP.

It is aligned to:
- `projects/active/client/jwblng-mvp/JWBLNG-Donated-Scope-One-Pager.md`
- `projects/active/client/jwblng-mvp/SCOPE_DECISION_LOCK.md`
- `projects/active/client/jwblng-mvp/notes/meeting-notes-2026-03-17-jessica-follow-up.md`
- `projects/active/client/jwblng-mvp/transcripts/jwblng-meeting-2026-03-16-transcript-extract.md`
- `projects/active/client/jwblng-mvp/SCOPE_EXECUTION_STATUS.md`
- `projects/active/client/jwblng-mvp/COMMUNICATION_STARTER_PACK.md`
- `projects/active/client/jwblng-mvp/QA_LOG.md`
- `projects/active/client/jwblng-mvp/HANDOFF_NOTES.md`

## Operating Principles
- Use one canonical join path.
- Keep membership free in Phase 1.
- Keep the public site simple and easy to explain.
- Keep public content broad and discoverable.
- Keep sensitive member actions behind approval/login.
- Do not make production write changes without capturing current-state notes and a rollback path.

## Current Phase 1 Public Architecture
- Canonical join target: `/#block-1772192187104_0`
- Compatibility bridge: `/join`
- Public nav: `About Us`, `Events`, `Donate`, plus Kajabi `Log In`
- Public pages in scope:
  - `/`
  - `/about`
  - `/contact`
  - `/events`
  - `/speaker-series`
  - `/book-club`
  - `/halacha-circle`
  - `/support-jwblng`
- Donation surface: Zeffy via `/support-jwblng`

## Access and Security
### Required systems
- Kajabi
- DNS/domain owner when sender or domain work is required
- Zeffy
- Zoom, if event logistics require it

### Access rules
- Credentials live in 1Password only.
- MFA codes are approved by the designated owner during an agreed overlap window.
- Never share passwords or MFA codes in chat or email.

### Pre-change safety checklist
1. Confirm the page or workflow you are changing.
2. Confirm the last-known-good path from `projects/active/client/jwblng-mvp/ROLLBACK_CHECKLIST.md`.
3. Confirm whether write actions are enabled for automation (`ALLOW_KAJABI_WRITES=1`).

## Standard Workflows
### 1) Contact approval workflow
1. Open Kajabi Contacts segment `pending-review`.
2. Validate legitimacy and any referral context.
3. Approve by adding `approved-member`.
4. Hold or reject by adding `needs-follow-up` or `declined`.
5. Confirm only free community access is granted.
6. If the automation does not send the welcome message, use the manual fallback email draft.

### 2) Event publishing workflow
1. Create or update the event/program page.
2. Confirm title, date/time/timezone, summary, and visibility.
3. Confirm any public join CTA routes into the approved join path.
4. Trigger or schedule the reminder communication.
5. Verify the public page after saving.

### 3) Communication workflow
1. Start from the approved Kajabi draft.
2. Select the correct audience.
3. Send an internal seed test.
4. Verify sender identity, formatting, and links.
5. Schedule or send.
6. Record any blocker in `projects/active/client/jwblng-mvp/HANDOFF_NOTES.md`.

### 4) Join-flow governance
1. Keep one canonical join URL: `/#block-1772192187104_0`.
2. Use `/join` only where Kajabi strips homepage fragments on secondary pages.
3. Preserve the homepage form contract:
  - `name`
  - `email`
  - `interest`
4. Do not create a second public signup journey.

## Automation Operations (Local Playwright)
Path: `projects/active/client/jwblng-mvp/playwright`

### Setup
1. `npm install`
2. `npx playwright install chromium`
3. Populate root `.env` values from `projects/active/client/jwblng-mvp/playwright/.env.example`
4. Save authenticated state:
   `npx playwright codegen "https://app.kajabi.com/login" --save-storage="projects/active/client/jwblng-mvp/playwright/.auth/kajabi-admin.json"`

### Commands
- Read-only audit: `npm run pw:jwblng:audit`
- Public journey verify: `npm run pw:jwblng:verify`
- Homepage QA: `npm run pw:jwblng:homeqa`
- Homepage builder QA: `npm run pw:jwblng:homebuilderqa`
- Event-page QA: `npm run pw:jwblng:eventqa`
- Write-gated join compatibility flow: `npm run pw:jwblng:join`
- Write-gated homepage content apply: `npm run pw:jwblng:homeapply`
- Write-gated scope pages apply: `npm run pw:jwblng:scopepages`
- Write-gated public-page sync: `npm run pw:jwblng:phase1pages`
- Write-gated event flow: `npm run pw:jwblng:event`
- Write-gated contact approval flow: `npm run pw:jwblng:approve`

### Artifacts
- `projects/active/client/jwblng-mvp/playwright/artifacts`
- `projects/active/client/jwblng-mvp/playwright/test-results`
- `projects/active/client/jwblng-mvp/playwright/playwright-report`

## Launch Readiness
### Go/No-Go checks
- Canonical join path works from homepage and event/program pages.
- Donation CTA path works.
- Approval workflow grants only intended access.
- Kajabi drafts exist for welcome, reminder, and digest communications.
- Current QA evidence is attached.
- Open issues are classified and owned.

### Rollback triggers
- Broken join path or failed submissions
- Wrong offer/access assignment
- Broken event or donation links
- Broken links in outbound campaigns

### Rollback action
- Revert to the last-known-good public paths from `projects/active/client/jwblng-mvp/ROLLBACK_CHECKLIST.md`.
- Re-run verification.
- Record the incident and owner.

## Handoff
1. Run the supervised walkthrough with Jessica and Marcy.
2. Complete one supervised run of each core workflow:
   - approve a contact
   - update/publish an event
   - send or edit an email draft
3. Record any remaining dependency in `projects/active/client/jwblng-mvp/HANDOFF_NOTES.md`.
4. Record sign-off.

## Checkpoint Log
- 2026-02-28: Kajabi automation baseline stabilized.
- 2026-02-28: Audit paths updated to valid tenant routes.
- 2026-02-28: Join compatibility flow automated for `/join`.
- 2026-02-28: Event flow implemented for draft creation and evidence capture.
- 2026-03-17: Canonical join governance updated to homepage form + `/join` bridge.
- 2026-03-17: March 16 transcript and March 17 follow-up notes normalized into the repo.
- 2026-03-17: Homepage, About, and Contact public copy refreshed using transcript and Wix source material.
