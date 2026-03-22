# JWBLNG Agile Slice Backlog
Date: 2026-02-28

## Loop
1. Pick one slice.
2. Run `apply` for that slice only.
3. Run slice verification.
4. If fail, patch only that slice path and rerun.

## Slice Definitions
| Slice ID | Scope | Apply Command | Verify Command | Status |
|---|---|---|---|---|
| `home-hero` | Homepage hero content surface in Kajabi builder | `powershell -ExecutionPolicy Bypass -File projects/active/client/jwblng-mvp/playwright/scripts/run-slice.ps1 -Slice home-hero -Mode apply` | `powershell -ExecutionPolicy Bypass -File projects/active/client/jwblng-mvp/playwright/scripts/run-slice.ps1 -Slice home-hero -Mode verify` | in_progress |
| `home-cta` | Homepage join/events CTA surface | `powershell -ExecutionPolicy Bypass -File projects/active/client/jwblng-mvp/playwright/scripts/run-slice.ps1 -Slice home-cta -Mode apply` | `powershell -ExecutionPolicy Bypass -File projects/active/client/jwblng-mvp/playwright/scripts/run-slice.ps1 -Slice home-cta -Mode verify` | ready |
| `event-speaker` | Speaker Series page builder target + content pass | `powershell -ExecutionPolicy Bypass -File projects/active/client/jwblng-mvp/playwright/scripts/run-slice.ps1 -Slice event-speaker -Mode apply` | `powershell -ExecutionPolicy Bypass -File projects/active/client/jwblng-mvp/playwright/scripts/run-slice.ps1 -Slice event-speaker -Mode verify` | ready |
| `event-book` | Book Club page builder target + content pass | `powershell -ExecutionPolicy Bypass -File projects/active/client/jwblng-mvp/playwright/scripts/run-slice.ps1 -Slice event-book -Mode apply` | `powershell -ExecutionPolicy Bypass -File projects/active/client/jwblng-mvp/playwright/scripts/run-slice.ps1 -Slice event-book -Mode verify` | ready |
| `event-halacha` | Halacha Circle page builder target + content pass | `powershell -ExecutionPolicy Bypass -File projects/active/client/jwblng-mvp/playwright/scripts/run-slice.ps1 -Slice event-halacha -Mode apply` | `powershell -ExecutionPolicy Bypass -File projects/active/client/jwblng-mvp/playwright/scripts/run-slice.ps1 -Slice event-halacha -Mode verify` | ready |

## Definition of Done Per Slice
- Apply run exits with no Playwright failures.
- Slice verify run exits with no Playwright failures.
- Evidence screenshot exists in `projects/active/client/jwblng-mvp/playwright/artifacts` as `slice-verify-<slice>.png`.

