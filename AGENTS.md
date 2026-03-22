# Codex Operating Guide

This repository is organized for Codex-first work.

## Pick the right root

- Use the repo root for cross-repo architecture, restructuring, repo hygiene, and shared docs.
- Use `proposal-ops/`, `boss-key-website/`, or `marketing-agents/` as focused project roots for implementation work inside those products.
- Use a folder under `projects/` as the root when the task is client-specific, internal, or pipeline-specific.

## Folder ownership

- `proposal-ops/`: flagship product code and demos
- `boss-key-website/`: public-facing website and packaging surfaces
- `marketing-agents/`: automation, intake, growth, and operator workflows
- `projects/`: active client, internal, pipeline, completed, and shared working material
- `outputs/`: generated deliverables, reports, scratch captures, and packaging bundles
- `templates/`: reusable project and proposal starting points
- `.agents/skills/`: repo-local Codex skills
- `.codex/agents/`: repo-local custom agent definitions
- `workspace/`: legacy local scratch only; do not treat it as a normal project lane

## Parallel work

- Prefer one worktree or one focused thread per project root.
- Avoid spreading one task across multiple roots unless the task is explicitly cross-repo.
- Assign clear ownership when multiple agents run in parallel.
- Put thread-specific generated artifacts under a dedicated folder in `outputs/` so threads do not overwrite each other.
- Do not edit another thread's generated artifacts unless the handoff is explicit.

## Outputs

- Use `outputs/deliverables/<slug>-YYYY-MM-DD/` for client-ready or review-ready bundles.
- Use `outputs/generated/` for generated reports, logs, exports, and compatibility artifacts.
- Use `outputs/scratch/` for recordings, quick captures, and disposable operator artifacts.
- Keep source material in `projects/` or product folders, not in `outputs/`.

## Git and review

- Keep changes scoped to one lane whenever possible.
- Run the narrowest verification that proves the change.
- Use the Codex review flow or `/review` before committing larger diffs.
- Stage by hunk when a thread touched more than one concern.

## Skills and custom agents

- Repo-local skills live in `.agents/skills/`.
- Repo-local custom agents live in `.codex/agents/`.
- Human-readable role briefs live in `agents/`.

## Handoff expectation

Every substantial change should leave:

- updated paths or references if files moved
- docs updated when ownership or workflow changed
- generated output separated from reusable source
