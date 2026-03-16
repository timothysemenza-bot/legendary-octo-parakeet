# Auto Call Intake and Transcription

This gives you an always-on intake path for call recordings and transcript files so action items can flow into your existing Boss Key workflow.

It is designed to work even when transcripts come from different tools (Copilot, Gemini, call platform exports), as long as files land in one folder.

## What it does

Script:
- `marketing-agents/scripts/auto-call-intake-agent.ps1`
- `marketing-agents/scripts/install-transcription-engine.ps1`
- `marketing-agents/scripts/setup-auto-call-intake-task.ps1`

Workflow:
1. Syncs files from configured source folders into `marketing-agents/data/call-capture/inbox`.
2. Ingests transcript files directly (`.txt`, `.md`, `.json`, `.srt`).
3. Attempts local transcription for audio files (`.wav`, `.mp3`, `.m4a`, `.aac`, `.mp4`, `.wma`).
4. Extracts action-item style summary and outcome.
5. Writes a structured capture into `marketing-agents/data/engagement-inbox/call-intake/`.
6. Runs the company OS engagement intake so the call becomes a signal, engagement, action set, and approval item.
7. Writes processing logs and moves files to `processed` or `failed`.

## Important practical constraint

This cannot magically capture calls from every app without that app producing a recording/transcript file.

To get full automation:
- set your dialer/meeting tools to auto-save recordings or transcript exports
- configure source folders in `marketing-agents/data/call-capture/source-folders.txt`

## Start command

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\auto-call-intake-agent.ps1 -BusinessHoursOnly
```

## Configure source folders

The first run creates:
- `marketing-agents/data/call-capture/source-folders.txt`

Edit that file to include all export directories for Aircall/Teams/Zoom/Gemini/Copilot transcript dumps.

## Recommended runtime

Run the auto intake agent directly:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\auto-call-intake-agent.ps1 -BusinessHoursOnly -BusinessStart 08:30 -BusinessEnd 17:30
```

If you want it to capture files but defer OS processing until later, add:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\auto-call-intake-agent.ps1 -SkipEngagementIntake
```

## File naming convention (optional but useful)

Use:

`Company__Contact__Phone.ext`

Example:

`Delta_Cleaning__Tom_Richter__12035551212.txt`

This improves matching quality for automatic logging.

## Output files

- Ingest log: `marketing-agents/data/call_capture_ingest_log.csv`
- Pending queue (when capture write fails): `marketing-agents/data/call_capture_pending_ingest.csv`
- Processed files: `marketing-agents/data/call-capture/processed`
- Failed files: `marketing-agents/data/call-capture/failed`
- Company OS call captures: `marketing-agents/data/engagement-inbox/call-intake/`

## Local transcription options

The script tries:
1. Python `faster-whisper`
2. `whisper` CLI

If neither is installed, audio files are marked failed with a note.

Transcript text files still ingest without STT.

Install `faster-whisper` automatically:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\install-transcription-engine.ps1 -Engine faster-whisper
```

## Weekday auto-start task

Create task:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\setup-auto-call-intake-task.ps1 -TaskName "BossKey-Auto-Call-Intake" -Time "08:35"
```

## Daily brief integration

Your daily brief already includes inbound and action focus areas.
Call captures from this intake path flow into the company OS files:
- `communication_signal_log.csv`
- `engagement_register.csv`
- `engagement_timeline.csv`
- `action_workbench.csv`
- `approval_router_queue.csv`
- `meeting_follow_through.csv`

Then the normal brief job summarizes priorities.
