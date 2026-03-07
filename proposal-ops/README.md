# ProposalOps Monorepo

Artifact-first scaffold for a multi-tenant, human-gated proposal operations platform.

## Quick Start

```bash
cd proposal-ops
npm test
```

## Boss Key Pursuit OS (FastAPI v1)

```bash
cd proposal-ops
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

Open:
- `http://127.0.0.1:8000/` for the web UI
- `http://127.0.0.1:8000/docs` for API docs

## Janitorial Contract Capture OS v1

`proposal-ops` now includes an internal-first Janitorial Contract Capture OS for pre-RFP market intelligence, pursuit scoring, contractor matching, capture workbench operations, and consulting economics tracking.

Primary web routes:
- `/dashboard`
- `/organizations`
- `/facilities`
- `/contracts`
- `/contractors`
- `/settings/scoring`
- `/opportunities/{id}/capture-workbench`

Primary API routes:
- `GET|POST /api/organizations`
- `GET|POST /api/facilities`
- `GET|POST /api/contracts`
- `POST /api/contracts/import`
- `POST /api/contracts/{id}/pursuits`
- `GET|POST /api/contractors`
- `POST /api/opportunities/{id}/matches`
- `GET|POST /api/opportunities/{id}/contacts`
- `GET|POST /api/opportunities/{id}/intelligence`
- `GET|POST /api/opportunities/{id}/evidence`
- `GET|POST /api/opportunities/{id}/capture-actions`
- `GET|PUT /api/opportunities/{id}/commercials`
- `GET /api/dashboard/summary`
- `POST /api/dashboard/seed-demo`

MVP contract import CSV columns:
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

Operator guidance:
- [Janitorial Capture OS Operator Guide](./docs/runbooks/janitorial-capture-os-operator-guide.md)
- [Execution plan](./PLANS.md)

### Migration mismatch fix
If you see `table opportunities already exists`, your DB has tables but is not Alembic-stamped.

Preserve data:
```bash
python -m alembic stamp head
```

Reset local DB:
```bash
powershell -ExecutionPolicy Bypass -File .\tools\reset-local-db.ps1
```

## Phase B Endpoints
- `POST /api/opportunities/{id}/rfp/parse`
- `GET /api/opportunities/{id}/compliance-matrix`
- `PATCH /api/compliance-matrix/{row_id}`

## Phase B Web Screens
- `/opportunities/{id}/rfp-upload`
- `/opportunities/{id}/compliance-matrix`

## Current Scope

- Product and architecture docs
- Domain model and workflow definitions
- Client config JSON schema
- Demo tenant fixture config
- Contract tests for gate transitions and tenant isolation
- Opportunity Intake Engine (FastAPI + SQLite + UI + scoring + audit trail)
- RFP Parser + Compliance Matrix (heuristic extraction, matrix generation, manual row updates)
- Janitorial market radar: organizations, facilities, contracts, and CSV import
- Pursuit scoring with configurable profiles and contract-to-pursuit creation
- Contractor matching, capture workbench, ethical evidence tracking, dashboard reporting, and commercials
