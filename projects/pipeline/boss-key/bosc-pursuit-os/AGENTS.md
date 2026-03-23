# Boss Key Pursuit OS Rules

## Scope

- Keep work inside this project unless the task explicitly spans another root.
- Treat this as a self-contained prototype for a Boss Key pursuit/proposal operating system.
- Keep business logic in `src/engine/` and `src/domain/`; do not bury decision logic inside UI components.
- Keep AI integrations behind interfaces in `src/services/`; do not wire vendor-specific model calls into the core slice.

## Inputs And Outputs

- Put reusable local opportunity inputs in `inputs/`.
- Keep scratch notes or operator thread material in `working/`.
- Put generated review bundles or client-ready artifacts in the repo-level `outputs/`, not beside source files here.

## Verification

- Run the smallest check that proves the change.
- Prefer tests for non-UI business logic first.
- Run `npm run typecheck` and `npm run build` when the UI or data contracts change.

## Handoff

- Leave docs updated when the architecture, workflow, or folder ownership changes.
- Call out which assumptions are intentionally rules-based or mocked so future AI integration work is clear.

