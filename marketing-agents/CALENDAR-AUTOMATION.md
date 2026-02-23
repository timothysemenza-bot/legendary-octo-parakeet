# Calendar Automation

This workflow auto-fits your prospect calls into open slots and generates calendar events each morning.

## What it does

- reads `marketing-agents/data/daily_call_plan.csv`
- checks your busy blocks from:
- `marketing-agents/data/busy_blocks.csv` (manual blocks), and/or
- a private ICS calendar feed URL/file
- creates `marketing-agents/data/daily_call_plan_adaptive.csv`
- creates `marketing-agents/briefs/daily-call-plan.ics`
- creates outcome-driven follow-up events in:
- `marketing-agents/data/follow_up_events.csv`
- `marketing-agents/briefs/follow-up-events.ics`

## Run once (manual test)

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\build-adaptive-call-calendar.ps1 -Date 2026-02-23 -OpenCalendar
```

## Use with your morning automation

Your existing daily task now runs this automatically through:

- `marketing-agents/scripts/run-daily-brief-job.ps1`

If you have a private ICS URL (Google/Outlook publish link), re-register task with it:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\setup-daily-brief-task.ps1 -TaskName "BossKey-Daily-Brief" -Time "08:00" -BusyIcsUrl "<YOUR_PRIVATE_ICS_URL>" -OpenBrief
```

When `-BusyIcsUrl` is provided, the morning job now imports that calendar into:

- `marketing-agents/data/busy_blocks.csv`

using:

- `marketing-agents/scripts/sync-google-calendar-busy-blocks.ps1`

## One-time Google Calendar import

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\sync-google-calendar-busy-blocks.ps1 -IcsUrl "<YOUR_PRIVATE_ICS_URL>"
```

Optional horizon controls:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\sync-google-calendar-busy-blocks.ps1 -IcsUrl "<YOUR_PRIVATE_ICS_URL>" -DaysBack 1 -DaysAhead 30
```

## Busy block format (manual fallback)

`marketing-agents/data/busy_blocks.csv`

```csv
"start","end","title"
"2026-02-23 11:00","2026-02-23 11:30","Client check-in"
"2026-02-23 13:00","2026-02-23 14:00","On-site walkthrough"
```

## Recommended setup

1. Keep the scheduled task at 8:00 AM weekdays.
2. Add your non-negotiable meetings to `busy_blocks.csv` or connect ICS URL.
3. Open `marketing-agents/briefs/daily-call-plan.ics` to import/update your calendar events.
4. Import `marketing-agents/briefs/follow-up-events.ics` for automatic +2/+7 (or outcome-based) follow-up reminders.
