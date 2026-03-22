---
name: proposal-document-workflow
description: Run proposal, brief, and document assembly work from reusable templates through review-ready packaging. Use when a thread needs to build a proposal artifact, structured brief, one-pager, or client-ready document without mixing templates and outputs.
---

# Proposal Document Workflow

## Purpose

Guide a document-centric thread from source collection to draft assembly, review, and packaging while keeping reusable templates separate from generated deliverables.

## When to use it

- when producing proposals, statements of work, one-pagers, capability statements, or briefing packs
- when adapting reusable proposal content for a specific client or pursuit
- when packaging a review-ready document bundle
- when a thread needs clear separation between templates, working files, and exports

## Required inputs

- project or client root
- source notes, solicitation, brief, or business context
- desired output type and audience
- delivery date if timing affects packaging or review order

## Expected outputs

- working draft or structured outline inside the relevant project folder
- references to reusable assets pulled from `templates/`
- review notes or issue list
- deliverable bundle in `outputs/deliverables/<slug>-YYYY-MM-DD/`

## Step-by-step instructions

1. Start in the correct project root and keep project-specific source material there.
2. Pull reusable copy blocks, layouts, or snippets from `templates/proposals/` or `templates/sample-content/` rather than copying old deliverables.
3. If the task is a managed proposal effort, pair this skill with `$proposal-manager` for schedule, review, and compliance control.
4. Draft the working document inside the project folder so the source remains close to its context.
5. When the draft becomes review-ready or client-ready, create a deliverable bundle under `outputs/deliverables/`.
6. Put editable assembly files in `source/`, final exports in `export/`, and record assumptions or verification notes in the bundle `README.md`.
7. Keep generated exports out of `templates/` and out of the project root unless the export itself is a tracked source asset.

## Scripts and resources

- Run `.\scripts\new-deliverable-bundle.ps1 -Slug "<slug>" -Title "<title>"` before assembling a handoff package.
- Use `.\templates\proposals\` for proposal structures and snippets.
- Use `.\templates\sample-content\` for reusable sample sections and proof-point starters.
- Use `.\.agents\skills\proposal-manager\SKILL.md` when the user needs a full proposal-management package instead of document assembly alone.
