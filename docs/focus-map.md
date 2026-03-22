# Repo Focus Map

## Flagship

`proposal-ops/` is the main product in this repository.

Working definition:
An internal proposal operating system for Boss Key that connects opportunity intelligence, capture strategy, and proposal execution into one repeatable workflow.

## What stays in the active lane

### Core product
- `proposal-ops/`

### Product-adjacent support
- `boss-key-website/`
- `marketing-agents/`
- root `server.js`
- root `package.json`

### Active working material
- `outputs/deliverables/`
- `projects/shared/records/`
- `projects/shared/data/`
- `projects/active/client/`
- `projects/internal/admin/`
- `projects/internal/personal/`
- `projects/pipeline/`
- `docs/`
- `templates/`

## What should not compete with the flagship

Projects that are interesting but not part of the current product story should move to `archive/`.

Use these tests:
- Does this directly improve the ProposalOps product?
- Does this help sell or demonstrate ProposalOps?
- Does this support the Boss Key operating model that ProposalOps is built for?

If the answer is no, archive it.

## Current support narrative

The repo now has a cleaner stack:

1. `proposal-ops/` is the product.
2. `boss-key-website/` is the market-facing wrapper and microsite layer.
3. `marketing-agents/` is the operating automation layer that feeds growth and intake.
4. `projects/` contains active client, internal, pipeline, and shared working material.
5. `outputs/` contains generated deliverables and scratch artifacts.
6. `archive/` holds older experiments and side directions.

## Near-term discipline

For the next phase of development:

- avoid starting new standalone experiments in the repo root
- put client-specific or secondary operational work under the right `projects/` lane
- put reusable product work under `proposal-ops/`, `boss-key-website/`, or `marketing-agents/`
- move non-core experiments into `archive/` as soon as they stop contributing to the main story
