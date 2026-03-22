# Demo Script

## Format

Aim for a 10- to 15-minute walkthrough.

## Opening

Explain that the demo is a sanitized proof of concept showing how Codex can support an APMP-informed proposal lifecycle without needing access to confidential client data.

## Step 1: Show the sample engagement

Open:
- `inputs/sample-client-brief.md`
- `inputs/sample-opportunity-intake.md`
- `inputs/sample-rfp-fragment.md`

Say:
- "This is the kind of source material a team typically has early in an engagement."
- "The workflow starts from incomplete but realistic inputs."

## Step 2: Show the APMP automation logic

Open:
- `docs/prompt-pack.md`
- `C:/Users/timot/Documents/Proposal-Microsite/docs/apmp-automation-reference-map.md`

Say:
- "The system is grounded in the APMP material we exported locally."
- "The orchestrator determines the current stage, then routes the run to the right specialist workflow."

## Step 3: Demonstrate the orchestration pattern

Use the orchestrator prompt first.

Say:
- "Instead of a monolithic prompt, we let the system choose whether this run should behave like capture, kickoff, compliance, review, or knowledge harvest."

## Step 4: Show representative outputs

Open:
- `working/sample-artifacts/01-capture-brief.md`
- `working/sample-artifacts/02-proposal-workplan.md`
- `working/sample-artifacts/03-compliance-outline-starter.md`
- `working/sample-artifacts/04-review-issue-log.md`
- `working/sample-artifacts/05-knowledge-harvest.md`

Say:
- "These are the kinds of artifacts the workflow leaves behind: concise, operational, and ready for a proposal lead or account lead to use."

## Step 5: Explain the client rollout path

Open:
- `docs/client-facing-talk-track.md`

Say:
- "A live rollout would use the same structure inside a client-specific project root, with the client's inputs, templates, roles, and review cadence."

## Close

Suggest a next step:
- a one-engagement pilot
- a sanitized historical replay
- or a weekly operator automation for capture and review support
