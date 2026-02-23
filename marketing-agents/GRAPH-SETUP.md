# Graph Setup (Reliable Email Sending)

Use this when Outlook COM is unavailable.

## 1) Azure App Registration

Create an app registration in your Microsoft tenant:

- Platform: public client/native
- Permissions (delegated):
  - `Mail.Send`
  - `Mail.ReadWrite`
  - `offline_access`
- Grant admin consent if tenant policy requires it.

## 2) Acquire token (device code)

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\get-graph-token-devicecode.ps1 -TenantId "<tenant-id>" -ClientId "<app-client-id>"
```

This sets `GRAPH_ACCESS_TOKEN` in your current PowerShell session.

## 3) Run reliable sender

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\run-email-reliable.ps1 -FromUserPrincipalName you@yourdomain.com
```

## 4) Queue discipline

- `owner_approved=yes` required to process
- `send_mode=send` sends immediately
- `send_mode=draft` creates draft message records

## 5) Reliability behavior

- auth preflight before queue processing
- retry with backoff
- per-row `attempt_count` and `last_error`
- terminal state at max retries: `failed-max-attempts`
