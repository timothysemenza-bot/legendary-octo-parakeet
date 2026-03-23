# Boss Key Pursuit OS

Boss Key Pursuit OS is an AI-native prototype for janitorial and facilities bids. It treats the proposal as a structured decision environment: qualify the opportunity, assemble a solution, generate operator-first strategy ideas, manage approvals and review checkpoints, bind proof, and render a buyer-facing web experience with an export-friendly fallback. The default seed now uses a live public-sector LASD Region 4 custodial-services pilot, while the earlier Ridgeview commercial scenario remains preserved as a fixture.

## Why This Lives Here

This project was placed at `projects/pipeline/boss-key/bosc-pursuit-os/` because it is an incubating Boss Key system, not a public website surface and not a change to the flagship `proposal-ops/` product. That keeps the work self-contained, demoable, and safe to evolve without disrupting other roots.

## Architecture

- Frontend: Vite + React + TypeScript
- Domain model: explicit schemas and types for `Opportunity`, `QualificationResult`, `SolutionModule`, and `ProposalExperience`
- Business logic: rules-based qualification and solution assembly engines in `src/engine/`
- Strategy and narrative layers: interface-based idea and narrative services so mocked or real AI generation can be swapped later without touching core logic
- Operator layer: APMP-shaped approvals, Pink/Red/Gold-style review checkpoints with exit criteria, assumptions ledger, owned open actions with due labels and close conditions, scenario save/load, local persistence, and a curated working-story mode for live bid strategy briefs
- Rendering: a segmented pursuit desk for operator work plus separate buyer-facing and export modes
- Buyer experience format: a 90-second brief and fast-scanning decision feed for modern decision-makers, with a deeper section view behind it
- Variant workflow: named buyer story variants can be saved, compared, promoted, and exported as concept sheets
- Import layer: browser-side JSON intake plus an optional Node import server for model-backed source-file extraction

See [boss-key-v1-product-spec.md](docs/boss-key-v1-product-spec.md), [bosc-proposal-system-architecture.md](docs/bosc-proposal-system-architecture.md), and [bosc-proposal-system-roadmap.md](docs/bosc-proposal-system-roadmap.md) for the working product spec, decision record, and roadmap.

## Project Layout

- `docs/`: architecture and roadmap
- `inputs/`: local structured opportunity and workspace-state files, including a promoted demo concept
- `server/`: optional Node import server for model-backed source-file intake
- `scripts/`: local packaging utilities for deliverable handoff bundles
- `src/domain/`: typed business models and schemas
- `src/engine/`: qualification, solution, and experience composition logic
- `src/deliverables/`: packaging helpers for shareable concept-sheet exports
- `src/services/`: AI-safe service boundaries and narrative adapters
- `src/ui/`: presentational components
- `tests/`: focused non-UI tests
- `working/`: local notes or thread-specific material

## Local Run

From [package.json](C:\Users\timot\Documents\Proposal-Microsite\projects\pipeline\boss-key\bosc-pursuit-os\package.json):

```bash
npm install
npm run dev
```

Open the local Vite URL shown in the terminal. The app starts with the live-pilot LASD Region 4 opportunity from `inputs/demo-opportunity.json`, and you can now import either a local opportunity JSON, a saved workspace-state JSON, or one or more local `PDF` / `TXT` / `MD` RFP files directly from the workbench. When the optional import server is not running, source-file conversion stays local and heuristic-only. The earlier Ridgeview commercial fixture is still available at `inputs/ridgeview-demo-opportunity.json`, and a smaller public-sector contrast case is available at `inputs/east-bay-library-opportunity.json`.

The default desk landing view is `Idea Engine -> Curate Story`, which lets you pin the opening, choose the strongest themes and proof, and turn the current pursuit state into a compact working strategy memo.

To run the optional model-backed import lane:

```bash
copy .env.example .env.local
# add OPENAI_API_KEY to .env.local
npm run dev:full
```

That starts the Vite client on `http://localhost:4173` and the Boss Key import server on `http://localhost:4174`. The client proxies `/api/*` requests to the import server in development. If the import server is down or not configured, the workbench falls back to the local heuristic importer automatically.

## Deliverable Packaging

To package the promoted concept sheet into a dated handoff bundle under `outputs/deliverables/`:

```bash
npm run package:concept-sheet
```

That command uses `inputs/demo-workspace-state.json` by default for the LASD Region 4 pilot and creates:

- `source/workspace-state.json`
- `source/opportunity.json`
- `source/package-payload.json`
- `source/working-story-brief.md`
- `export/<slug>.html`
- `export/<slug>.pdf`

You can point the packager at a different saved workspace-state file:

```bash
npm run package:concept-sheet -- --state path/to/workspace-state.json --slug buyer-concept-sheet
```

You can still package the preserved Ridgeview commercial fixture with:

```bash
npm run package:concept-sheet -- --state inputs/ridgeview-demo-workspace-state.json --slug ridgeview-property-group-concept-sheet
```

## Verification

```bash
npm run test
npm run typecheck
npm run build
npm run package:concept-sheet
```

## Current Slice

The current slice includes:

- structured opportunity intake from a seed JSON file, workspace-state JSON, local `PDF` / `TXT` / `MD` RFP source files, or a simple form
- optional model-backed source-file intake through `/api/import-opportunity`, with automatic fallback to the local heuristic importer when the server is unavailable
- rules-based qualification with risk flags and pursue/review/no-bid output
- rules-based solution assembly from predefined janitorial and facilities modules
- an operator-first idea engine that generates strategy memo, buyer hot buttons, janitorial-specific win themes, objection counters, competitor ghosting angles, transition plays, proof matches, executive-summary variants, and validation questions
- a working-story curation mode inside the idea engine that pins one opening, curates themes/proof/contrast choices, and assembles a compact live-bid strategy brief
- named buyer story variants that can be saved, compared, promoted into the buyer view, and exported as a concept sheet
- dated deliverable bundle packaging with a source snapshot, standalone HTML concept sheet, and PDF fallback handoff
- operator workbench controls for gate approvals, review checkpoints, assumptions, module overrides, owned actions, scenario saves, and local persistence
- local persistence for the active pursuit draft and saved scenarios
- a pursuit desk split into focused views for idea generation and story curation, opportunity intake, solution design, decision workflow, and scenario comparison
- a single next-checkpoint panel that shows the most important step, blockers, owner actions, and advance criteria
- review checkpoints with APMP aliases and exit criteria for content-plan, evaluator-style, and Gold-readiness flow
- saved scenarios that preserve rationale plus gate/review readiness metadata for comparison
- a buyer-facing mode that now defaults to a fast-scanning decision feed and 90-second brief, with deep-dive sections still available
- an export mode that can print either the promoted concept sheet or the fallback summary view

## Roadmap

- deepen intake from files, notes, transcripts, addenda, and email summaries beyond the current local JSON and `PDF` / `TXT` / `MD` import path
- add a review screen that shows extracted evidence, assumptions, and field-level confidence before creating a new pursuit draft
- expand qualification logic with configurable scoring and explicit gate approvals
- deepen the idea engine with stronger proof traceability, operator-tunable output styles, and model-backed strategy generation behind the existing service seam
- deepen review checkpoints with richer agendas, exit criteria, and operator-ready issue-log packaging
- add owned open actions with real due dates and blocker visibility for each gate and review checkpoint
- add proof binding from a reusable proof library
- add assumption ownership, unresolved-action tracking, and stronger scenario comparison/readiness views
- add packaging support for browser-exported live workspace state instead of only structured state files
- add hosted storage, collaboration, and authenticated client-facing delivery
