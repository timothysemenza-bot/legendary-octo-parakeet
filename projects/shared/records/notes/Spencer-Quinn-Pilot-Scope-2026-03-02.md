# Boss Key Pilot Scope (Draft)
Client: Spencer Quinn team  
Date: March 2, 2026  
Pilot type: Transcript-to-CRM Compliance Automation

## Pilot Goal
Reduce CRM non-compliance by converting sales call transcripts into structured CRM updates and immediate next-step tasks.

## Problem This Solves
- Sales reps complete calls but do not consistently update CRM records.
- Sales leadership lacks reliable, current activity data for coaching and forecasting.
- Manual follow-up logging creates avoidable admin drag.

## Pilot Scope (2 Weeks)
1. Ingest call transcript text from recorded discovery calls.
2. Parse and map key fields:
- account/company
- contact/persona
- pain points
- buying signals
- objections
- agreed next step
- follow-up date
3. Generate a structured CRM-ready update object for each call.
4. Generate a manager summary email per call (or daily digest).
5. Create an auditable activity log for QA and refinement.

## Out Of Scope (Pilot)
- Full CRM migration
- End-to-end outbound sequencing build
- Legal/compliance policy redesign
- Multi-department workflow redesign beyond sales activity capture

## Deliverables
1. Pilot workflow map (input -> parse -> update -> review).
2. Working transcript-to-CRM mapping template.
3. Manager summary format (single call + daily digest variant).
4. QA log with detected gaps and refinement notes.
5. Pilot readout with recommendation: scale, revise, or stop.

## Success Metrics
- CRM completion rate on pilot calls (target: +40% or better vs baseline)
- Average time from call end to CRM update (target: under 15 minutes)
- Manual admin time per rep per call (target reduction: 30%+)
- Manager confidence score on update quality (simple 1-5 rubric)

## Required Inputs From Client
1. Sample call transcripts (minimum 10, preferred 20+).
2. CRM field list and required data schema.
3. One sales manager point-of-contact for quality review.
4. Access method decision:
- API push, or
- email/drop-file handoff for manual import in pilot phase.

## Implementation Plan
### Week 1
1. Confirm schema and required fields.
2. Build first-pass extraction and mapping logic.
3. Run on historical transcripts and review quality.

### Week 2
1. Process live calls daily.
2. Tune extraction accuracy from manager feedback.
3. Final readout and recommendation for rollout.

## Commercial Frame (Pilot Option)
- Fixed pilot fee: `$5,500` (aligned to your 6-week sprint packaging logic but condensed for a 2-week proof phase if desired).
- Alternative structure: apply pilot fee as credit toward a 3-month monthly retainer at `$6,000/month`.

## Decision Checkpoint
At end of week 2, decide one:
1. Scale to broader sales team with weekly optimization loop.
2. Continue as manager-only support workflow.
3. Pause and document lessons learned.

