# BOSC Proposal System Architecture

## Status

Accepted for the first prototype slice on March 22, 2026.

## Context

Boss Key needs a modern pursuit and proposal operating system for private-sector service bids, especially janitorial and facilities services. The system should not behave like a Word-first proposal generator. It should ingest an opportunity, structure the pursuit, assemble a solution, generate strong operator-first strategy ideas, generate buyer-facing content, and render the output as a navigable web experience with a printable fallback.

APMP guidance in the local repository makes one distinction especially important for this project: gate approvals and review checkpoints are not the same thing. Gate approvals decide whether the pursuit should advance. Review checkpoints validate whether the current controlled draft is ready for the next quality pass, with the current operator slice framing those checkpoints as content-plan/Pink, evaluator-style/Red, and Gold-readiness reviews with explicit exit criteria.

The repository already has clear product lanes:

- `proposal-ops/` is the flagship product and already carries broad product complexity.
- `boss-key-website/` is the public-facing marketing and microsite surface.
- `projects/` is the safe place for incubating, client, internal, and pipeline work that should not disturb the main products.

## Decision

Create the project at `projects/pipeline/boss-key/bosc-pursuit-os/` as a self-contained TypeScript web prototype.

Use:

- Vite for a low-friction local developer and demo workflow
- React for component-driven UI composition
- TypeScript for explicit schemas, types, and maintainability
- Zod for runtime-safe parsing of local JSON opportunity inputs
- Rules-based engines for qualification and solution assembly in the first slice
- Operator controls for approvals, assumptions, scenario comparison, and local persistence in the second slice
- An operator-first idea engine that turns the current pursuit state into strategy, theme, proof, and narrative options
- A deliverable-packaging layer that turns a promoted concept into a dated bundle with source and export separation

## Why This Location

- It is incubating product work, so `projects/pipeline/` is the correct lane.
- It should not disturb the public Boss Key website.
- It should not assume adoption into `proposal-ops/` until the operating model is proven.
- A dedicated project root makes local demoing, docs, tests, and future hosting decisions easier.

## Architectural Principles

- Proposal as decision environment: the UI should expose logic, assumptions, and sections, not just linear narrative.
- Fast-scan first: buyer-facing output should support the way 2026 decision-makers consume information, with high-signal cards and a 90-second brief before deeper sections.
- APMP-shaped control model: gate approvals, review checkpoints, and action follow-up stay separate so the operator can see both decision status and content readiness.
- Review discipline is explicit: Pink, Red, and Gold-equivalent checkpoints should each carry clear exit criteria rather than a generic status only.
- Operator output quality matters more than broad end-user onboarding in the current phase, so the app should favor strong generated ideas over generalized self-service UX.
- Owned follow-up: open actions should carry an owner, a due label in the current local slice, and a close condition so blockers are visible and easy to carry into the next checkpoint.
- Web-native first: HTML, CSS, and JavaScript are the primary medium; printable output is secondary.
- Explicit domain models: pursuit state should be represented as typed data, not implicit template text.
- Engine and renderer separation: qualification, assembly, proof, and narrative logic must stay independent of the UI.
- AI-safe boundaries: model-powered steps should be replaceable adapters, not mixed into core rules.
- Solo-operator realism: local workflows come first, but the shape should support a future hosted install.

## Module Map

### `src/domain/`

Typed models and schemas:

- `Opportunity`
- `QualificationResult`
- `SolutionModule`
- `ProposalExperience`
- `PursuitIdeaPack`
- packaged promoted concept-sheet payloads

### `src/engine/`

Rules and composition:

- qualification engine
- solution assembler
- experience composer
- idea pack builder
- promoted concept-sheet packaging helpers

### `src/services/`

Service boundaries:

- narrative service interface
- current rules-based narrative implementation
- idea generation service interface
- current rules-based idea generation implementation
- future AI-backed narrative adapters

### `src/ui/`

Presentation layer:

- opportunity workbench
- qualification panel
- buyer-facing experience renderer
- buyer-facing experience renderer with a fast-scanning decision feed and a deeper section mode
- export-friendly summary view
- operator workbench for approvals, review checkpoints with exit criteria, assumptions, module overrides, owned open actions, and scenario compare
- operator-first idea engine surface for buyer hot buttons, janitorial win themes, objection counters, competitor ghosting, proof matches, executive-summary variants, and a curated working-story brief

### `inputs/`

Structured local JSON inputs used for demos, repeatable test scenarios, and seeded promoted-workspace states.

## Data Flow

1. Intake loads a structured opportunity from seed JSON or a simple form.
2. The opportunity schema validates and normalizes the input.
3. The qualification engine scores the bid and emits recommendation plus risk flags.
4. The solution assembler selects service modules, staffing logic, transition steps, and proof examples.
5. The operator workbench can adjust assumptions, approval checkpoints, review checkpoints, owned open actions, and module overrides, then persist the current draft locally.
6. Saved scenarios preserve the decision basis plus gate/review readiness metadata for comparison and later restore.
7. The idea generation service turns the current pursuit state into strategy outputs for the operator.
8. The narrative service turns structured outputs into buyer-facing sections.
9. The UI renders both:
   - a navigable buyer-facing experience
   - an export-friendly structured summary
10. The packaging layer can turn a promoted buyer story variant into a dated deliverable bundle with source artifacts plus shareable HTML and PDF exports.

## First Vertical Slice Scope

The initial slice intentionally stops at a narrow, real workflow:

- one structured opportunity input
- rules-based qualification
- rules-based solution assembly
- proof selection from a small mock library
- buyer-facing proposal experience with layered navigation
- export summary view
- core non-UI tests

The current operator slice adds:

- gate approval controls for qualification, solution, and experience
- review checkpoints for content plan/Pink, evaluator-style/Red, and Gold readiness with explicit exit criteria
- an assumptions ledger with operator-added entries
- owned open actions with due labels, close conditions, and blocker visibility
- module overrides that reset downstream approval state when the draft changes
- a private operator idea engine that produces buyer hot buttons, janitorial win themes, differentiator options, objection counters, competitor ghosting angles, transition angles, proof matches, executive-summary variants, and validation questions
- a working-story curation layer that lets the operator pin one opening, choose the best themes and proof, and keep a compact live-bid memo tied to the current pursuit state
- named buyer story variants that preserve alternate story directions, support promotion into the buyer experience, and drive a printable concept-sheet export
- a deliverable bundle flow that packages the promoted concept into `outputs/deliverables/<slug>-YYYY-MM-DD/` with source snapshots, a standalone HTML concept sheet, and a PDF fallback
- scenario save/load and local persistence
- a comparison panel that shows the current draft against saved variants with readiness metadata

## Non-Goals For This Slice

- file parsing from PDFs, emails, or transcripts
- pricing optimization
- authenticated operators or clients
- persistent storage
- real model calls
- multi-opportunity dashboards

## Key Assumptions

- Boss Key primarily targets self-performed janitorial and facilities opportunities.
- Southeastern or otherwise preferred geographies matter in qualification.
- The first operator needs a local demo that shows system shape more than full workflow depth.
- A strong export summary reduces risk without making the document the primary artifact.
- APMP-style gate decisions should remain visible and separate from review readiness status.
- Review checkpoints should follow an APMP sequence: content plan first, evaluator-style review next, Gold readiness last.

## Consequences

Benefits:

- fast demoable prototype
- explicit seams for future AI, storage, and hosted workflows
- low risk to the rest of the repo
- operator workflow now reflects decision control rather than just presentation

Tradeoffs:

- local-only state for now
- intentionally simple rules
- UI optimized for proof of concept, not production-grade operator workflow yet
