# MVP Epics and User Stories v1

## Epic 1: Tenant Foundation
- Story: As an admin, I can create a client and workspace so data is isolated.
  - Acceptance: records require client/workspace ids; cross-tenant access test fails with denial.

## Epic 2: Intake and Qualification
- Story: As an operator, I can ingest solicitation files and generate a qualification draft.
  - Acceptance: opportunity and solicitation records created, Gate A required.

## Epic 3: Compliance Artifact Generation
- Story: As a compliance lead, I can shred an RFP into atomic requirements.
  - Acceptance: each requirement includes source locator and mandatory flag.
- Story: As a compliance lead, I can generate compliance and response matrices.
  - Acceptance: each row links to requirement and owner.

## Epic 4: Gate Engine and Audit
- Story: As a manager, I can approve/reject/rework gates with rationale.
  - Acceptance: decision stored with immutable audit event.

## Epic 5: Drafting and Review Discipline
- Story: As a section owner, I can generate section drafts with citations.
  - Acceptance: unsupported claims flagged before review closure.
- Story: As a reviewer, I can create comments and request rework.
  - Acceptance: rework packet includes owner and due date.

## Epic 6: Submission and Lessons
- Story: As an executive approver, I can authorize final submission only after Gate F.
  - Acceptance: authorization API rejects if Gate F not approved.
- Story: As a knowledge manager, I can approve lessons learned promotion.
  - Acceptance: Gate G required before archive completion.

## Epic 7: Email-Driven Ops Automation
- Story: As a proposal operator, I can ingest inbound emails and extract deterministic bid-status signals.
  - Acceptance: email ingest endpoint stores parsed updates with confidence/rationale and queue status.
- Story: As a proposal manager, I can apply or dismiss email-derived updates from a review queue.
  - Acceptance: applying a BID_STATUS signal updates opportunity pursuit recommendation and emits audit events.
- Story: As an operator, I can configure mailbox connections and run sync to ingest messages automatically.
  - Acceptance: connection create/list/sync endpoints exist; sync ingests new messages and skips duplicates by external message id.
- Story: As an operator, I can pause/resume/delete email connections to control ingestion safely.
  - Acceptance: update/delete endpoints exist; active connections cannot be deleted until paused or disabled.
- Story: As an operator, I can set Outlook access tokens on a connection so sync can authenticate.
  - Acceptance: token-set endpoint exists; Outlook sync uses configured token/cursor state and processes pages incrementally.
- Story: As an operator, I can trigger Outlook token refresh and have sync auto-refresh near expiry.
  - Acceptance: refresh endpoint exists; sync refreshes token when expiry is near and then continues ingestion.
- Story: As an operator, I can view connection configs without exposing raw secrets in API responses.
  - Acceptance: access_token/refresh_token/client_secret are redacted in returned connection config payloads.
- Story: As an admin, I can rotate secret-store encryption keys without losing existing secret references.
  - Acceptance: rotation utility re-encrypts all entries under a new key while preserving secret refs.
