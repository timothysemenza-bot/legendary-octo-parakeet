# JWBLNG Local Kajabi Automation Scaffold

This folder provides a safe starter for running a local browser agent against Kajabi.

## What is included
- `playwright.config.js`: Single-project Chromium config + artifacts.
- `tests/audit.kajabi.spec.js`: Read-only inventory capture.
- `tests/create-join-flow.spec.js`: Write-gated `/join` compatibility-page draft script.
- `tests/create-event-template.spec.js`: Write-gated event create-flow draft script.
- `tests/apply-homepage-content.spec.js`: Write-gated homepage content apply script (Kajabi editor).
- `tests/verify-member-journey.spec.js`: Public homepage-form journey smoke test.
- `utils/env.js`: Environment and safety helpers.

## 1) Install dependencies (from repo root)
```powershell
npm install --save-dev @playwright/test dotenv
npx playwright install chromium
```

## 2) Configure environment
1. Copy `projects/active/client/jwblng-mvp/playwright/.env.example` values into your root `.env`.
2. Keep `ALLOW_KAJABI_WRITES=0` until you explicitly want write actions.
3. If your admin URL is site-scoped (for example `app.kajabi.com/admin/sites/<id>/dashboard`), set `KAJABI_ADMIN_BASE_URL`.

## 3) Save authenticated Kajabi storage state
Run this once, log in manually, then close the browser:
```powershell
npx playwright codegen "https://app.kajabi.com/login" --save-storage="projects/active/client/jwblng-mvp/playwright/.auth/kajabi-admin.json"
```

## 4) Run tests
Read-only audit:
```powershell
npm run pw:jwblng:audit
```

Public journey smoke test:
```powershell
npm run pw:jwblng:verify
```

Homepage QA in Kajabi builder preview (works even when public domain is in coming-soon mode):
```powershell
npm run pw:jwblng:homebuilderqa
```

Agile slice verification (single-slice checks):
```powershell
$env:JWBLNG_SLICE_ID="home-cta"
npm run pw:jwblng:sliceverify
```

Write-gated draft flow (only after review):
```powershell
$env:ALLOW_KAJABI_WRITES="1"
npm run pw:jwblng:join
```

Write-gated event draft flow:
```powershell
$env:ALLOW_KAJABI_WRITES="1"
npm run pw:jwblng:event
```

Optional event env vars:
- `JWBLNG_EVENT_TITLE`
- `JWBLNG_EVENT_DATE` (format expected by your Kajabi date input)
- `JWBLNG_EVENT_TIME` (format expected by your Kajabi time input)
- `JWBLNG_EVENT_TIMEZONE` (label text match, e.g. `Eastern`)
- `JWBLNG_EVENT_DESCRIPTION`

Write-gated contact approval flow (requires email filter):
```powershell
$env:ALLOW_KAJABI_WRITES="1"
npm run pw:jwblng:approve
```

Write-gated homepage content apply flow:
```powershell
$env:ALLOW_KAJABI_WRITES="1"
npm run pw:jwblng:homeapply
```

Write-gated scoped event pages ensure/create flow:
```powershell
$env:ALLOW_KAJABI_WRITES="1"
npm run pw:jwblng:scopepages
```

Write-gated scoped event pages content-apply flow:
```powershell
$env:ALLOW_KAJABI_WRITES="1"
npm run pw:jwblng:eventpagesapply
```

Write-gated global brand palette flow (Encore Style Guide):
```powershell
$env:ALLOW_KAJABI_WRITES="1"
npm run pw:jwblng:palette
```

Optional homepage env vars:
- `JWBLNG_CANONICAL_JOIN_URL` (default `/#block-1772192187104_0`)
- `JWBLNG_HOMEPAGE_NAME` (default `Home`)
- `JWBLNG_HOMEPAGE_HEADLINE`
- `JWBLNG_HOMEPAGE_SUBHEAD`
- `JWBLNG_HOMEPAGE_PRIMARY_CTA_TEXT`
- `JWBLNG_HOMEPAGE_PRIMARY_CTA_LINK`
- `JWBLNG_HOMEPAGE_SECONDARY_CTA_TEXT`
- `JWBLNG_HOMEPAGE_SECONDARY_CTA_LINK`
- `JWBLNG_HOMEPAGE_DONATION_LINK`
- `JWBLNG_SCOPE_PAGE_TITLES` (pipe-delimited, default `Speaker Series|Book Club|Halacha Circle`)

