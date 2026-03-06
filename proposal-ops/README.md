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
