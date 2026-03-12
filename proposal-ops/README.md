# ProposalOps Monorepo

Internal-first operating system for Boss Key's early-lifecycle government opportunity intelligence and capture advisory practice.

## What This Repo Is

Boss Key's firm model is:

```text
Policy Intelligence
-> Opportunity Forecasting
-> Capture Strategy
-> Proposal Execution
```

`proposal-ops` is where that model is codified operationally.

Current truth:
- The repo is **not** a SaaS product.
- The repo is **not** a lobbying platform.
- The repo is an internal consulting toolkit for running research, capture, proposal, and reusable client-deliverable workflows.
- The first implementation wedge is **janitorial / facilities services** inside Mid-Atlantic state and local markets.

## Lifecycle Mapping

### 1. Policy / Procurement Intelligence
- Monitor budgets, agendas, legislation, regulatory movement, rebid timing, and procurement-adjacent signals.
- Current state: implemented as an additive opportunity-intelligence workspace for signal sources, signal events, and opportunity hypotheses.

### 2. Opportunity Forecasting
- Turn signals into likely buying events, target accounts, confidence framing, and timing hypotheses.
- Current state: implemented in the Janitorial Contract Capture OS through organizations, facilities, contract radar, dashboard views, and forecast-oriented workflow support.

### 3. Capture Strategy
- Build stakeholder maps, contractor strategy, intelligence notes, capture actions, commercials, and pre-RFP pursuit discipline.
- Current state: implemented in the janitorial operating wedge through contractor prospecting, touchpoints, capture workbench, opportunity handoff, and dashboard readiness views.

### 4. Proposal Execution
- Carry qualified pursuits into formal solicitation handling, compliance framing, content planning, review, and submission support.
- Current state: partially implemented through opportunity intake, downstream proposal workflow scaffolding, compliance-matrix work, and proposal-oriented module plans.

## Foundational Docs

- [Early-Lifecycle Operating Model](./docs/early-lifecycle-operating-model.md)
- [System Architecture](./docs/system-architecture.md)
- [Development Roadmap](./docs/development-roadmap.md)
- [Proposal Workflow](./docs/proposal-workflow.md)
- [Janitorial Capture OS Operator Guide](./docs/runbooks/janitorial-capture-os-operator-guide.md)
- [Execution Plan](./PLANS.md)

## Quick Start

```bash
cd proposal-ops
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

Open:
- `http://127.0.0.1:8000/` for the web UI
- `http://127.0.0.1:8000/docs` for API docs

## Boss Key Pursuit OS (FastAPI v1)

The current production-quality wedge inside this repo is the **Janitorial Contract Capture OS**.

It supports:
- upstream opportunity-intelligence tracking
- organization-backed buying-organization normalization across intelligence and intake flows
- hypothesis-to-pursuit conversion into the live opportunity workflow, with saved or override advised-contractor seeding
- contract radar and rebid visibility
- organizations and facilities
- contractor prospecting and touchpoints
- active/archive lifecycle for contractors and opportunities
- pursuit scoring and contract-to-pursuit handoff
- capture workbench operations
- commercials and advised contractor linkage
- operator dashboard and readiness visibility
- UX friction feedback capture
- approval-based friction recommendation checkpoints

Primary web routes:
- `/dashboard`
- `/intelligence`
- `/opportunities`
- `/organizations`
- `/facilities`
- `/contracts`
- `/contractors`
- `/settings/scoring`
- `/opportunities/{id}/capture-workbench`
- `/ux/friction`

Primary API routes:
- `GET|POST /api/intelligence/sources`
- `GET|POST /api/intelligence/signals`
- `GET|POST /api/intelligence/hypotheses`
- `POST /api/intelligence/hypotheses/{id}/convert-to-pursuit`
- `GET /api/intelligence/summary`
- `GET|POST /api/organizations`
- `GET|POST /api/facilities`
- `GET|POST /api/contracts`
- `POST /api/contracts/import`
- `POST /api/contracts/{id}/pursuits`
- `GET|POST /api/contractors`
- `POST /api/contractors/{contractor_id}/archive`
- `POST /api/contractors/{contractor_id}/restore`
- `GET|POST /api/contractors/{contractor_id}/touchpoints`
- `POST /api/contractors/{contractor_id}/pursuits`
- `POST /api/contractors/{contractor_id}/opportunity-links`
- `GET /api/opportunities`
- `POST /api/opportunities/{id}/archive`
- `POST /api/opportunities/{id}/restore`
- `GET|POST /api/opportunities/{id}/contacts`
- `GET|POST /api/opportunities/{id}/intelligence`
- `GET|POST /api/opportunities/{id}/evidence`
- `GET|POST /api/opportunities/{id}/capture-actions`
- `GET|PUT /api/opportunities/{id}/commercials`
- `GET /api/dashboard/summary`
- `POST /api/dashboard/seed-demo`
- `POST /api/ux/events`
- `POST /api/ux/feedback`
- `GET /api/ux/friction-summary`
- `GET|POST /api/ux/recommendation-checkpoints`
- `POST /api/ux/recommendation-checkpoints/{id}/status`

### MVP contract import CSV columns

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

## Automated Demo and Knowledge Base

Run from the repo root:

```bash
npm run pw:bosskey:demo
```

Narrated partner demo:

```bash
npm run pw:bosskey:demo:narrated
```

Narrated knowledge-base library:

```bash
npm run pw:bosskey:kb:narrated
```

What the harness does:
- starts Boss Key on `http://127.0.0.1:8010`
- resets a dedicated demo database under `proposal-ops/.artifacts/playwright-demo/`
- seeds deterministic janitorial demo data
- records high-resolution walkthrough videos, traces, and screenshots
- renders scripted narration with OpenAI text-to-speech when `OPENAI_API_KEY` is available, or falls back to Windows speech synthesis

Artifacts are written to:
- `proposal-ops/test-results/`
- `proposal-ops/playwright-report/`
- `proposal-ops/demo-artifacts/`

## Migration mismatch fix

If you see `table opportunities already exists`, your DB has tables but is not Alembic-stamped.

Preserve data:

```bash
python -m alembic stamp head
```

Reset local DB:

```bash
powershell -ExecutionPolicy Bypass -File .\tools\reset-local-db.ps1
```

## Working Assumptions

- Internal-first, local-first, human-gated operation
- Janitorial / facilities is the first vertical wedge, not the only end state
- Structured signal interpretation is preferred over black-box automation
- Client deliverables should remain exportable and editable
- The internal repo remains the master system for reusable methodology and workflow

## Locked Follow-On

The next data-model expansion after this pilot-hardening release is intentionally deferred:
- manual logo upload for organizations and contractors through a reusable `brand_assets` pattern
- structured contractor service areas, state/territory coverage, and normalized vertical taxonomy
- contractor office records for headquarters and regional offices
- lightweight map views driven by stored office/service-area data rather than live scraping or geocoding
