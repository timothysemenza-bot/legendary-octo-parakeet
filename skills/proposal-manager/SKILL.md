---
name: proposal-manager
description: Lead compliant proposal execution from solicitation intake through submission and lessons learned. Use when Codex needs to review an RFP, RFQ, grant, or draft solicitation; translate capture or win strategy into a proposal plan; build compliance-aware outlines, schedules, kickoff packs, and data calls; manage Pink/Red/Gold reviews; control drafts, comments, and approvals; or prepare the final submission checklist and handoff package.
---

# Proposal Manager

Lead the proposal process with schedule discipline, compliance control, and clean handoffs from capture to submission. Keep outputs operator-ready: assignable, reviewable, and ready to drop into project management or document workflows.

## Workflow

1. Confirm pursuit context.
- Capture the solicitation type, customer, deadline, submission channel, volumes, evaluation criteria, incumbent situation, teammates, pricing dependencies, and required forms.
- If the user provides only a role brief or operating need, build a reusable proposal-management operating model instead of a bid-specific package.
- Read [references/proposal-lifecycle.md](references/proposal-lifecycle.md) when you need standard intake fields, stage gates, or artifact expectations.

2. Build the management package.
- Create the control set: intake summary, compliance matrix starter, annotated outline, page allocation, author roster, proposal calendar, review agenda, data-call list, and submission checklist.
- Run `scripts/generate-proposal-workplan.ps1` when the user needs a kickoff packet or a backward schedule anchored to a due date.
- Keep assumptions explicit and label placeholders rather than inventing facts.

3. Transfer win strategy into content planning.
- Convert capture notes into 3 to 5 response themes, proof points, discriminators, and customer outcomes.
- Tie every major section to evaluation criteria, strengths, and evidence sources.
- Flag where pricing, staffing, past performance, resumes, graphics, or certifications could break the schedule.

4. Manage reviews and revisions.
- Use Pink to test structure and message, Red to test evaluator readiness, and Gold to test production readiness.
- Read [references/review-and-submission-controls.md](references/review-and-submission-controls.md) for exit criteria, configuration control, and escalation rules.
- Convert reviewer feedback into an issue log with owner, disposition, due date, and reopen criteria.

5. Control production and submission.
- Freeze approved content, verify forms and attachments, confirm approvals, and prepare the final submission checklist.
- Surface submission risks early: portal access, file naming, size limits, signatures, pricing mismatches, and timezone mistakes.
- Finish with a lessons-learned log when the user needs a repeatable process, not just a one-off deliverable.

## Output Standard

- Prefer brief operational deliverables over narrative explanation.
- Default to tables, checklists, and owner/date trackers when the user needs something actionable.
- Separate confirmed facts, working assumptions, and open questions.
- If the source solicitation is incomplete, state the missing inputs and still provide the best-available draft package.

## Script

```powershell
& .\skills\proposal-manager\scripts\generate-proposal-workplan.ps1 `
  -OpportunityName "SBM Facilities Support Services" `
  -Customer "State Agency" `
  -DueDate "2026-04-15 14:00" `
  -ResponseType "RFP" `
  -SubmissionMethod "Procurement portal" `
  -Writers "Technical Lead, Past Performance Lead" `
  -ReviewLead "Proposal Manager" `
  -PricingLead "Finance Lead" `
  -ProductionLead "Operations Lead" `
  -OutputPath ".\proposal-workplan.md"
```

For historical bids or lessons-learned reviews, add `-AllowPastDueDate`.
