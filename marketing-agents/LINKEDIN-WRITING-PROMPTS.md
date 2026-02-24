# LinkedIn Writing Prompt Workflow

This replaces AI-written post drafts with a daily prompt so ideas come from you.

## Generate today’s prompt

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\generate-daily-linkedin-writing-prompt.ps1 -OpenInNotepad
```

Output file:
- `marketing-agents/briefs/linkedin-writing-prompt-YYYY-MM-DD.md`

## Run as part of daily cadence

`run-daily-marketing.ps1` now includes the writing-prompt step and opens it in Notepad.

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\run-daily-marketing.ps1
```

## How rotation works

- Monday -> Prompt 1 (Launch)
- Tuesday -> Prompt 2 (Proof)
- Wednesday -> Prompt 3 (Tactical)
- Thursday -> Prompt 4 (Case)
- Friday -> Prompt 5 (Founder POV)
- Saturday -> Prompt 6 (Fit)
- Sunday -> Prompt 1

Cadence source:
- `marketing-agents/data/linkedin_writing_cadence.csv`
