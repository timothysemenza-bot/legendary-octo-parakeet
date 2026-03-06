# ADR-004: Audit Event Model

## Status
Accepted

## Decision
Use append-only audit events for gate decisions, stage transitions, artifact version changes, and agent actions.

## Rationale
- Required for regulatory traceability and quality governance
- Enables forensic reconstruction of proposal lifecycle decisions

## Consequences
- No hard delete of governed events
- Event payload contract versioning required
