# Janitorial Contract Capture OS v1

## Summary
- Implementation target is `proposal-ops` only. Reuse the current FastAPI + SQLAlchemy/Alembic + Jinja stack and existing proposal modules.
- Preserve the current proposal workflow engine as the downstream `proposal_stage` system and add a business-facing `pursuit_stage`.
- Add janitorial-specific market data, pursuit intelligence, contractor matching, commercials, and dashboard/reporting in phased slices.
- Use SQLite for MVP, but keep schema and services structured for future tenant-aware expansion.

## Public Interfaces and Data Model
- Extend opportunities with janitorial pursuit fields: `pursuit_stage`, `proposal_stage`, `buying_organization_id`, `primary_contract_id`, `primary_facility_id`, `confidence_level`, `expected_rfp_date`, provenance summary fields, and score snapshot fields.
- Add dedicated modules and routes for organizations, facilities, contracts, contractors, matches, intelligence, capture actions, commercials, and dashboard summary.
- Keep existing proposal endpoints under `/api/opportunities/{id}/...` and treat them as active once a pursuit reaches `ACTIVE_RFP`.

## Phases
### Phase 1: Market Base and Contract Radar
- Added:
  - Market data module with `organizations`, `facilities`, `contract_records`, and `contract_facilities`.
  - CRUD APIs and web pages for list/detail/create/edit flows.
  - CSV import for MVP contract radar records.
  - Seed/sample janitorial data and contract radar dashboard hooks.
- Remaining:
  - Contractor matching, intelligence/evidence, commercials, and expanded reporting.
  - Full proposal-stage handoff automation and client-facing hardening.
- Verify:
  - Run Alembic upgrade to head.
  - Run serial pytest suites for market data APIs/UI and existing opportunity workflows.
  - Open the web UI and confirm organization, facility, contract, and import flows work end-to-end.

### Phase 2: Pursuits and Configurable Opportunity Scoring
- Added:
  - Pursuit-centric extensions on opportunities.
  - Configurable scoring profile tables and services.
  - Create-pursuit-from-contract flow.
- Remaining:
  - Broader score tuning UX and richer forecast analytics.
- Verify:
  - Unit tests for scoring.
  - API/UI tests for contract-to-pursuit creation and scoring settings persistence.

### Phase 3: Contractors and Bidder Matching
- Added:
  - Contractor records, fit profiles, match snapshots, and ranking logic.
- Remaining:
  - Broader import/enrichment flows.
- Verify:
  - Ranking unit tests and contractor CRUD/match API/UI tests.

### Phase 4: Capture Actions, Contacts, Intelligence, and Ethical Evidence
- Added:
  - Contacts, capture actions, intelligence notes, and evidence records with provenance and ethics controls.
- Remaining:
  - Deeper relationship-mapping analytics.
- Verify:
  - Provenance validation tests and UI tests for ethical-use messaging.

### Phase 5: Active Proposal Workflow Integration
- Added:
  - Pursuit-stage to proposal-stage synchronization and proposal workflow summary.
- Remaining:
  - Additional automation around pricing and assignments.
- Verify:
  - Stage-sync and regression tests across proposal modules.

### Phase 6: Dashboard and Reporting
- Added:
  - Operator dashboard with rebids, hottest pursuits, active proposals, weighted pipeline, and expected consulting revenue.
- Remaining:
  - More advanced cohort and historical reporting.
- Verify:
  - Dashboard API/UI tests and CSV export checks.

### Phase 7: Commercials, Operator Docs, and Final Hardening
- Added:
  - Commercial engagement tracking, README updates, and the operator guide at `docs/runbooks/janitorial-capture-os-operator-guide.md`.
  - Full serial verification across Python and Node suites.
- Remaining:
  - Future automation from `marketing-agents` and stronger multi-tenant isolation.
- Verify:
  - Commercial math tests, `python -m pytest -q`, `npm test`, and operator-doc review.

## Test Plan
- Unit: scoring normalization, contractor-fit ranking, commercial EV math, provenance validation, CSV parsing, stage mapping, and dashboard aggregation.
- Integration/API: CRUD for new entities, import flows, contract-to-pursuit creation, matching, intelligence/evidence linking, commercials, and dashboard export.
- UI: list/detail/create/edit/import flows, dashboard, capture workspace, contractor matching, proposal handoff, and ethical-use messaging.
- Regression: existing proposal workflow, gate engine, review manager, submission checklist, and current `/api/opportunities/*` compatibility.

## Assumptions and Defaults
- Internal-first, local-first MVP.
- Phase 1 uses manual entry plus a CSV importer; automated ingestion from `marketing-agents` is deferred.
- Existing dirty changes remain untouched unless directly required for this implementation.
- Python verification runs serially because the current SQLite-backed test harness is not parallel-safe.
