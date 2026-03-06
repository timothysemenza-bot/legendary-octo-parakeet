# Opportunity Service

Owns intake, qualification lifecycle, and opportunity metadata.

## Endpoint Skeleton (v1)
- `POST /opportunities/intake`
- `POST /opportunities/:id/qualify`
- `POST /opportunities/:id/compliance/shred`
- `POST /opportunities/:id/gates/:gateCode/decision`
- `POST /opportunities/:id/reviews/:cycleId/comments`
- `POST /opportunities/:id/submission/authorize`

## Source
- `src/contracts.ts`
- `src/opportunities.controller.ts`
- `src/gates.controller.ts`
- `src/reviews.controller.ts`
- `src/submission.controller.ts`
