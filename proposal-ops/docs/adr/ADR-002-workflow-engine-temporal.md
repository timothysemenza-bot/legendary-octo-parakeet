# ADR-002: Workflow Engine

## Status
Accepted

## Decision
Use Temporal for stateful long-running workflows with explicit human gate waits.

## Rationale
- Durable timers and retries
- Deterministic workflow history
- Native fit for human-in-the-loop approvals and rework loops

## Consequences
- Requires Temporal infrastructure and workflow versioning policy
