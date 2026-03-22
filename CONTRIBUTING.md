# Contributing

## Repo focus

This repository is centered on `proposal-ops` as the flagship product.

Supporting surfaces:
- `boss-key-website/`
- `marketing-agents/`
- `projects/`
- `templates/`
- `outputs/`

Archived legacy code now lives under `archive/` and should stay out of normal product work unless you are intentionally revisiting it.

## Workflow

1. Create a branch from `main`.
2. Keep the change scoped to one active lane when possible.
3. Update docs when the product story, folder ownership, or workflow changes.
4. Merge only after review and verification.

## Placement rules

- Put flagship product work in `proposal-ops/`.
- Put market-facing packaging and offer presentation in `boss-key-website/` or `marketing-agents/`.
- Put client, internal, pipeline, and shared working material in `projects/`.
- Put generated deliverables, reports, and scratch captures in `outputs/`.
- Put reusable starting points in `templates/`.
- Move non-core experiments or retired systems into `archive/`.

## Verification

Run the checks that match the area you touched.

- Website/server work: `npm start`
- Writing center tribute flow: `npm run test:writing-center-tribute`
- ProposalOps work: run targeted tests and verification inside `proposal-ops/`

## Local conventions

- Keep generated files out of version control.
- Update `.gitignore` when a new local-only output folder appears.
- Do not leave loose experiments in the repo root.
- Prefer repo-local skills in `.agents/skills/` and repo-local custom agents in `.codex/agents/`.
- When using Codex app worktrees, keep changes scoped to one project root whenever possible.

## Optional local safety

Install the repo hooks to catch accidental pushes to `main`:

```bash
git config core.hooksPath .githooks
```
