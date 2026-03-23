# APMP Client Automation POC Rules

## Scope

- Keep work inside this project unless the task explicitly spans another root.
- Put source edits here.
- Put generated artifacts in `outputs/`.
- Treat this project as a sanitized demo environment only.
- Prefer the APMP automation pack before inventing one-off workflows:
  - `apmp-automation-orchestrator`
  - `apmp-capture-cycle`
  - `apmp-kickoff-plan`
  - `apmp-compliance-content`
  - `apmp-review-cycle`
  - `apmp-knowledge-harvest`

## Multi-Thread Workspace

- The active run root is `outputs/runs/2026-03-22/`.
- Read `outputs/runs/2026-03-22/00-operator-brief/README.md` before launching a lane thread.
- Use one Codex thread per lane.
- Lane threads may create or update files only inside their assigned lane folder.
- Lane `README.md` files are instructions and should stay read-only during execution.
- Use each lane's `handoff.md` to report status, assumptions, blockers, and manual-review needs.
- `06-final/` is the only lane allowed to assemble a merged package for this run.
- Use `docs/orchestration-kit/` for coordinator runbooks, reusable prompts, and current-pursuit orchestration notes.

## Protected References During Lane Execution

- `inputs/**/*`
- `docs/**/*`
- `working/poc-output-map.md`
- `working/sample-artifacts/**/*`
- `README.md`
- `AGENTS.md`
- `outputs/runs/2026-03-22/00-operator-brief/**/*`

## Verification

- Run the smallest check that proves the change.
- Update nearby docs when folder ownership or workflow changes.

## Handoff

- Leave a short note describing what changed, what was verified, and what still needs manual review.
- When preparing a client demo, keep outputs concise and operator-ready.
- Make all assumptions explicit so the workflow can be explained live.

