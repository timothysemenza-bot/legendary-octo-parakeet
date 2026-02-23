# Outlook Email Automation (Personal Address)

This module lets your agent send outreach from your Outlook mailbox with human approval controls.

## Requirements

- Outlook desktop installed on this machine.
- Outlook signed in to your personal/business mailbox.
- Outlook running during send operations.
- Use **Classic Outlook** for automation (New Outlook does not support COM automation).

If COM is unavailable, use Graph API sender (recommended fallback).

## Files

- Queue: `marketing-agents/data/email_outbox_queue.csv`
- Pipeline: `marketing-agents/data/prospect_pipeline.csv`
- Interaction log: `marketing-agents/data/interaction_log.csv`

## Commands

1. Build queue rows from active pipeline records with known emails:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\build-email-queue-from-pipeline.ps1 -ScheduledDate 2026-02-23 -ScheduledTime 09:30 -OwnerApproved no -SendMode draft
```

Diagnostic check:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\test-outlook-automation.ps1
```

2. Approve rows for execution:
- Set `owner_approved=yes` for rows you want to process.
- Set `send_mode=draft` to create Outlook drafts first.
- Set `send_mode=send` to send immediately.

3. Execute approved rows via Outlook:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\send-outlook-email-batch.ps1
```

Optional specific sender account:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\send-outlook-email-batch.ps1 -FromAccount you@yourdomain.com
```

### Graph API fallback (works without Outlook COM)

```powershell
$env:GRAPH_ACCESS_TOKEN = "<token>"
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\send-outlook-email-batch-graph.ps1 -GraphAccessToken $env:GRAPH_ACCESS_TOKEN -FromUserPrincipalName you@yourdomain.com
```

Required Graph permissions:
- `Mail.Send`
- `Mail.ReadWrite` (if using draft mode via `/messages`)

### SMTP fallback (works with any SMTP-capable mailbox)

Use this when COM is broken and Graph token flow is not ready.

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\send-email-batch-smtp.ps1 `
  -SmtpHost smtp.office365.com `
  -SmtpPort 587 `
  -UseSsl $true `
  -SmtpUsername you@yourdomain.com `
  -SmtpPassword "<app-password-or-smtp-password>" `
  -FromAddress you@yourdomain.com
```

Notes:
- For Microsoft 365 tenants, SMTP AUTH must be enabled for the mailbox/tenant.
- For personal Microsoft accounts, use an app password if MFA is enabled.

### Personal Microsoft account quick-start (no Entra required)

1. Turn on 2-step verification for your Microsoft account.
2. Create an app password in account security.
3. Run guided sender:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\start-smtp-personal-email.ps1
```

This prompts for:
- your Microsoft email address
- app password

Then it sends all `owner_approved=yes` queued emails through SMTP and logs updates automatically.

## Business-Hours Policy (Default)

- Weekdays only: Monday-Friday
- Allowed window: `09:00-17:00`
- Outside this window, execution is blocked unless explicitly overridden.

## What Gets Updated Automatically

- `email_outbox_queue.csv`: status (`queued` -> `drafted` or `sent`) and timestamp
- `interaction_log.csv`: outbound email event logged per message
- `prospect_pipeline.csv`: touch dates and stage update

## Maximum Reliability Mode (Recommended Default)

Use Graph-first sending with retries and queue failure tracking.

1. Set token in environment:

```powershell
$env:GRAPH_ACCESS_TOKEN = "<token>"
```

2. Run reliable sender:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\run-email-reliable.ps1 -FromUserPrincipalName you@yourdomain.com
```

Reliability controls:
- auth preflight check (`/me` or `/users/{upn}`)
- retry with backoff (`MaxAttempts`, `RetryDelaySeconds`)
- queue-level `attempt_count` and `last_error` tracking
- terminal state after max retries: `failed-max-attempts`
