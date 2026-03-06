# API Contracts v1

## Endpoints
- POST /opportunities/intake
- POST /opportunities/:id/qualify
- POST /opportunities/:id/compliance/shred
- POST /opportunities/:id/gates/:gateCode/decision
- POST /opportunities/:id/reviews/:cycleId/comments
- POST /opportunities/:id/submission/authorize

## Contract Notes
- Every request includes tenant scope context.
- Every mutating endpoint emits audit events.
- Gate transition validation is centralized in workflow engine.
