# Outputs

This folder is for generated artifacts only.

## Lanes

- `deliverables/`: client-ready or review-ready packages
- `generated/`: generated exports, reports, logs, and compatibility outputs
- `scratch/`: recordings, quick captures, and disposable operator artifacts

## Naming convention

- deliverable bundles: `<slug>-YYYY-MM-DD`
- scratch bundles: `<source-or-task>-YYYY-MM-DD` when they are likely to persist

## Rules

- Do not treat `outputs/` as a source folder.
- One thread should own one output subfolder.
- If the artifact is not meant to ship, keep it in `scratch/` or ignore it.
