---
name: project-bootstrap
description: Create or normalize a project folder so it is ready for Codex threads, worktrees, handoffs, and generated-output separation. Use when starting a new client, internal, or pipeline project inside this repo.
---

# Project Bootstrap

## Purpose

Create a predictable project home with clear inputs, working files, docs, and local instructions so Codex can operate without guessing.

## When to use it

- when starting a new project under `projects/`
- when normalizing an ad hoc folder into the standard layout
- when adding a dedicated project root for the Codex app or IDE
- when a project needs its own `AGENTS.md` and handoff conventions

## Required inputs

- project name
- lane: `active`, `internal`, `pipeline`, `completed`, or `shared`
- bucket or owner grouping when applicable
- project slug if the default slug is not good enough
- short description of the project purpose

## Expected outputs

- new project folder at `projects/<lane>/<bucket>/<slug>/`
- `README.md`
- `AGENTS.md`
- `docs/`, `inputs/`, and `working/` directories
- clear placement instructions for future files

## Step-by-step instructions

1. Confirm the correct lane and bucket before creating anything.
2. Create the project folder using the standard scaffold instead of hand-building it.
3. Add a short project description so later threads understand the scope quickly.
4. Tailor the generated `AGENTS.md` to the project if it has special constraints such as client confidentiality, a local runtime, or a fixed deliverable format.
5. Keep source material in `inputs/`, ongoing drafts in `working/`, and longer-lived context in `docs/`.
6. If the project will generate client-ready packages, point future threads to `outputs/deliverables/` instead of storing exports inside the project folder.

## Scripts and resources

- Run `.\scripts\bootstrap-project.ps1 -ProjectName "<name>" -Lane <lane> -Bucket <bucket> -Description "<summary>"`.
- Use `.\templates\project\README.template.md` and `.\templates\project\AGENTS.template.md` as the baseline.
- Read `.\projects\README.md` for lane definitions and placement rules.
