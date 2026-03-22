# JWBLNG Kajabi Workflow Contract

This contract defines stable automation behavior for write-gated Kajabi flows.

## Global Contract
- All write flows require `ALLOW_KAJABI_WRITES=1`.
- `JWBLNG_RUN_MODE=plan` runs navigation/validation/screenshots only (no writes).
- `JWBLNG_RUN_MODE=apply` executes write actions.
- All flows run against `KAJABI_ADMIN_BASE_URL` (or `KAJABI_BASE_URL` fallback).
- Every flow must:
  - navigate via visible UI controls,
  - fail with a concrete reason when required controls are missing,
  - write screenshots to `projects/active/client/jwblng-mvp/playwright/artifacts`.

## Flow: Join Compatibility Page Draft
- Command: `npm run pw:jwblng:join`
- Required env:
  - `ALLOW_KAJABI_WRITES=1`
- Optional env:
  - `JWBLNG_JOIN_PAGE_TITLE` (default: `Join JWBLNG`)
  - `JWBLNG_JOIN_PAGE_PATH` (default: `/join`, compatibility bridge path)
- Expected behavior:
  - open Website Pages,
  - start new page flow,
  - handle create modal if present,
  - retry with unique name if duplicate-name validation appears,
  - attempt customize/builder transition,
  - attempt draft save when save/update controls are available.
- Artifacts:
  - `join-page-draft-before-customize.png`
  - `join-page-draft-after-customize.png`
  - `join-page-draft-before-save.png`
  - `join-page-draft-after-save.png`

## Flow: Event Draft
- Command: `npm run pw:jwblng:event`
- Required env:
  - `ALLOW_KAJABI_WRITES=1`
- Optional env:
  - `JWBLNG_EVENT_TITLE`
  - `JWBLNG_EVENT_DATE`
  - `JWBLNG_EVENT_TIME`
  - `JWBLNG_EVENT_TIMEZONE`
  - `JWBLNG_EVENT_DESCRIPTION`
- Expected behavior:
  - open Marketing > Events,
  - start new event flow,
  - fill supported fields,
  - click save and verify a post-submit state.
- Artifacts:
  - `event-flow-events-screen.png`
  - `event-flow-create-dialog.png`
  - `event-flow-after-save.png`

## Flow: Approve Contact by Tag
- Command: `npm run pw:jwblng:approve`
- Required env:
  - `ALLOW_KAJABI_WRITES=1`
  - `JWBLNG_CONTACT_EMAIL_FILTER`
- Optional env:
  - `JWBLNG_APPROVAL_TAG` (default: `approved-member`)
- Expected behavior:
  - open Contacts > All Contacts,
  - search contact by email,
  - open contact detail (drawer/page),
  - apply tag through supported tag UI variant:
    - textbox/combobox input, or
    - modal picker (`Select tags`).
- Artifacts:
  - `contact-flow-before-open.png`
  - `contact-flow-after-tag.png`

## Flow: Homepage Content Apply
- Command: `npm run pw:jwblng:homeapply`
- Required env:
  - `ALLOW_KAJABI_WRITES=1`
- Optional env:
  - `JWBLNG_CANONICAL_JOIN_URL` (default: `/#block-1772192187104_0`)
  - `JWBLNG_HOMEPAGE_NAME` (default: `Home`)
  - `JWBLNG_HOMEPAGE_HEADLINE`
  - `JWBLNG_HOMEPAGE_SUBHEAD`
  - `JWBLNG_HOMEPAGE_PRIMARY_CTA_TEXT`
  - `JWBLNG_HOMEPAGE_PRIMARY_CTA_LINK`
  - `JWBLNG_HOMEPAGE_SECONDARY_CTA_TEXT`
  - `JWBLNG_HOMEPAGE_SECONDARY_CTA_LINK`
  - `JWBLNG_HOMEPAGE_DONATION_LINK`
