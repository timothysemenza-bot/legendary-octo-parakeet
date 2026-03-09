# Janitorial Contract Capture OS Operator Guide

## Purpose

This system is an internal operating layer for janitorial and facilities-services capture work. It is designed to help you identify rebids early, qualify them, match realistic bidders, manage pre-RFP capture actions, and track your own consulting economics without collapsing into a generic CRM.

## Setup

1. Install dependencies.
2. Run `python -m alembic upgrade head`.
3. Start the app with `python -m uvicorn app.main:app --reload`.
4. Open `http://127.0.0.1:8000/dashboard`.

For demo data, use `POST /api/dashboard/seed-demo` or the `Seed Demo Data` action on the dashboard.

## Core workflow

### 1. Build the market base

Use these screens first:
- `/organizations`
- `/facilities`
- `/contracts`

Recommended order:
1. Create the buying organization.
2. Add one or more facilities or a portfolio record.
3. Add the current janitorial contract and tie it to the relevant facilities.

The contracts screen is the contract radar. Use it to filter by geography, facility type, incumbent vendor, and rebid timing.

### 2. Import contract radar data

The MVP importer accepts CSV uploads through the contracts screen or `POST /api/contracts/import`.

Required/expected columns:
- `organization_name`
- `organization_type`
- `facility_name`
- `facility_kind`
- `city`
- `state`
- `contract_title`
- `incumbent_vendor`
- `annual_value`
- `total_value`
- `start_date`
- `expiration_date`
- `rebid_window_start`
- `rebid_window_end`
- `procurement_source_url`
- `source_type`
- `source_notes`

Date fields should be ISO format, for example `2026-09-30`.

### 3. Create a pursuit from a contract

From a contract detail page, create a pursuit when there is enough evidence that a rebid or net-new opportunity is real enough to track.

The pursuit bootstrap captures:
- Buying organization
- Primary facility
- Primary contract
- Confidence level
- Expected RFP date
- Provenance summary
- Initial scoring inputs

The system computes:
- `qualification_score`
- `score_breakdown_json`
- `weighted_pipeline_value`
- `pursuit_stage`
- downstream `proposal_stage`

Operator-facing contractor pipeline fields use controlled categories for stage, scale, labor profile, and union profile so follow-up reporting remains consistent.

The contract-detail pursuit bootstrap also uses controlled choices for:
- `pursuit_stage`
- `confidence_level`
- initial 1-5 qualification score inputs

### 4. Tune scoring

Use `/settings/scoring` to edit default weights for:
- Opportunity scoring
- Contractor fit scoring

Opportunity scoring is intended for prioritization, not precision forecasting. Use it to decide where pre-RFP effort is justified.

### 5. Manage contractor prospects

Use `/contractors` and `/contractors/{id}` to maintain a contractor-side prospect pipeline before a specific pursuit is active.

Track on each contractor:
- `prospect_stage`
- `next_follow_up_date`
- `last_touch_at`
- touchpoint history with contact name, interaction type, summary, and next step

Recommended operator sequence:
1. Create the contractor prospect record.
2. Set the initial `prospect_stage`.
3. Log each outreach, meeting, or note as a touchpoint.
4. Carry the next follow-up date forward from the most recent confirmed next step.
5. Once the contractor is `ENGAGED`, use `/contractors/{id}` to either:
   - create a new pursuit handoff from a contract and seed the advised contractor automatically, or
   - link the contractor to an existing opportunity without creating a duplicate commercial row.
6. Move into pursuit-specific commercials only once an active engagement exists.

### 6. Run the capture workbench

Use `/opportunities/{id}/capture-workbench` once a pursuit is active.

This workspace supports:
- Contractor match refresh
- Buyer and contractor contacts
- Intelligence notes
- Evidence records
- Capture actions
- Commercial engagement tracking

Recommended operator sequence:
1. Refresh contractor matches.
2. Add buyer-side and contractor-side contacts.
3. Record intelligence with clear provenance.
4. Attach evidence to notes where possible.
5. Create next capture actions with owners and dates.
6. Update commercials once a contractor engagement is real.

The workbench now uses controlled choice lists for the repetitive operator fields that were generating most validation noise:
- contact side
- contact source type
- confidence level
- intelligence note type
- evidence/intelligence source class
- capture action type
- capture action status
- commercial success fee type

The contractor handoff form on `/contractors/{id}` uses the same controlled pursuit-stage, confidence, and 1-5 score selections as the contract-detail bootstrap.

