---
name: apmp-automation-orchestrator
description: Coordinate a recurring APMP-informed automation run across capture, kickoff, compliance, review, and knowledge-harvest workflows. Use when Codex should inspect the current pursuit state, decide the next justified workflow, and leave an operator-ready package instead of a broad narrative summary.
---

# APMP Automation Orchestrator

## Purpose

Run one stage-aware APMP workflow at a time so recurring automations stay focused, current, and useful.

## When to use it

- when an automation should inspect a proposal or pursuit workspace and decide what to do next
- when the current stage is unclear and the run needs to triage before acting
- when you want one recurring run to dispatch cleanly into capture, kickoff, compliance, review, or knowledge-harvest work

## Required inputs

- the project root or pursuit root
- current due date or next major review date, if known
- any existing proposal, capture, review, or knowledge artifacts
- the immediate run objective, if one is already defined

## Expected outputs

- current-stage assessment
- recommended primary workflow for this run
- updated action list with owners or owner placeholders
- concise operator brief with blockers, assumptions, and next recommended run

## Step-by-step instructions

1. Read `docs/apmp-automation-reference-map.md` before inspecting deeper source pages.
2. Identify the current lifecycle stage from the artifacts on disk: capture, kickoff prep, compliance/content planning, review cycle, or harvest.
3. Prefer a single primary workflow for the run. Only chain a second workflow when the first naturally produces a mandatory handoff.
4. If the pursuit is pre-proposal, route to capture work. If kickoff materials are missing, route to kickoff planning. If the outline or requirements baseline is weak, route to compliance/content work. If a draft exists, route to review work. If a review or submission just ended, route to knowledge harvest.
5. Keep outputs operational: matrices, schedules, packets, issue logs, and next actions.
6. Do not create large new planning documents unless the stage requires them.
7. End with an operator brief that states what changed, what remains blocked, and which specialist should handle the next run.

## Scripts and resources

- Read `docs/apmp-automation-reference-map.md`.
- Read `docs/apmp-automation-workflows.md` for workflow fit and prompt patterns.
- Reuse `.\.agents\skills\proposal-manager\scripts\generate-proposal-workplan.ps1` when the selected workflow needs a schedule seed.
