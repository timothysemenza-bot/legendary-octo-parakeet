# Email Automation with Approval Gate

This workflow lets agents generate outreach automatically while keeping you in control of final send.

## Flow

1. Generate draft queue + review files:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\run-email-review-cycle.ps1 -ScheduledDate 2026-02-23 -ScheduledTime 09:30
```

2. Review/edit in:
- `marketing-agents/data/email_review_decisions.csv`
- Set `decision` per row: `approve`, `hold`, or `reject`
- Optional edits:
  - `revised_subject`
  - `revised_body`
  - `send_mode` (`send` or `draft`)

3. Apply decisions:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\apply-email-review-decisions.ps1
```

4. Send only approved rows:
- SMTP path:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\send-email-batch-smtp.ps1 -SmtpHost smtp-mail.outlook.com -SmtpPort 587 -UseSsl $true -SmtpUsername you@outlook.com -SmtpPassword "<app-password>" -FromAddress you@outlook.com
```

- or Graph path:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\run-email-reliable.ps1 -FromUserPrincipalName you@yourdomain.com
```

## Result

- Agent does draft generation automatically.
- You review and edit quickly in one decisions file.
- Only explicitly approved emails are sent.
