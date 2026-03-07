# Boss Key Pursuit OS - System Architecture

## Runtime
- FastAPI application process
- SQLite database (local file)
- Server-rendered HTML templates + API routes

## Layers
1. Web layer (`app/main.py`, module routers)
2. Module layer (`app/modules/*`)
3. Core layer (`app/core/*`)
4. Knowledge layer (`app/knowledge/*`)

## Module boundaries
- `janitorial_os`: market radar, contract records, contractor profiles, matching, capture workbench, dashboard, and commercials
- `opportunity_intake`: intake scoring, persistence, capture plan bootstrap
- `rfp_parser`: document extraction and structured RFP model (planned)
- `compliance_matrix`: requirement-to-section matrix orchestration (planned)
- `capture_plan`: enriched pursuit strategy artifacts (planned)
- `proposal_outline`: response structure generation (planned)
- `review_manager`: Pink/Red/Gold review workflow (planned)
- `submission_checklist`: final readiness validation (planned)

## Human control points
- Bid/no-bid approval
- Win theme acceptance
- Pricing strategy approval
- Final messaging approval
- Executive submission authorization

## Persistence strategy
- SQLAlchemy ORM models
- Alembic migrations in `migrations/versions`
- Startup preflight validates schema state and fails fast on unstamped DBs
- Janitorial pursuit fields extend `opportunities` and keep the downstream proposal workflow as a separate `proposal_stage`