### Optional: One-command PowerShell runner
Use `projects/active/client/jwblng-mvp/playwright/scripts/run-flow.ps1` to set env vars and run a flow in one command.
- `-Mode plan`: navigation/validation/screenshots only (no mutations)
- `-Mode apply`: execute write actions (requires `-AllowWrites` for write flows)

Examples:
```powershell
powershell -ExecutionPolicy Bypass -File projects/active/client/jwblng-mvp/playwright/scripts/run-flow.ps1 -Flow audit -Mode plan
powershell -ExecutionPolicy Bypass -File projects/active/client/jwblng-mvp/playwright/scripts/run-flow.ps1 -Flow join -Mode plan
$env:JWBLNG_CANONICAL_JOIN_URL="/#block-1772192187104_0"
powershell -ExecutionPolicy Bypass -File projects/active/client/jwblng-mvp/playwright/scripts/run-flow.ps1 -Flow join -Mode apply -AllowWrites -JoinTitle "Join JWBLNG" -JoinPath "/join"
powershell -ExecutionPolicy Bypass -File projects/active/client/jwblng-mvp/playwright/scripts/run-flow.ps1 -Flow event -Mode apply -AllowWrites -EventDate "03/15/2026" -EventTime "7:00 PM" -EventTimezone "Eastern"
powershell -ExecutionPolicy Bypass -File projects/active/client/jwblng-mvp/playwright/scripts/run-flow.ps1 -Flow approve -Mode apply -AllowWrites -ContactEmail "timmy@bosskeyops.com" -ApprovalTag "approved-member"
powershell -ExecutionPolicy Bypass -File projects/active/client/jwblng-mvp/playwright/scripts/run-flow.ps1 -Flow homepage -Mode apply -AllowWrites -HomepageName "Home" -HomepagePrimaryCtaText "Join JWBLNG" -HomepageSecondaryCtaText "View Events" -HomepageSecondaryCtaLink "/events"
powershell -ExecutionPolicy Bypass -File projects/active/client/jwblng-mvp/playwright/scripts/run-flow.ps1 -Flow homeverify -Mode plan -HomepageName "Home"
powershell -ExecutionPolicy Bypass -File projects/active/client/jwblng-mvp/playwright/scripts/run-flow.ps1 -Flow scopepages -Mode apply -AllowWrites
powershell -ExecutionPolicy Bypass -File projects/active/client/jwblng-mvp/playwright/scripts/run-flow.ps1 -Flow eventpages -Mode apply -AllowWrites
powershell -ExecutionPolicy Bypass -File projects/active/client/jwblng-mvp/playwright/scripts/run-flow.ps1 -Flow palette -Mode apply -AllowWrites
powershell -ExecutionPolicy Bypass -File projects/active/client/jwblng-mvp/playwright/scripts/run-slice.ps1 -Slice home-cta -Mode apply
```

Optional contact env vars:
- `JWBLNG_CONTACT_EMAIL_FILTER` (required for safety in approve flow)
- `JWBLNG_APPROVAL_TAG` (defaults to `approved-member`)

## Artifacts
Generated under:
- `projects/active/client/jwblng-mvp/playwright/artifacts`
- `projects/active/client/jwblng-mvp/playwright/test-results`
- `projects/active/client/jwblng-mvp/playwright/playwright-report`

## Safety model
- No write actions unless `ALLOW_KAJABI_WRITES=1`.
- Start with `audit` and `verify` before any write run.
- Review screenshots before publish or delete operations.

## Workflow Contract
- See `projects/active/client/jwblng-mvp/playwright/WORKFLOW_CONTRACT.md` for flow inputs, expected outcomes, artifacts, and failure codes.
