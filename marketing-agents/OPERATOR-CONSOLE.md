# Operator Console App

This gives you an app-style workflow so you do not have to run scripts manually.

## Start the app

```powershell
npm run start:operator
```

Open:

- `http://localhost:3201`

## What it does

- Runs morning refresh from a button
- Shows queue status and next call
- Starts next call in queue
- Launches Aircall through your `tel:` default handler
- Logs call outcomes
- Supports Aircall auto-ingest from notes/transcript into cadence tracking
- Updates:
- `marketing-agents/data/interaction_log.csv`
- `marketing-agents/data/prospect_pipeline.csv`
- `marketing-agents/data/follow_up_events.csv`
- `marketing-agents/briefs/follow-up-events.ics`

## Daily usage

1. Click `Run Morning Refresh`
2. Click `Start Next Call`
3. Click `Launch Aircall`
4. After call, fill outcome and click `Save Outcome`
5. Repeat
6. Optional: use `Aircall Auto Log` panel to paste transcript/notes and auto-log
