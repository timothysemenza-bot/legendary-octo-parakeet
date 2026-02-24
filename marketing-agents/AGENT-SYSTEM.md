# Boss Key Outbound Agent System

This system is designed for initial outreach to janitorial and facility service companies in Burlington County and South Jersey.

## Goal

Get first meetings by sending highly tailored, operationally grounded outreach that emphasizes:

- margin protection
- faster bid turnaround
- reduced administrative burden

Do not position Boss Key LLC as a generic AI consultancy.

## Agent Stack

1. `Agent 1: Account Research`
- Input: company name, website, service area, target contact.
- Output: operational context and likely pain points.

2. `Agent 2: Personalization Strategy`
- Input: Agent 1 findings.
- Output: message angle, hooks, proof points, and objection assumptions.

3. `Agent 3: Outreach Writer`
- Input: Agent 2 strategy.
- Output: tailored email, LinkedIn connection note, LinkedIn follow-up, cold call opener.

4. `Agent 4: Campaign QA + Tracker`
- Input: draft messages and prospect data.
- Output: quality score, rewrite suggestions, final copy, and next-touch plan.

5. `Agent 5: LinkedIn Operator (Human Approval Required)`
- Input: weekly content goals, relationship priorities, inbox exports, and campaign context.
- Output: post drafts, comment/reply drafts, approval packet, and relationship alerts.
- Rule: never post directly without explicit owner approval.

6. `Agent 6: Prospect Scout`
- Input: target geography, company-size filters, and ICP rules.
- Output: ranked prospect candidates with reasons, contacts, and next action.

7. `Agent 7: Call Planner + Relationship Memory`
- Input: active pipeline, interaction logs, and calendar limits.
- Output: daily call schedule, follow-up queue, and updated engagement memory.

8. `Agent 8: Public Bid Scout`
- Input: geography, NAICS/keywords, and client capability profile.
- Output: prioritized janitorial/facility contract opportunities.

9. `Agent 9: Transcript-to-Requirements Mapper`
- Input: meeting transcripts and client direction.
- Output: reusable capability statements, constraints, and proposal inputs.

10. `Agent 10: Proposal Draft Builder`
- Input: RFP package, compliance matrix, and mapped client inputs.
- Output: first draft technical proposal with evidence-backed claims.

11. `Agent 11: Compliance QA + Submission Pack`
- Input: draft proposal and solicitation requirements.
- Output: pass/fail compliance review, redline fixes, and submission checklist.

12. `Agent 12: Call Execution Agent (Integration-Ready)`
- Input: approved call queue, call scripts, dialing window, and logging rules.
- Output: dial-ready batch, per-call script prompts, real-time note capture, and automatic CRM updates.
- Rule: require explicit owner authorization for each outbound call batch.

13. `Agent 13: Outlook Email Execution Agent`
- Input: approved email queue, send window, sender account, and tracking rules.
- Output: draft/send actions through Outlook, send logs, and CRM updates.
- Rule: send only records explicitly marked `owner_approved=yes`.

14. `Agent 14: Burlington Public Digital Capture Agent`
- Input: Burlington-area procurement sources, recompete timing signals, and service focus (web/digital/IT-adjacent modernization).
- Output: ranked pre-RFP government target list, seeded opportunity rows, and seeded pipeline rows for proactive outreach.
- Rule: prioritize near-term recompetes and named office contacts.

## Standard Workflow

1. Fill one row in `marketing-agents/data/prospect_pipeline.csv`.
2. Run Agent 1 prompt.
3. Run Agent 2 prompt.
4. Run Agent 3 prompt.
5. Run Agent 4 prompt before sending.
6. Log outcome and next step in the CSV.
7. Use Agent 5 for LinkedIn content queue + inbox triage + approval workflow.
8. Use Agent 6 to refresh prospect targets each day/week.
9. Use Agent 7 + scripts to generate call plans and update interaction memory automatically.
10. Use Agent 8 to identify public-sector bid targets.
11. Use Agent 9 to convert client transcripts into proposal-ready guidance.
12. Use Agent 10 to create tailored draft proposals.
13. Use Agent 11 to validate compliance before submission.
14. Use Agent 12 to execute approved call batches and auto-log outcomes.
15. Use Agent 13 to send approved outreach emails from Outlook and auto-log outcomes.
16. Use Agent 14 to run a weekly Burlington public digital recompete scan and refresh pre-RFP capture priorities.
17. Generate GO/NO-GO memos for `pursue_now` accounts before outreach using `marketing-agents/scripts/generate-public-go-no-go-memos.ps1`.

## Quality Bar

Every outreach asset must:

- reference at least one prospect-specific fact
- use practical language for owner/operators
- include measurable outcomes
- avoid buzzwords and hype
- end with a clear low-friction CTA
- if channel is LinkedIn, require owner approval before publish
- all interactions must be logged and retained in the CRM files
- proposals must be owner-reviewed before external submission
- outbound call batches require owner approval and local legal/compliance checks
- outbound emails require owner approval and must run inside business-hour policy unless overridden
