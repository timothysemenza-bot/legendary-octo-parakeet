# JWBLNG Local Kajabi Automation Scaffold

This folder provides a safe starter for running a local browser agent against Kajabi.

## What is included
- `playwright.config.js`: Single-project Chromium config + artifacts.
- `tests/audit.kajabi.spec.js`: Read-only inventory capture.
- `tests/create-join-flow.spec.js`: Write-gated join-page draft script.
- `tests/create-event-template.spec.js`: Write-gated event create-flow draft script.
- `tests/verify-member-journey.spec.js`: Public journey smoke test.
- `utils/env.js`: Environment and safety helpers.

## 1) Install dependencies (from repo root)
```powershell
npm install --save-dev @playwright/test dotenv
npx playwright install chromium
```

## 2) Configure environment
1. Copy `jwblng-mvp/playwright/.env.example` values into your root `.env`.
2. Keep `ALLOW_KAJABI_WRITES=0` until you explicitly want write actions.
3. If your admin URL is site-scoped (for example `app.kajabi.com/admin/sites/<id>/dashboard`), set `KAJABI_ADMIN_BASE_URL`.

## 3) Save authenticated Kajabi storage state
Run this once, log in manually, then close the browser:
```powershell
npx playwright codegen "https://app.kajabi.com/login" --save-storage="jwblng-mvp/playwright/.auth/kajabi-admin.json"
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

## Artifacts
Generated under:
- `jwblng-mvp/playwright/artifacts`
- `jwblng-mvp/playwright/test-results`
- `jwblng-mvp/playwright/playwright-report`

## Safety model
- No write actions unless `ALLOW_KAJABI_WRITES=1`.
- Start with `audit` and `verify` before any write run.
- Review screenshots before publish or delete operations.
