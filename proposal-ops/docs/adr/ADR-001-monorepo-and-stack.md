# ADR-001: Monorepo and Stack

## Status
Accepted

## Decision
Use a TypeScript-first monorepo with pnpm + Turborepo, Next.js for frontend workbench, NestJS for backend services, PostgreSQL + pgvector for persistence, and Temporal for workflow orchestration.

## Rationale
- Shared domain types and contracts across services
- Strong support for modular bounded contexts
- Reliable long-running workflow support

## Consequences
- Requires disciplined package boundaries
- Requires CI guardrails for contract compatibility
