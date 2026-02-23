# New Outlook Simple Mode (No Graph / No COM)

This is the easiest workflow:

- Opens prefilled compose windows in **New Outlook**
- You review/edit/send manually
- No API auth setup needed

## Run now

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\open-new-outlook-review-drafts.ps1 -IgnoreBusinessHours -MaxToOpen 5
```

## Daily automation

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\setup-daily-new-outlook-draft-task.ps1 -Time "08:45" -MaxToOpen 5
```

This creates scheduled task:

- `BossKey-NewOutlook-DraftReview`

## Notes

- It opens only approved queue rows (`owner_approved=yes`) that are due.
- Queue status updates to `opened-for-review`.
- Your final send decision remains manual in New Outlook.
