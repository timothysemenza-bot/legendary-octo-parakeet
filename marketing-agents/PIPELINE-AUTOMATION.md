# Prospecting and Call Automation

This workflow keeps prospecting, call planning, and engagement memory updated with minimal admin time.

## Files

- Prospect candidates: `marketing-agents/data/prospect_candidates.csv`
- Active pipeline: `marketing-agents/data/prospect_pipeline.csv`
- Interaction memory: `marketing-agents/data/interaction_log.csv`
- Daily call sheet: `marketing-agents/data/daily_call_plan.csv`

## Agents

- Prospect scanning: `marketing-agents/prompts/06_prospect_scout.md`
- Call schedule + memory: `marketing-agents/prompts/07_call_planner_memory.md`

## Automation Scripts

1. Sync interactions into pipeline:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\sync-interactions-to-pipeline.ps1
```

2. Generate daily call plan:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\generate-daily-call-plan.ps1 -CallCount 12 -StartTime 09:00
```

3. Run end-to-end daily flow:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\run-daily-marketing.ps1 -CallDate 2026-02-23 -CallCount 8
```

## Recommended Daily Sequence (10-15 min admin)

1. Add any new messages/calls/emails to `interaction_log.csv`.
2. Run sync script to update `prospect_pipeline.csv` automatically.
3. Run call-plan script to create today's schedule.
4. Run Agent 7 to produce briefing notes and follow-up priorities.
5. Execute calls and community meetings.

## Interaction Logging Standard

For each touch, log:

- date
- company + person
- channel (call/email/linkedin/in-person)
- summary
- outcome
- next action and next touch date

This retains long-term relationship memory so outreach context is not lost.
