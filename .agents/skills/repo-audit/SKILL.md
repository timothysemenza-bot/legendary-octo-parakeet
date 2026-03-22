---
name: repo-audit
description: Audit repository structure, ownership, duplication, archival material, generated outputs, and Codex readiness. Use when planning cleanup, deciding project roots, validating worktree safety, or preparing a Codex-first reorganization.
---

# Repo Audit

## Purpose

Produce a practical repository assessment that helps operators decide what belongs where, what should be archived, and how to organize Codex projects, skills, threads, and worktrees.

## When to use it

- when a repo feels cluttered or hard to navigate
- when project roots are unclear
- when reusable assets and generated outputs are mixed together
- when multiple agents need clearer write boundaries
- when preparing a restructuring plan before moving files

## Required inputs

- the current repository root
- any user constraints about preserving history, branch boundaries, or risky areas
- optional guidance on which products or client projects matter most

## Expected outputs

- top-level structure summary
- classification of active, archival, generated, reusable, and ambiguous material
- safe moves versus risky moves
- recommended Codex app project roots
- worktree and parallel-thread guidance

## Step-by-step instructions

1. Start at the current repository root and inventory the major folders before suggesting changes.
2. Identify which roots are product code, client work, shared assets, templates, generated outputs, scratch space, and archive material.
3. Flag duplication, naming collisions, stale roots, mixed concerns, and relative-path coupling.
4. Separate safe moves from risky moves. Prefer moves and archival over deletion.
5. Recommend which directories should stay as independent Codex projects and which should remain inside a shared repo.
6. Call out anything that will create merge conflicts or thread confusion when multiple agents run in parallel.
7. End with a Codex-specific recommendation set: project roots, worktree strategy, and next cleanup actions.

## Scripts and resources

- Run `.\scripts\repo-audit.ps1` for a quick Markdown inventory of folders, `AGENTS.md` coverage, skills, custom agents, and git status.
- Read `.\AGENTS.md` for repo-wide operating rules.
- Read `.\docs\codex-workspace-guide.md` and `.\docs\top-level-triage.md` before proposing structural changes.
