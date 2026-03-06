# Workflow State Machine v1

## Stages
INTAKE -> QUALIFICATION -> STRATEGY -> COMPLIANCE -> CONTENT_PLANNING -> DRAFTING -> REVIEW -> SUBMISSION -> ARCHIVE

## Gate Map
- Gate A applies to QUALIFICATION exit
- Gate B applies to STRATEGY exit
- Gate C applies to COMPLIANCE exit
- Gate D and Gate E apply to REVIEW progression
- Gate F applies to SUBMISSION authorization
- Gate G applies to ARCHIVE closeout

## Decision Outcomes
- APPROVED: move to next stage
- REJECTED: return to previous relevant stage and set BLOCKED until reassigned
- REWORK_REQUIRED: stay in current stage with required actions

## Forbidden Transitions
- Any jump that skips a stage
- DRAFTING before Gate C APPROVED
- SUBMISSION authorization before Gate F APPROVED

## Audit Event Requirements
Each transition emits:
- event_id
- timestamp
- actor_type (human|agent|system)
- actor_id
- client_id
- workspace_id
- opportunity_id
- action
- before_state
- after_state
- linked_artifacts
