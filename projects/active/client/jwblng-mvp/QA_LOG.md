# JWBLNG QA Log
Date: 2026-03-17

## Manual Public Verification
### Confirmed live on 2026-03-17
- Homepage `/`
  - Updated hero copy is live.
  - Homepage join form remains present.
  - Join buttons remain on the homepage flow.
- About `/about`
  - Updated mission/member-benefit copy is live.
- Contact `/contact`
  - Updated email, phone, and charity number are live.
- Join `/join`
  - Remains a compatibility bridge path, not a second signup funnel.
- Events `/events`
  - Public events hub is live.
- Program pages
  - `/speaker-series`
  - `/book-club`
  - `/halacha-circle`
  - Join intent remains routed into the approved join path.
- Support `/support-jwblng`
  - Updated giving copy is live.
  - `Donate via Zeffy` and `Make a Donation` both point to the approved Zeffy URL.
  - `Email JWBLNG` points to `mailto:info@jwblng.org`.
  - Check-giving guidance, phone, and charity number are visible without inventing a static mailing address.

## Join-Flow Validation
- Canonical join target: `/#block-1772192187104_0`
- Secondary-page compatibility bridge: `/join`
- Homepage form fields confirmed:
  - `name`
  - `email`
  - `interest`
- Smoke submission completed on 2026-03-17:
  - Label: `JWBLNG Smoke Test 2026-03-17`
  - Email: `jwblng-smoke-20260317@example.com`
  - Result: reached Kajabi thank-you state

## Automation / Command Validation
### Updated tests and specs
- `projects/active/client/jwblng-mvp/playwright/tests/verify-member-journey.spec.js`
- `projects/active/client/jwblng-mvp/playwright/tests/verify-homepage-spec.spec.js`
- `projects/active/client/jwblng-mvp/playwright/tests/verify-event-pages-spec.spec.js`
- `projects/active/client/jwblng-mvp/playwright/tests/apply-homepage-content.spec.js`
- `projects/active/client/jwblng-mvp/playwright/tests/sync-phase1-public-pages.spec.js`

### Recommended final rerun before sign-off
- `npm run pw:jwblng:audit`
- `npm run pw:jwblng:verify`
- `npm run pw:jwblng:homeqa`
- `npm run pw:jwblng:eventqa`

### Completed on 2026-03-17
- `npm run pw:jwblng:audit`
- `npm run pw:jwblng:verify`
- `npm run pw:jwblng:homeqa`
- `npm run pw:jwblng:eventqa`
- `JWBLNG Monthly Digest` seed test sent to `timmy@bosskeyops.com`
- Monthly digest test email confirmed in Gmail inbox at 5:09 PM ET
- Fresh artifacts captured in `projects/active/client/jwblng-mvp/playwright/artifacts`, including:
  - `kajabi-audit.json`
  - `admin_dashboard.png`
  - `admin_website_pages.png`
  - `admin_contacts.png`
  - `admin_events.png`
  - `admin_marketing.png`
  - `public-home.png`
  - `public-join-path.png`
  - `public-home-scope-check.png`
  - `public-speaker-series-scope-check.png`
  - `public-book-club-scope-check.png`
  - `public-halacha-circle-scope-check.png`

## Open QA Items
- Re-run the artifact set only if additional public or admin changes are made before handoff.
- Capture seed-test proof for `JWBLNG Welcome Sequence` and `JWBLNG Upcoming Events`.
- Confirm sender/domain setup status if outbound email sends are blocked.
