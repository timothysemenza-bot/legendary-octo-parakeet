# New Outlook Draft Workflow

Use this flow to create drafts directly in **New Outlook** (no COM, no send).

## One command

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\run-new-outlook-draft-cycle.ps1 -ApplyReviewDecisions -IgnoreBusinessHours
```

What it does:

1. Applies `email_review_decisions.csv` to queue (optional via `-ApplyReviewDecisions`)
2. Authenticates with Microsoft Graph using device code
3. Creates drafts only (`ForceDraft`) from approved queue rows

## Where drafts appear

- New Outlook -> `Drafts`

## Notes

- Defaults to personal Microsoft account auth (`TenantId=consumers`)
- Default client app id: Azure CLI public client
- If needed, set sender mailbox explicitly:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\run-new-outlook-draft-cycle.ps1 -FromUserPrincipalName "you@outlook.com" -ApplyReviewDecisions -IgnoreBusinessHours
```
