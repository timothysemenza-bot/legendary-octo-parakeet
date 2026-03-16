# Aircall Capture Notes

## Current Model

The old local Operator Console webhook flow has been retired.

Aircall activity should now enter the company OS through file capture:

1. Save notes, transcripts, or exports from Aircall into a watched source folder.
2. Run `marketing-agents/scripts/auto-call-intake-agent.ps1`.
3. The script converts the call into a structured capture in `marketing-agents/data/engagement-inbox/call-intake/`.
4. The company OS intake runner turns that capture into signals, engagements, actions, timelines, and approvals.

## Recommended Command

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\auto-call-intake-agent.ps1 -BusinessHoursOnly -BusinessStart 08:30 -BusinessEnd 17:30
```

## Source Folder Setup

Configure transcript/export folders in:

- `marketing-agents/data/call-capture/source-folders.txt`

Each line should be one absolute folder path where Aircall or related tooling drops transcripts, notes, or recordings.

## Supported Inputs

- `.txt`
- `.md`
- `.json`
- `.srt`
- `.wav`
- `.mp3`
- `.m4a`
- `.aac`
- `.mp4`
- `.wma`

Audio/video files need local transcription installed. The script tries:

1. Python `faster-whisper`
2. `whisper` CLI

## Output Path

The company OS captures land in:

- `marketing-agents/data/engagement-inbox/call-intake/`

They are then processed into:

- `marketing-agents/data/communication_signal_log.csv`
- `marketing-agents/data/engagement_register.csv`
- `marketing-agents/data/engagement_timeline.csv`
- `marketing-agents/data/action_workbench.csv`
- `marketing-agents/data/approval_router_queue.csv`
- `marketing-agents/data/meeting_follow_through.csv`

## Important

- No local webhook server is required anymore.
- No `localhost:3201` dependency remains in the supported Aircall flow.
- If you want immediate OS updates after each capture, do not pass `-SkipEngagementIntake`.
