# ADR-005: Retrieval Architecture

## Status
Accepted

## Decision
Use tenant-scoped hybrid retrieval: metadata filters + full-text + vector similarity, with citation packing and unsupported-claim checks.

## Rationale
- Balances precision and recall for proposal content reuse
- Preserves evidence-based drafting discipline

## Consequences
- Requires embedding lifecycle management
- Requires deterministic tenant/workspace filter enforcement in every query
