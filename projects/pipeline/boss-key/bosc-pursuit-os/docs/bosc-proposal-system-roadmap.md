# BOSC Proposal System Roadmap

## Phase 0: First Vertical Slice

Goal: prove the operating-system shape with a narrow, inspectable workflow.

Deliver:

- local structured opportunity input
- rules-based qualification
- rules-based solution assembly
- proof/example binding from a small curated library
- buyer-facing web experience
- export-friendly summary view
- core engine tests

Operator controls in this phase should stay lightweight and local: approvals, review checkpoints with exit criteria, assumptions, scenario saves, readiness metadata, module overrides, and an operator-first idea engine are present, but they do not yet require multi-user collaboration or backend storage.

The current slice now also includes bundle packaging for promoted concept sheets, with a dated `outputs/deliverables/` folder, source snapshot files, a standalone HTML handoff, and a PDF fallback.

## Phase 1: Intake Expansion

Goal: move from hand-entered data toward assisted opportunity ingestion.

Add:

- PDF, email, note, and transcript parsing adapters
- normalization into the `Opportunity` schema
- field confidence markers and missing-data prompts
- operator review queue for low-confidence extractions

Keep APMP control discipline visible here: gate approvals should still be separate from review checkpoints, even as intake confidence and source traceability improve.

## Phase 2: Operator Workbench

Goal: make the system useful for a solo consultant running real pursuits.

Add:

- editable assumptions ledger
- module override controls
- operator idea engine surfaces for hot-button modeling, janitorial win themes, objection handling, competitor ghosting, proof matches, and executive-summary variants
- working-story curation that turns the current idea pack into a pinned strategy brief for the live bid
- multiple named buyer story variants with concept-sheet promotion and export
- deliverable packaging from promoted concept sheets into source/export handoff bundles
- approval checkpoints for qualification, solution, and final experience
- explicit review checkpoints for content plan/Pink, evaluator-style/Red, and Gold readiness with exit criteria
- owned open actions with real due dates and blocker visibility
- decision versioning and scenario comparison with rationale capture and readiness snapshots
- unresolved action tracking tied to the next gate and a real review calendar

## Phase 3: Proof And Narrative Depth

Goal: increase differentiation and traceability.

Add:

- reusable proof library with hot-button metadata, metrics, and source traceability
- stronger idea generation prompts or adapters behind the existing service interface
- stronger narrative generation prompts or adapters behind the existing service interface
- section-level generation and approval controls
- export packages tuned for specific buyer expectations
- packaging flows that can consume live browser-exported workspace state, not just structured seed files

Prefer proof, idea, and narrative outputs that point back to the active decision basis, not just to the final marketing copy.

## Phase 4: Hosted Install Readiness

Goal: support a consulting or system-install model.

Add:

- persistent storage for pursuits, modules, proof, and approvals
- multi-user roles for operator, reviewer, and client
- hosted delivery for buyer-facing proposal experiences
- audit trails and printable package exports

At this phase, the local persistence model should become shared persistence with version history, approval timestamps, and scenario lineage.

## Phase 5: Consulting Productization

Goal: turn the prototype into a repeatable service install for clients.

Add:

- configurable scoring rules by client profile
- industry presets for janitorial, facilities, and related field services
- onboarding templates, proof packs, and implementation playbooks
- deployment and adoption guidance for local-first or hosted workflows

## Design Guardrails

- keep the web experience primary
- make the buyer-facing experience fast to scan first, then deeper on demand
- do not collapse the system into a long-form document generator
- preserve traceability and export fallback
- prefer modular rules and services over hidden prompt logic
- keep gate approvals separate from review checkpoints and issue-log follow-up
- keep the operator mental model simple even as the engines deepen
