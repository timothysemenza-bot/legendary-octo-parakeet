# Gmail Manual Send Workflow (Write-Only Automation)

Use this flow when Boss Key automates writing and you send emails manually from Gmail.

## 1) Generate tailored email drafts from pipeline

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\build-email-queue-from-pipeline.ps1 -ScheduledDate 2026-02-23 -ScheduledTime 09:30 -OwnerApproved yes -SendMode draft
```

## 2) Export Gmail-ready send sheet

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\export-gmail-send-sheet.ps1
```

Output file:
- `marketing-agents/data/gmail_send_sheet.csv`

## 3) Send manually from Gmail

- Open `gmail_send_sheet.csv`
- Copy `to_email`, `subject`, and `body_text` into Gmail compose
- Send

## 4) Mark sent and sync CRM memory

After sending, update those queue rows from `queued` to `sent` in:
- `marketing-agents/data/email_outbox_queue.csv`

Then run:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\sync-interactions-to-pipeline.ps1
```
