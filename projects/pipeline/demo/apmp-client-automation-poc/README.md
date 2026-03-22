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

