# Call Automation (Owner-Approved Batches)

This module automates call operations management, pre-call briefing, and queue-based dialing.

## Files

- Batch queue: `marketing-agents/data/call_batch_queue.csv`
- Call plan: `marketing-agents/data/daily_call_plan.csv`
- Interaction memory: `marketing-agents/data/interaction_log.csv`
- Pipeline: `marketing-agents/data/prospect_pipeline.csv`
- Queue state: `marketing-agents/data/call_session_state.json`
- Runbook brief: `marketing-agents/briefs/call-runbook.md`
- Research pack: `marketing-agents/briefs/prospect-research-pack.md`
- Follow-up events store: `marketing-agents/data/follow_up_events.csv`
- Follow-up calendar feed: `marketing-agents/briefs/follow-up-events.ics`

## Commands

1. Create a batch from today's call plan:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\create-call-batch.ps1 -BatchId batch-20260223-a -DialerProvider manual -OwnerApproved yes
```

2. Execute (or prepare outside calling window):

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\execute-call-batch.ps1 -BatchId batch-20260223-a
```

3. Generate the call runbook and research pack for today's calls:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\generate-call-runbook.ps1
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\generate-prospect-research-pack.ps1
```

4. Run calls one-by-one with auto-advance:

```powershell
# first run each day
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\run-next-call.ps1 -Reset -DialMode tel

# each next call
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\run-next-call.ps1 -DialMode tel

# if needed, log last call without opening another dial
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\run-next-call.ps1 -LogOnly

# non-interactive mode (skip outcome prompts)
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\run-next-call.ps1 -NoPrompt -DialMode none

# optional: disable automatic +2/+7 follow-up event creation
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\run-next-call.ps1 -DisableAutoFollowUps
```

5. Install a desktop dialer app (optional):

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\install-dialer-app.ps1 -Provider aircall-workspace
```

## Business-Hours Policy (Default)

- Weekdays only: Monday-Friday
- Allowed window: `09:00-17:00` (local machine time)
- Batches outside this window are blocked at creation/execution.

Optional override window:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\create-call-batch.ps1 -BatchId batch-20260223-b -OwnerApproved yes -BusinessStart 08:30 -BusinessEnd 17:30
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\execute-call-batch.ps1 -BatchId batch-20260223-b -BusinessStart 08:30 -BusinessEnd 17:30
```

## What It Automates

- validates owner approval
- validates dialing window
- logs each planned call into `interaction_log.csv`
- updates batch status in `call_batch_queue.csv`
- advances pipeline stage from `new` to `outreach-sent` where applicable
- generates a per-prospect runbook for same-day call windows
- generates a research pack with fast owner/local context links
- routes you into the next call via `tel:` (default Windows calling app) or Google Voice web mode
- prompts post-call outcome logging before moving to the next call
- writes outcomes to `interaction_log.csv` and updates stage/status/next touch in `prospect_pipeline.csv`
- creates follow-up calendar events by outcome (default offsets):
- `connected/voicemail/no-answer`: +2 and +7 days
- `meeting-booked`: +1 and +7 days
- `not-now`: +7 and +14 days

## Current Boundary

- You still control live conversation and disposition outcomes.
- For full power-dialer logic (auto-skip voicemail rules, call recordings, analytics), use a dialer subscription and keep this workflow as your prospecting control plane.
