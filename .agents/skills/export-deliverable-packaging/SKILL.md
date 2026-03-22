---
name: export-deliverable-packaging
description: Package review-ready and client-ready outputs into predictable bundles with clean source and export separation. Use when a task produces files that need to be handed off, reviewed, archived, or delivered.
---

# Export Deliverable Packaging

## Purpose

Standardize how this repo stores generated deliverables so multiple Codex threads can work in parallel without overwriting each other or confusing reusable source with disposable output.

## When to use it

- when exporting PDFs, slide decks, HTML packages, reports, or review bundles
- when preparing material for client delivery or internal approval
- when a project thread has finished assembly and needs a stable handoff folder
- when output naming and folder ownership need to stay predictable across worktrees

## Required inputs

- deliverable slug
- title or short package label
- source location for the material being packaged
- delivery date or packaging date
- any review or verification notes that should travel with the bundle

## Expected outputs

- bundle folder at `outputs/deliverables/<slug>-YYYY-MM-DD/`
- `source/` directory for editable or assembly assets
- `export/` directory for final client-facing files
- `README.md` with assumptions, contents, and handoff notes

## Step-by-step instructions

1. Create a dedicated deliverable bundle before copying exports around.
2. Put editable or staging material in `source/` and final deliverables in `export/`.
3. Use a date-stamped slug so parallel threads do not trample each other.
4. Record what the bundle contains, what was verified, and what is still assumed.
5. If the bundle is derived from a project under `projects/` or a product root, keep the source-of-truth files there and copy only the packaged subset into the bundle.
6. If a package is superseded or delivery is cancelled, move it to `archive/` rather than deleting it unless removal is clearly safe.

## Scripts and resources

- Run `.\scripts\new-deliverable-bundle.ps1 -Slug "<slug>" -Title "<title>"`.
- Read `.\outputs\README.md` for bundle conventions and output ownership rules.
- Read `.\docs\codex-workspace-guide.md` for the repo-wide output placement rules.
