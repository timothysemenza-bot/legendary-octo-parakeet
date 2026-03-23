# APMP Client Automation POC

Type: pipeline

## Purpose

Proof-of-concept workspace for demonstrating APMP-informed Codex automation on a sample client engagement without exposing live client data. This project packages a repeatable demo scenario, operator runbook, prompts, and expected outputs so the workflow can be shown safely to prospective clients before being deployed on active engagements.

## Inputs

- `inputs/sample-client-brief.md`
- `inputs/sample-opportunity-intake.md`
- `inputs/sample-rfp-fragment.md`
- future sanitized client examples you want to test against the same workflow

## Working folders

- `docs/`
- `inputs/`
- `working/`

## Demo assets

- `docs/demo-overview.md`: what this proof of concept demonstrates
- `docs/demo-script.md`: a short client-facing walkthrough
- `docs/client-facing-talk-track.md`: how to explain value, safeguards, and next steps
- `docs/prompt-pack.md`: ready-to-run prompts for the APMP automation skills and agents
- `working/sample-artifacts/`: representative outputs to show during a demo

## Recommended Codex entry point

Start the demo from this project root so the thread stays isolated:

`projects/pipeline/demo/apmp-client-automation-poc`

## Deliverables

Generated packages belong in `outputs/`, not inside this project folder.

## Parallel Lane Workspace

The active multi-thread run scaffold for this project is:

`outputs/runs/2026-03-21/`

Use that run folder for live lane execution.

- `00-operator-brief/`: coordinator brief, launch order, and dependency rules
- `01-intake/`: source normalization and intake handoff
- `02-compliance/`: requirements baseline and compliance package
- `03-kickoff/`: kickoff packet, schedule, and role planning
- `04-content/`: writer-ready content planning package
- `05-qa/`: review readiness and issue-log package
- `06-final/`: final merge and operator delivery note

## Read-Only Shared References

Treat these as preserved references during lane execution:

- `inputs/`
- `docs/`
- `working/poc-output-map.md`
- `working/sample-artifacts/`

Do not place live lane outputs in `working/`. The `working/sample-artifacts/` files remain in place as demo references and should be preserved.

