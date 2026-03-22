# APMP Automation Reference Map

This reference map distills the local APMP Helpjuice export at `outputs/generated/apmp-helpjuice-export-2026-03-22/` into the workflow guidance most useful for Codex automations, scheduled runs, and repeatable agent handoffs.

Use this file as the stable reference layer for APMP automation skills and agents. It intentionally filters out navigation pages, duplicate pages, and `Helpjuice - 404` exports.

## Selection rules

- Prefer pages with explicit timing, ownership, review, checklist, or handoff guidance.
- Favor workflow pages that can support repeated runs with minimal human interpretation.
- Use the export JSON files as the local source of truth when a skill needs more detail.

## Workflow map

| Workflow | Primary source pages | Automation guidance |
| --- | --- | --- |
| End-to-end orchestration | `046-manage-processes-end-to-end-process.json`, `100-use-tools-and-systems-collaboration-and-other-proposal-automation-tools.json` | Run one stage-aware workflow at a time, keep outputs tied to the current pursuit stage, and avoid extra artifacts that do not help the next decision, review, or delivery step. |
| Opportunity and capture | `047-manage-processes-gate-decisions.json`, `058-use-tools-and-systems-opportunitycapture-and-proposal-management-scheduling.json`, `059-use-tools-and-systems-opportunitycapture-plan-development.json` | Use scheduled gate decisions, explicit action ownership, measurable tasks, realistic calendars, and probability-of-win thinking to advance or stop work. |
| Kickoff and proposal planning | `048-manage-processes-kickoff-meeting-management.json`, `060-use-tools-and-systems-proposal-management-plans.json`, `054-use-tools-and-systems-content-plans.json` | Do not kickoff immediately on receipt. Build planning materials first, then issue a kickoff packet with the schedule, outline, responsibilities, draft executive summary, and content-plan guidance. |
| Compliance and content design | `040-focus-on-the-customer-identifying-requirements-for-compliance-and-responsiveness.json`, `023-create-deliverables-compliance-matrix.json`, `054-use-tools-and-systems-content-plans.json` | Treat compliance as the planning baseline, shred requirements line by line, maintain a response matrix, and use annotated outlines and section plans before full drafting. |
| Review and readiness | `052-manage-processes-review-management.json`, `058-use-tools-and-systems-opportunitycapture-and-proposal-management-scheduling.json` | Plan reviews early, tie them to draft maturity, consolidate comments into actions, and preserve proofreading and production time rather than stealing it for more drafting. |
| Knowledge harvest and reuse | `049-manage-processes-lessons-learned-analysis-and-management.json`, `056-use-tools-and-systems-knowledge-management.json`, `100-use-tools-and-systems-collaboration-and-other-proposal-automation-tools.json` | Capture lessons immediately, turn observations into actions, harvest reusable objects in small chunks, and store them with enough structure to reuse later without rework. |
| SME extraction | `055-use-tools-and-systems-interviewing-subject-matter-experts.json`, `054-use-tools-and-systems-content-plans.json` | Prepare questions before asking for SME time, capture open-ended answers, summarize and validate quickly, then feed the results into section plans or proof points. |

## Core operating rules

### Stage discipline

- Align outputs to the current stage of the business development lifecycle.
- Use gate decisions to decide whether to advance, defer, or stop.
- Keep the pursuit moving from planning to execution; do not create plans with no follow-through.

### Parallel work

- Minimize sequential dependencies and maximize parallel assignments where possible.
- Assign one accountable owner per task, even when several people contribute.
- Keep schedules visible and stable. Change them only for real customer-driven or material internal reasons.

### Reviews

- Use the right review at the right time instead of defaulting to one generic review.
- Content development reviews are short operational checks; final document reviews emulate evaluators.
- Proofreading is not editing and should remain a distinct late-stage quality check.

### Reuse and knowledge management

- Store reusable knowledge as discrete objects rather than large undifferentiated documents.
- Track what was learned, what should change, and who owns the improvement.
- Favor structured templates, content standards, and searchable repositories over ad hoc memory.

## Pinned source pages

- `outputs/generated/apmp-helpjuice-export-2026-03-22/pages/023-create-deliverables-compliance-matrix.json`
- `outputs/generated/apmp-helpjuice-export-2026-03-22/pages/040-focus-on-the-customer-identifying-requirements-for-compliance-and-responsiveness.json`
- `outputs/generated/apmp-helpjuice-export-2026-03-22/pages/046-manage-processes-end-to-end-process.json`
- `outputs/generated/apmp-helpjuice-export-2026-03-22/pages/047-manage-processes-gate-decisions.json`
- `outputs/generated/apmp-helpjuice-export-2026-03-22/pages/048-manage-processes-kickoff-meeting-management.json`
- `outputs/generated/apmp-helpjuice-export-2026-03-22/pages/049-manage-processes-lessons-learned-analysis-and-management.json`
- `outputs/generated/apmp-helpjuice-export-2026-03-22/pages/052-manage-processes-review-management.json`
- `outputs/generated/apmp-helpjuice-export-2026-03-22/pages/054-use-tools-and-systems-content-plans.json`
- `outputs/generated/apmp-helpjuice-export-2026-03-22/pages/055-use-tools-and-systems-interviewing-subject-matter-experts.json`
- `outputs/generated/apmp-helpjuice-export-2026-03-22/pages/056-use-tools-and-systems-knowledge-management.json`
- `outputs/generated/apmp-helpjuice-export-2026-03-22/pages/058-use-tools-and-systems-opportunitycapture-and-proposal-management-scheduling.json`
- `outputs/generated/apmp-helpjuice-export-2026-03-22/pages/059-use-tools-and-systems-opportunitycapture-plan-development.json`
- `outputs/generated/apmp-helpjuice-export-2026-03-22/pages/060-use-tools-and-systems-proposal-management-plans.json`
- `outputs/generated/apmp-helpjuice-export-2026-03-22/pages/100-use-tools-and-systems-collaboration-and-other-proposal-automation-tools.json`

## How to use this map

- Start with the workflow row that matches the run objective.
- Read the listed export JSON pages only when the skill needs deeper detail.
- Prefer short, operator-ready outputs: action lists, schedules, matrices, packets, review logs, and harvested knowledge objects.
