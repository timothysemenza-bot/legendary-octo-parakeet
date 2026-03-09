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

### Automated Chris Demo (Playwright)

Run from the repo root:

```bash
npm run pw:bosskey:demo
```

Optional headed run for a visible browser:

```bash
npm run pw:bosskey:demo -- --headed
```

Create a narrated partner-facing MP4 from the same deterministic demo flow:

```bash
npm run pw:bosskey:demo:narrated
```

Generate the full narrated knowledge-base library:

```bash
npm run pw:bosskey:kb:narrated
```

What the harness does:
- starts Boss Key on `http://127.0.0.1:8010`
- resets a dedicated demo database under `proposal-ops/.artifacts/playwright-demo/`
- seeds deterministic janitorial demo data
- walks the overview film plus focused knowledge-base videos for contractor workflow, capture workbench, and dashboard operations
- records Playwright artifacts including video, trace, and named screenshots
- renders a scripted voiceover with OpenAI text-to-speech when `OPENAI_API_KEY` is available, or falls back to Windows speech synthesis
- refuses to squeeze narration into scenes that are too short, so pacing errors surface as authoring errors instead of producing unintelligible audio

Artifacts are written to:
- `proposal-ops/test-results/`
- `proposal-ops/playwright-report/`
- `proposal-ops/demo-artifacts/01-bosskey-overview.mp4`
- `proposal-ops/demo-artifacts/02-bosskey-contractor-workflow.mp4`
- `proposal-ops/demo-artifacts/03-bosskey-capture-workbench.mp4`
- `proposal-ops/demo-artifacts/04-bosskey-dashboard-operations.mp4`

The demo harness does not use your live working SQLite file.
The narration is scripted by walkthrough step and synchronized to the recorded Playwright video after the run; it is not live microphone capture.
If you want the higher-quality external voice, set `OPENAI_API_KEY` in the environment or a local `.env` file at the repo root before running the narrated commands.

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
