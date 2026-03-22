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

## Phase-1 Direct Intake

For direct federal consulting, proposal-support, and digital-service opportunities, the near-term intake surface is [`../projects/pipeline/federal-bid-cockpit/index.html`](../projects/pipeline/federal-bid-cockpit/index.html). Use that cockpit first for SAM.gov search, gate checks, and bid/no-bid scoring while `proposal-ops` remains the longer-term operating system. Keep NJSTART active as a secondary lane rather than the default lane.

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

## DEMO_RUNBOOK

The fastest demo entrypoint is the client-safe Proposal Builder workflow.

Local startup:

```bash
cd proposal-ops
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

Recommended `.env` settings for live demos:

```env
OPENAI_API_KEY=...
BOSSKEY_OPENAI_MODEL=gpt-5.4
BOSSKEY_OPENAI_TIMEOUT_SECONDS=120
BOSSKEY_OPENAI_EXTRACT_TIMEOUT_SECONDS=120
BOSSKEY_OPENAI_SKELETON_TIMEOUT_SECONDS=180
BOSSKEY_OPENAI_DRAFT_TIMEOUT_SECONDS=300
```

Restart Uvicorn after changing `.env` so the running app picks up the new values.

Open:

- `http://127.0.0.1:8000/proposal-builder`

One-command shortcut on Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\start-proposal-builder-demo.ps1
```

Demo click path:

1. Open `/proposal-builder`
2. Click `Launch Demo Sample` for the cleanest screen-share path, or upload a live PDF / paste text
3. On the workspace, start with the `Opportunity Summary`, `Document Gaps`, `Assumption Flags`, `Evaluation Criteria`, and `Compliance Matrix`
4. Click `Start Full Package Run`
5. Let the background run progress through extraction, compliance mapping, customer strategy, content plan, full draft, and pricing
6. When the dashboard pauses at pricing, click `Approve Pricing and Continue`
7. Show the forms/attachments stage and the pink/red/gold review stages as they complete
8. When the dashboard pauses at final export, click `Approve Final Export`
9. Download the `Final Proposal DOCX`, `Pricing Workbook`, `Forms Bundle`, and `Support Bundle`
10. Use the lower manual buttons only as a fallback or detail view if you want to show an individual stage outside the full package run

Fallbacks if a stage fails:

- If a live upload is messy, go back to `/proposal-builder` and use the checked-in demo sample
- The workspace shows both `generation_mode` and `generation_reason`, so you can explain exactly why a run is live, sample-cached, or failed
- Live model stages no longer downgrade into deterministic drafts when they time out; they stop, record the failure reason, and let you rerun with a longer timeout
- The full package engine is live-only for AI stages. If customer strategy, content plan, full draft, or review stages fail, the dashboard will block explicitly instead of inventing content
- If DOCX export fails, use the Markdown draft and ZIP bundle from `.artifacts/exports/`
- If the inference step cannot name the opportunity or client, confirm those two fields on the built-in mini-confirm screen and continue

## CLIENT_DEPLOYMENT_NOTES

This Proposal Builder and full package engine are designed to be sold as a client-owned deployment rather than a SaaS platform.

Recommended framing:

- Delivery model: one-time implementation and configuration, then a light O&M retainer for parser tuning, prompt updates, APMP rubric tuning, approved-content maintenance, pricing/form mapping updates, and support
- Runtime: FastAPI web app on a Windows-friendly host or VM
- Storage: local or shared file storage for source documents and export bundles
- Database: SQLite for pilot and light deployment; optional Postgres later if the client wants multi-user scale
- Model access: client-owned `OPENAI_API_KEY`, outbound HTTPS access to OpenAI, and a configurable default model of `gpt-5.4`
- Security boundary: the proposal team uses a normal browser workflow with background package runs, approval gates, and downloads; no prompt-writing, terminal use, or developer tooling is exposed

High-level IT dependencies:

- Outbound HTTPS access to `api.openai.com`
- File upload allowance for PDF, DOCX, TXT, and Markdown
- Permission to persist uploaded source documents and generated export bundles
- Optional shared-drive or SharePoint handoff for Word finishing

What the system owns versus what Microsoft Copilot can complement:

- This system owns staged orchestration, requirement extraction, compliance mapping, APMP-derived review logic, proposal skeleton creation, reusable approved-content insertion, deterministic pricing, forms-and-attachments packaging, and export packaging
- Microsoft Copilot can still help proposal staff refine tone or polish the last 10 percent inside Word
- Copilot does not replace the structured intake, grounded compliance traceability, staged artifact reuse, or export workflow this build provides

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