- Expected behavior:
  - open Website > Pages,
  - locate the configured homepage row,
  - open customize/builder context,
  - apply supported headline/body/CTA field edits,
  - default homepage join CTA targets to `JWBLNG_CANONICAL_JOIN_URL` when no explicit override is provided,
  - save/update when control is available.
- Artifacts:
  - `homepage-flow-pages-list.png`
  - `homepage-flow-before-save.png`
  - `homepage-flow-after-save.png`

## Flow: Homepage Builder Verification
- Command: `npm run pw:jwblng:homebuilderqa`
- Required env:
  - none
- Optional env:
  - `JWBLNG_HOMEPAGE_NAME` (default: `Home`)
- Expected behavior:
  - open Website > Pages,
  - open homepage in customize/builder context,
  - assert preview includes join/member CTA, events link, and hero heading.
- Artifacts:
  - `homepage-builder-preview-check.png`

## Flow: Scoped Event Pages Ensure/Create
- Command: `npm run pw:jwblng:scopepages`
- Required env:
  - `ALLOW_KAJABI_WRITES=1` (apply mode)
- Optional env:
  - `JWBLNG_SCOPE_PAGE_TITLES` (pipe-delimited; default `Speaker Series|Book Club|Halacha Circle`)
- Expected behavior:
  - open Website > Pages,
  - ensure each configured page exists,
  - if missing (apply mode), create page via `New Website Page`,
  - open builder context for newly created pages and return to Pages list.
- Artifacts:
  - `scope-pages-<slug>-builder.png` (for created pages)
  - `scope-pages-summary.png`

## Flow: Scoped Event Pages Content Apply
- Command: `npm run pw:jwblng:eventpagesapply`
- Required env:
  - `ALLOW_KAJABI_WRITES=1` (apply mode)
- Expected behavior:
  - open each scoped event page in builder context,
  - attempt section/block text updates with safe selectors,
  - save when controls are editable,
  - return to Pages list after each page.
- Notes:
  - Some Kajabi theme/editor variants expose no automatable text controls in the current accessibility tree.
  - In that case flow logs `No editable controls detected for: ...` and still captures evidence screenshots.
- Artifacts:
  - `event-pages-<slug>-after-save.png`

## Failure Codes (Current)
- `Could not find visible create-page control on Pages screen`
- `Join page flow did not reach builder context after create/customize`
- `Could not find a visible Event Title/Name input`
- `Event save did not leave create form`
- `No visible contact row found for '<email>'`
- `Did not open contact detail view; still on contacts list/tag management page`
- `Could not apply tag '<tag>' (tag_control_not_found)`
- `Could not apply tag '<tag>' (tag_input_not_found)`
- `Could not find homepage row '<name>'`
- `Did not reach homepage builder context`
- `Reached builder, but Save/Update control was not visible`
- `Expected join/membership CTA in homepage preview`
- `Expected events link in homepage preview`
- `Missing scoped pages: ...`

## Operator Run Checklist
1. `cd C:\Users\timot\Documents\Proposal-Microsite`
2. Set required env vars for the target flow.
3. Run one flow at a time.
4. On failure, capture:
   - test error text,
   - page snapshot,
   - latest artifact filenames.

## One-Command Runner
- Script: `projects/active/client/jwblng-mvp/playwright/scripts/run-flow.ps1`
- Supported flows: `join`, `event`, `approve`, `audit`, `verify`
- Supported flows: `join`, `event`, `approve`, `homepage`, `homeverify`, `scopepages`, `eventpages`, `audit`, `verify`
- Modes: `-Mode plan` or `-Mode apply`
- Example:
  - `powershell -ExecutionPolicy Bypass -File projects/active/client/jwblng-mvp/playwright/scripts/run-flow.ps1 -Flow approve -Mode plan -ContactEmail "timmy@bosskeyops.com"`
  - `powershell -ExecutionPolicy Bypass -File projects/active/client/jwblng-mvp/playwright/scripts/run-flow.ps1 -Flow approve -Mode apply -AllowWrites -ContactEmail "timmy@bosskeyops.com" -ApprovalTag "approved-member"`
