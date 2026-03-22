# Codex Git Workflow

Use this workflow to keep Codex changes reviewable and easy to hand off.

## Branching

- Create scoped branches with the `codex/` prefix.
- Prefer one branch per coherent task or project root.
- Avoid mixing restructuring, product code, and generated deliverables in one branch.

Examples:

- `codex/proposal-ops-onboarding-pack`
- `codex/jwblng-phase1-fixes`
- `codex/repo-codex-structure`

## Worktrees

- Use a worktree when the task is long-running, risky, or likely to conflict with your current local checkout.
- Keep one active branch per worktree.
- If you need the branch in your main checkout, hand the thread back to Local instead of checking the same branch out twice.

## Review

- Use the Codex app review pane for local worktrees.
- Use `/review` in the CLI for quick findings-first review.
- Review against the base branch for larger tasks.
- Review uncommitted changes before committing if the task drifted.

## Staging

- Stage by hunk when a thread touched multiple concerns.
- Keep generated artifacts out of the main code commit unless the deliverable itself is the point of the task.
- Revert outputs or scratch files you do not intend to ship.

## Verification

- Run the smallest verification that proves the change.
- Record what you ran and what you did not run.
- For structure changes, verify links, scripts, and path references before committing.

## Commit hygiene

- Commit structure moves separately from follow-up behavior changes when possible.
- Use commit messages that name the lane you changed.
- Do not commit local browser profiles, caches, logs, or temporary captures.
