# LinkedIn Warm Path Mapping

Use this workflow to map your LinkedIn connections against current public capture targets so outreach can start with warm introductions.

## 1) Export LinkedIn connections

From LinkedIn:
- Settings & Privacy
- Data privacy
- Get a copy of your data
- Request `Connections`
- Download CSV and save as:
`marketing-agents/data/linkedin_connections.csv`

## 2) Run the matcher

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\map-linkedin-warm-paths.ps1
```

## 3) Review outputs

- Match CSV:
`marketing-agents/data/linkedin_warm_paths.csv`
- Summary brief:
`marketing-agents/briefs/generated/public-capture/linkedin-warm-paths.md`

## 4) Use in outreach

For each `pursue_now` account:
1. Prefer warm intros with highest `warm_path_score`.
2. Ask the connection for a simple intro email to the target office contact.
3. Reference local community commitment and request an in-person introductory meeting.
