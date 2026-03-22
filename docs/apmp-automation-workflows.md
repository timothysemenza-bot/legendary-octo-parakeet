# APMP Automation Workflows

This pack is designed for Codex automations, recurring runs, and operator-triggered work that should stay grounded in the APMP material exported locally from Helpjuice.

## Included skills

- `apmp-automation-orchestrator`
- `apmp-capture-cycle`
- `apmp-kickoff-plan`
- `apmp-compliance-content`
- `apmp-review-cycle`
- `apmp-knowledge-harvest`

## Included agents

- `apmp_automation_orchestrator`
- `apmp_capture_planner`
- `apmp_kickoff_coordinator`
- `apmp_compliance_content_lead`
- `apmp_review_director`
- `apmp_knowledge_harvester`

## How to use the pack

Use the orchestrator when a recurring run needs to inspect current pursuit state and decide what to do next. Use the specialist skills and agents when the scope is already clear.

Good automation pattern:

1. Inspect the current project root and identify the active pursuit stage.
2. Run exactly one primary workflow unless the inputs clearly justify a chained follow-on step.
3. Produce operational outputs, not broad study summaries.
4. Record blockers, assumptions, next owner, and next recommended run.
5. Harvest lessons and reusable content when the run closes a review, submission, or milestone.

## Suggested automation prompts

### Daily capture pulse

Use `apmp-automation-orchestrator` and `apmp-capture-cycle` to inspect the current pursuit workspace, identify the current gate or pre-gate stage, refresh the action list, update pursuit risks, and leave a short operator brief with next actions, owners, and date-sensitive blockers.

### Kickoff package prep

Use `apmp-kickoff-plan` to prepare or refresh the kickoff packet for the current opportunity. Build the proposal schedule, kickoff agenda, roles, draft executive-summary guidance, and content-plan handoff package.

### Compliance and outline refresh

Use `apmp-compliance-content` to build or update the requirements baseline, compliance matrix, response matrix starter, annotated outline, and section guidance for authors.

### Review readiness check

Use `apmp-review-cycle` to determine the appropriate review checkpoint, assemble a review agenda, consolidate comments into an issue log, and leave a clear rework plan.

### Weekly knowledge harvest

Use `apmp-knowledge-harvest` to capture lessons learned, extract reusable content objects, identify candidate templates, and recommend updates to standards or repositories.

## Fit by stage

| Stage | Best skill | Typical outputs |
| --- | --- | --- |
| Pursuit qualification and shaping | `apmp-capture-cycle` | gate packet, pursuit actions, risk notes, customer-contact priorities |
| Proposal planning | `apmp-kickoff-plan` | kickoff agenda, proposal management plan snapshot, schedule, responsibility matrix |
| Pre-draft content control | `apmp-compliance-content` | compliance matrix, response matrix, annotated outline, content plans |
| Mid-draft and late-draft quality control | `apmp-review-cycle` | review plan, comment log, rework instructions, proofread readiness |
| Post-milestone learning and reuse | `apmp-knowledge-harvest` | lessons learned, harvested assets, repository updates, follow-up actions |

## Local source of truth

Read `docs/apmp-automation-reference-map.md` first, then open the export JSON pages listed there only as needed.
