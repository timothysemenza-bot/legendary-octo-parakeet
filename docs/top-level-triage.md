# Top-Level Triage

This is the working classification for the remaining top-level folders after the Codex-first reorganization pass.

## Keep Active

These directly support the current main story and should stay easy to find.

### `proposal-ops/`
- Status: `keep active`
- Why: flagship product

### `boss-key-website/`
- Status: `keep active`
- Why: market-facing wrapper, proof surface, and microsite layer for the same offer

### `marketing-agents/`
- Status: `keep active`
- Why: operational automation layer that feeds growth, intake, review, and proposal workflows

### `projects/`
- Status: `keep active`
- Why: active client, pipeline, internal, and shared working material organized into Codex-friendly lanes

### `docs/`
- Status: `keep active`
- Why: repo-level planning, positioning, and operating decisions

### `outputs/`
- Status: `keep active`
- Why: generated deliverables, reports, and scratch artifacts are now isolated from source work

### `scripts/`
- Status: `keep active`
- Why: contains current utility scripts, including the writing center tribute smoke test and content migration helpers

## Keep As Support

These are not the main product, but they plausibly support the active lane and do not need urgent relocation.

### `assets/`
- Status: `keep as support`
- Why: shared visual assets used by active website and prototype surfaces

### `templates/`
- Status: `keep as support`
- Why: reusable proposal/content scaffolding and project bootstrap assets live here

### `.agents/skills/`
- Status: `keep as support`
- Why: local Codex workflow assets; not product code, but useful repo-side operating support

### `.codex/agents/`
- Status: `keep as support`
- Why: repo-local custom agent roles for parallel and review workflows

## Secondary Work Now Nested Under Projects

These are still real active work products, but they no longer compete with the flagship narrative at the repo root.

### `projects/internal/admin/boss-key-llc-admin/`
- Status: `secondary, relocated`
- Why: company admin and compliance operating files that should stay close at hand without reading like product code

### `projects/active/client/jwblng-mvp/`
- Status: `secondary, relocated`
- Why: substantial client-specific website work with its own delivery and launch artifacts

### `projects/active/client/editry/`
- Status: `secondary, relocated`
- Why: client business materials and a microsite package that support current work but are not the ProposalOps headline

### `projects/internal/personal/apmp-professional/`
- Status: `secondary, relocated`
- Why: personal credentialing package that is useful to keep, but outside the main product lane

## Already Archived

These have already been moved out of the way.

- `archive/experiments/charleigh-invention/`
- `archive/experiments/metroid-roguelite-mvp/`
- `archive/experiments/project-nebula/`
- `archive/experiments/summer-camp-comparison/`
- `archive/experiments/dungeon-crawler.html`
- `archive/legacy-root-stack/mod/`
- `archive/legacy-root-stack/src/`
- `archive/legacy-root-stack/tests/`
- `archive/legacy-root-stack/tools/`
- `archive/legacy-root-stack/config/`
- `archive/legacy-root-stack/requirements.txt`
- `archive/legacy-root-stack/.luacheckrc`
- `archive/legacy-root-stack/.artifacts/`
- `archive/legacy-root-stack/.github/workflows/ci.yml`
- `archive/legacy-root-stack/.github/workflows/integration.yml`
- `archive/legacy-root-stack/.github/workflows/release.yml`

## What changed in the latest cleanup pass

The old mixed root stack had already been moved under `archive/legacy-root-stack/`.
The latest pass:

- moved active working material from `workspace/` into `projects/`
- moved generated artifacts from `workspace/deliverables/` and `output/` into `outputs/`
- moved reusable proposal assets into `templates/`
- moved repo-local Codex skills into `.agents/skills/`
- reserved `workspace/` for legacy local scratch only

## Practical Rule

When deciding where new work goes:

1. If it strengthens `proposal-ops`, put it there.
2. If it helps sell or demonstrate the offer, it probably belongs in `boss-key-website` or `marketing-agents`.
3. If it is client, internal, pipeline, or shared working material, put it under `projects/`.
4. If it is a generated deliverable or scratch artifact, put it under `outputs/`.
5. If it is reusable scaffolding, put it under `templates/` or `.agents/skills/`.
6. If it does not support the current story, archive it quickly.
