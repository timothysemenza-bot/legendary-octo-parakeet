# Operator Console App

This gives you an app-style workflow so you do not have to run scripts manually.

## Start the app

```powershell
npm run start:operator
```

Open:

- `http://localhost:3201`
- `http://localhost:3201/company-os.html`

## What it does

- Runs morning refresh from a button
- Shows queue status and next call
- Starts next call in queue
- Launches Aircall through your `tel:` default handler
- Logs call outcomes
- Supports Aircall auto-ingest from notes/transcript into cadence tracking
- Runs engagement intake across approved communication sources
- Shows the latest engagement intake summary inside the main dashboard
- Includes a `Company OS` view for the full Boss Key operating agent stack
- Updates:
- `marketing-agents/data/interaction_log.csv`
- `marketing-agents/data/prospect_pipeline.csv`
- `marketing-agents/data/follow_up_events.csv`
- `marketing-agents/briefs/follow-up-events.ics`
- `marketing-agents/data/communication_signal_log.csv`
- `marketing-agents/data/engagement_register.csv`
- `marketing-agents/data/engagement_timeline.csv`
- `marketing-agents/data/stakeholder_map.csv`
- `marketing-agents/data/action_workbench.csv`
- `marketing-agents/data/approval_router_queue.csv`
- `marketing-agents/data/meeting_follow_through.csv`
- `marketing-agents/data/engagement_intake_summary.json`
- `marketing-agents/briefs/engagement-intake-latest.md`

## Daily usage

1. Click `Run Morning Refresh`
2. Click `Start Next Call`
3. Click `Launch Aircall`
4. After call, fill outcome and click `Save Outcome`
5. Repeat
6. Optional: use `Aircall Auto Log` panel to paste transcript/notes and auto-log
7. Optional: click `Run Engagement Intake` to pull approved transcripts, interaction logs, and inbox exports into the shared OS