Standardized janitorial workbench vocabularies are now:
- contact side: `BUYER`, `CONTRACTOR`
- contact source type: `PUBLIC`, `DIRECT_CONVERSATION`, `REFERRAL`, `INFERRED`
- intelligence note type: `INTELLIGENCE`, `POSITIONING`, `COMPETITOR`, `STAKEHOLDER`, `RISK`, `PRICING`, `TRANSITION`
- capture action type: `RESEARCH`, `OUTREACH`, `MEETING`, `FOLLOW_UP`, `REVIEW`, `DELIVERABLE`
- capture action status: `OPEN`, `IN_PROGRESS`, `BLOCKED`, `COMPLETE`
- commercial success fee type: `FIXED`, `PERCENT_ANNUAL`, `PERCENT_TOTAL`

Loose operator input is normalized into those canonical values before persistence so reporting and filtering stay consistent.

The capture workbench also supports additive GET filters for faster operator review:
- contacts: `contact_side`, `contact_source_type`, `contact_confidence_level`
- intelligence: `note_type`, `note_source_class`, `note_confidence_level`
- evidence: `evidence_source_class`, `evidence_confidence_level`
- capture actions: `action_type`, `action_status`

The corresponding API list routes expose the same filter dimensions on:
- `GET /api/opportunities/{id}/contacts`
- `GET /api/opportunities/{id}/intelligence`
- `GET /api/opportunities/{id}/evidence`
- `GET /api/opportunities/{id}/capture-actions`

## Pursuit stages

Business-facing pursuit stages:
- `INTELLIGENCE`
- `EARLY_QUALIFICATION`
- `PRE_RFP_CAPTURE`
- `ACTIVE_RFP`
- `SUBMITTED`
- `AWARD`
- `LOST`
- `DORMANT`

Downstream proposal workflow is still tracked separately as `proposal_stage`. Once a pursuit reaches `ACTIVE_RFP`, the existing proposal modules become the operational system of record for RFP parsing, compliance, reviews, outline generation, and submission readiness.

## Ethical handling rules

This system is designed for lawful capture planning and public-source intelligence.

Use these evidence classes intentionally:
- `PUBLIC`: public records, board packets, solicitation portals, public meeting material, published contract data
- `INFERRED`: reasoned conclusions drawn from public facts or pattern analysis
- `DIRECT_CONVERSATION`: information you obtained directly in a lawful business conversation

Rules:
- Do not present inferred content as fact.
- Preserve provenance for every meaningful intelligence entry.
- Do not store or solicit confidential procurement information.
- Use the ethics guidance text in the capture workbench as the operating standard.

## Commercials

Commercial tracking is tied to the opportunity, not the generic client record.

Track:
- Advised contractor
- Retainer amount
- Success fee structure
- Projected payout date
- Projected payout amount
- Weighted expected value
- Realized revenue

`weighted_expected_value` is calculated from current opportunity probability plus the retainer and projected success fee.

## Dashboard usage

`/dashboard` summarizes:
- Upcoming rebids
- Hottest pursuits
- Top contractor matches
- Overdue and upcoming contractor follow-ups
- Live pursuit readiness by active opportunity
- Operator friction signals and recommendations
- Active proposal workload
- Weighted pipeline value
- Expected consulting revenue

Use it as the weekly operating review page.

Treat the live-pursuit readiness panel as the go/no-go screen before running this on a real engagement. A pursuit is considered ready when it has:
- at least one buyer contact
- at least one contractor contact
- at least one intelligence note
- at least one evidence record
- at least one non-complete capture action
- an advised contractor linked through commercials

If the panel still shows missing items, resolve those gaps in the capture workbench before treating the pursuit as pilot-ready.

## Privacy-safe workflow feedback

Boss Key now includes a privacy-safe adaptive feedback layer intended to help improve the operator workflow without turning the app into surveillance software.

Tracked structured signals include:
- page visits
- time on page
- repeated clicks
- repeated validation failures
- abandoned forms
- field edit churn counts
- repeated revisits
- navigation loops
- explicit manual-workaround feedback

Guardrails:
- no raw keystroke logging
- no passive microphone capture
- no replay-style session surveillance
- no proposal text is stored unless you deliberately type it into the feedback note

Use the shared `Share workflow friction` panel when:
- a step is confusing
- a step took too long
- you had to do part of the work manually outside the intended flow

Use `/ux/friction` or the dashboard friction panel to review:
- which pages are generating the most friction
- which deterministic rules have fired
- which recommendations are being proposed for approval

Recommendations are advisory only. They should be reviewed before changing the core workflow.

## Verification

Serial verification commands:

```bash
python -m pytest -q
npm test
```

The current SQLite-backed test harness is serial-only. Do not run the Python suite in parallel.

## Roadmap notes

Current version is internal-first. The next logical extensions are:
- automated ingestion from `marketing-agents`
- stronger pursuit analytics and conversion reporting
- richer relationship mapping
- client-facing tenancy and permissions
- external enrichment connectors
