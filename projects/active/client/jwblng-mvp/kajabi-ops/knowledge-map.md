# Kajabi Ops Knowledge Map (JWBLNG)

## Purpose
Create one canonical reference for how JWBLNG operates Kajabi so automation and manual ops follow the same documented flow.

## Scope
This map targets the Phase 1 workflows only:
- Website page operations
- Events operations
- Contacts/tagging/review
- Email campaigns
- Offers/access control
- Automations used by onboarding and reminders

## Source Strategy
Use these source tiers in order:
1. In-product Kajabi Help links visible in the exact screen being automated.
2. Kajabi Help Center pages for the specific feature.
3. Live JWBLNG tenant UI behavior and snapshots (ground truth for selectors).

## Canonical JWBLNG Admin Entry
- Site admin dashboard: `https://app.kajabi.com/admin/sites/2148584608/dashboard`
- Public site shell: `https://jwblng.org`

## Workflow Map

### 1) Website Pages
- Goal: Create/update website pages safely.
- UI entry: `Main navigation -> Website -> Website Pages`
- Known in-product help link: `https://help.kajabi.com/hc/en-us/articles/360040118874-How-to-Create-a-New-Page`
- Verified flow in tenant:
  1. Click `New Website Page`
  2. Fill `Name` textbox
  3. Click `Customize Page`
- Automation contract:
  - Never assume `/website/pages` path naming.
  - Use visible nav elements and heading assertions.
  - Use role-based locators (`textbox Name`, `button Customize Page`).
- Proof checkpoint:
  - Modal `Add new website page` visible.
  - `Customize Page` becomes enabled after Name input.

### 2) Landing Pages
- Goal: Build/maintain campaign-specific entry pages.
- UI entry: `Website -> Landing Pages`
- Required doc capture:
  - Landing page creation/edit steps from Kajabi Help Center.
- Automation contract:
  - Distinguish Website Pages vs Landing Pages explicitly.
  - Assert current tab state before edit actions.
- Proof checkpoint:
  - Landing page list heading and create CTA visible.

### 3) Navigation
- Goal: Keep canonical Join path reachable from homepage and event surfaces.
- UI entry: `Website -> Navigation`
- Required doc capture:
  - Navbar edit/publish behavior and propagation timing.
- Automation contract:
  - Snapshot nav before edits.
  - Validate no duplicate primary Join CTA.
- Proof checkpoint:
  - Header nav contains approved Join label and URL.

### 4) Events
- Goal: Publish event with consistent RSVP/reminder behavior.
- UI entry: `Marketing -> Events` (tenant-specific nav label can vary).
- Required doc capture:
  - Event creation + reminder scheduling behavior.
- Automation contract:
  - Validate required fields (title/date/time/timezone).
  - Verify published event URL resolves publicly.
- Proof checkpoint:
  - Event status visible and reminder flow configured.

### 5) Contacts + Tags
- Goal: Operate `pending-review -> approved-member|needs-follow-up|declined` workflow.
- UI entry: `Contacts -> All Contacts/segments`
- Required doc capture:
  - Tag rules, bulk actions, and filtering semantics.
- Automation contract:
  - No approval without explicit tag action.
  - Preserve audit trail (screenshots + before/after tag state).
- Proof checkpoint:
  - Contact reflects expected final tag set.

### 6) Email Campaigns
- Goal: Send welcome/reminder/digest safely.
- UI entry: `Marketing -> Email Campaigns`
- Required doc capture:
  - Draft/test/send/schedule sequence.
- Automation contract:
  - Always perform internal seed test before send.
  - Assert segment selected matches campaign type.
- Proof checkpoint:
  - Test send confirmation and valid link checks.

### 7) Offers and Access
- Goal: Ensure free community access and avoid unintended Insider grants.
- UI entry: `Sales -> Offers`
- Required doc capture:
  - Offer assignment and access scoping behavior.
- Automation contract:
  - Verify target offer identity before assignment.
  - Deny ambiguous offer names in automation.
- Proof checkpoint:
  - Contact has intended offer only.

### 8) Automations
- Goal: Trigger onboarding and reminders reliably.
- UI entry: `Marketing -> Automations`
- Required doc capture:
  - Trigger/action limits and sequencing behavior.
- Automation contract:
  - Validate trigger and action chain exists before publish.
  - Disable destructive automation edits in scripted mode by default.
- Proof checkpoint:
  - Automation status active + dry-run conditions met.

## Selector Guidelines (for all scripts)
- Prefer `getByRole`/`getByLabel` with exact visible labels.
- Avoid hardcoded deep URLs when UI navigation exists.
- Never rely on first match from mixed hidden/visible selectors.
- Gate write actions with `ALLOW_KAJABI_WRITES=1`.

## Drift Detection
Run before write operations:
1. `npm run pw:jwblng:audit`
2. `npm run pw:jwblng:verify`

Treat these as drift signals:
- Heading/CTA labels changed
- Sidebar labels changed
- Expected controls hidden/disabled unexpectedly

## Knowledge Capture Backlog
- [ ] Add specific Kajabi Help Center links for Events flow.
- [ ] Add specific Kajabi Help Center links for Email Campaigns flow.
- [ ] Add specific Kajabi Help Center links for Contacts/Tags workflow.
- [ ] Add specific Kajabi Help Center links for Offers/access workflow.
- [ ] Add specific Kajabi Help Center links for Automations workflow.
- [ ] Add JWBLNG screenshots per workflow under `projects/active/client/jwblng-mvp/playwright/artifacts/knowledge-baseline/`.

## Change Control
When UI/docs differ from this map:
1. Capture screenshot + URL + timestamp.
2. Update this map first.
3. Then update automation selectors.
4. Re-run audit + verify before write tests.
