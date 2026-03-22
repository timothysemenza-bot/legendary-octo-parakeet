---
name: qa-review
description: Review a scoped change set for regressions, missing verification, and release risk. Use when a branch, worktree, or thread needs a clean Codex review pass before staging or handoff.
---

# QA Review

## Purpose

Turn a raw diff into a reviewable release decision by checking scope, verification, risks, and handoff readiness.

## When to use it

- when a thread has a non-trivial diff ready for review
- when multiple agents have worked in parallel and the merge boundary needs a final pass
- when staging by hunk or splitting follow-up fixes
- when user requests a review or wants to know what is risky

## Required inputs

- the project root or branch being reviewed
- changed files or compare ref if available
- verification commands relevant to that scope
- any known risk areas or user priorities

## Expected outputs

- prioritized findings with file references
- verification summary
- open questions or assumptions
- staging or follow-up guidance

## Step-by-step instructions

1. Start with the narrowest review scope possible: one root, one worktree, or one compare ref.
2. Run a change-scope summary before deep review so you know which files and roots moved.
3. Inspect for behavioral regressions, broken paths, missing docs, missing tests, or generated artifacts committed by accident.
4. Prefer findings over summaries. Lead with concrete issues, not praise.
5. Run the smallest useful verification for the touched area and report what was not tested.
6. If the diff spans multiple concerns, recommend how to stage or split it for cleaner review.
7. Finish with residual risks and whether the change looks ready to ship.

## Scripts and resources

- Run `.\scripts\review-change-scope.ps1 -IncludeStatus` for a quick branch and path summary.
- Read `.\docs\codex-git-workflow.md` before recommending staging or review flow changes.
- Use project-local test or lint commands from the scoped root instead of running broad repo-wide checks by default.
