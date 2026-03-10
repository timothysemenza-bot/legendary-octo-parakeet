# Boss Key Pursuit OS - System Architecture

## Strategic Role

`proposal-ops` is the internal operating system for Boss Key's early-lifecycle advisory model:

```text
Policy Intelligence
-> Opportunity Forecasting
-> Capture Strategy
-> Proposal Execution
```

The current software implementation is strongest from opportunity forecasting through capture strategy, with janitorial / facilities as the first vertical wedge.

## Lifecycle Mapping

| Stage | Current state | Primary support |
| --- | --- | --- |
| Policy intelligence | target-state in docs, manual-heavy in delivery today | future source and signal models |
| Opportunity forecasting | implemented | `janitorial_os` market radar, dashboard, contract records |
| Capture strategy | implemented | contractors, touchpoints, opportunity handoff, capture workbench, commercials |
| Proposal execution | partially implemented | `opportunity_intake`, compliance and downstream proposal modules |

## Runtime

- FastAPI application process
- SQLite database for local/internal use
- Server-rendered HTML templates plus API routes
- Playwright harness for deterministic demos and operator knowledge-base videos

## Layers

1. Web layer
   - `app/main.py`
   - module routers
   - Jinja templates

2. Module layer
   - `app/modules/janitorial_os`
   - `app/modules/opportunity_intake`
   - downstream proposal modules

3. Core layer
   - configuration
   - database/session handling
   - startup checks
   - shared runtime concerns

4. Knowledge / artifact layer
   - docs
   - runbooks
   - demo assets
   - reusable delivery templates

## Module Boundaries

### `janitorial_os`
- Current vertical wedge
- Market radar, contract records, contractor prospecting, touchpoints, capture workbench, dashboard, commercials, and operator feedback loops

### `opportunity_intake`
- Intake scoring
- qualification records
- initial capture recommendation scaffold

### `rfp_parser`
- Planned downstream solicitation extraction

### `compliance_matrix`
- Planned requirement-to-section mapping

### `capture_plan`
- Planned structured pursuit strategy artifacts

### `proposal_outline`
- Planned response-structure generation

### `review_manager`
- Planned Pink/Red/Gold review workflow

### `submission_checklist`
- Planned final submission readiness validation

## Human Control Points

- opportunity qualification and bid/no-bid approval
- forecast acceptance or rejection
- contractor selection and commercial assumptions
- win-theme and positioning approval
- pricing strategy approval
- final proposal messaging approval
- executive submission authorization

## Persistence Strategy

- SQLAlchemy ORM models
- Alembic migrations in `migrations/versions`
- startup preflight validates schema state and fails fast on drift
- additive schema evolution favored over destructive refactors

## Architectural Defaults

- Internal-first, local-first
- Human-gated decisions over autonomous workflow changes
- Structured metadata over raw surveillance-style capture
- Exportable artifacts over platform lock-in
- Vertical wedges layered on reusable foundations
