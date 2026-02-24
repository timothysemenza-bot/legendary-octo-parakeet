# Photoshop Agent (Local Batch Automation)

This gives you a simple agent workflow to run repeatable Photoshop edits from a queue.

## What it does

- Queues image jobs in `marketing-agents/data/photoshop_jobs.csv`
- Runs jobs through Photoshop scripting (COM + JSX) on Windows
- Produces optimized web outputs for your site/social assets

## Job types currently supported

- `resize_jpg`
- `headshot_web` (long edge 1200, JPG quality 10)
- `headshot_mobile` (long edge 600, JPG quality 9)

## Add a job

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\new-photoshop-job.ps1 `
  -SourcePath ".\boss-key-website\assets\headshots\timothy-semenza-headshot.jpg" `
  -OutputPath ".\boss-key-website\assets\headshots\timothy-semenza-headshot-web.jpg" `
  -JobType headshot_web
```

## Run the agent

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\run-photoshop-agent.ps1
```

## Notes

- Photoshop must be installed and licensed.
- This uses Photoshop COM automation. If COM is unavailable, the script will fail cleanly and keep jobs as `queued`.
- You can re-run safely; completed jobs are skipped.
