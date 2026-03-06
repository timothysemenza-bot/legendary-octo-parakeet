# ADR-003: Multi-Tenant Isolation

## Status
Accepted

## Decision
Default to strict logical isolation with required `client_id` and `workspace_id` on all domain records, PostgreSQL Row Level Security, and tenant-scoped storage prefixes.

## Rationale
- Balances security and operational complexity for v1
- Supports portability with config-driven onboarding

## Consequences
- All queries and indexes must include tenant scopes
- Enterprise tier can upgrade to dedicated infrastructure isolation
