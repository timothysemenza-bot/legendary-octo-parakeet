# Demo Overview

## Goal

Show a prospective client how Codex can operate as an APMP-informed proposal operations copilot across the lifecycle of an engagement without requiring production client data.

## What this proof of concept demonstrates

1. Stage-aware orchestration
- Codex inspects the pursuit state and chooses the next justified workflow instead of trying to do everything at once.

2. APMP-grounded operations
- The workflow is grounded in the local APMP Helpjuice export and the repo's APMP automation reference map.

3. Repeatable outputs
- The system produces operator-ready artifacts such as gate briefs, kickoff materials, compliance baselines, review logs, and knowledge-harvest notes.

4. Safe client demo structure
- The project uses sanitized sample inputs and representative outputs so the workflow can be shown without exposing live opportunity details.

## Suggested demo sequence

1. Show the sample engagement inputs in `inputs/`.
2. Explain the APMP automation pack at the repo level.
3. Run the orchestrator prompt from `docs/prompt-pack.md`.
4. Show the specialist prompts for capture, kickoff, compliance, review, and knowledge harvest.
5. Walk through the sample artifacts in `working/sample-artifacts/`.
6. Close with how this would map to a real client project root and a recurring automation.

## What the client should understand by the end

- Codex can support proposal operations in a structured way.
- The workflow is not generic AI improvisation; it follows documented operating logic.
- The system can be adapted to the client's process maturity and bid environment.
- A live engagement would use the same pack with client-specific inputs, project rules, and delivery expectations.
