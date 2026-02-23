# Aircall Automation Notes

## Recording

Call recording is controlled in Aircall admin/workspace settings, not in this app.

Enable recording inside Aircall, then use one of these paths to log outcomes into Boss Key:

1. Paste notes/transcript into `Aircall Auto Log` panel in the Operator Console.
2. Send JSON into `POST /api/aircall-ingest` from an automation tool.
3. Use Aircall webhooks into `POST /api/aircall-webhook` for direct automatic logging.

## API payload for auto-log

`POST http://localhost:3201/api/aircall-ingest`

```json
{
  "company_name": "Delta Cleaning Service",
  "contact_name": "Tom Richter",
  "phone": "+1 609-265-8044",
  "notes": "Left voicemail with specific margin angle.",
  "transcript": "",
  "outcome": "voicemail",
  "next_action": "Follow up in two days",
  "next_touch_date": "2026-02-25",
  "interaction_id": "aircall-12345"
}
```

If `outcome` is omitted, the app infers it from notes/transcript text.

## Aircall Webhook Endpoint

- URL: `POST http://localhost:3201/api/aircall-webhook`
- Recommended auth:
- Header token: set env `AIRCALL_WEBHOOK_TOKEN` and send `x-webhook-token`
- HMAC signature: set env `AIRCALL_WEBHOOK_SECRET` and send `x-aircall-signature`

Supported payload fields are flexible. The adapter auto-maps common fields:

- IDs: `id`, `call_id`, `data.call_id`, `sid`
- Company/contact: `company_name`, `contact.name`, `contact.company_name`
- Phone: `phone`, `number`, `to`, `from`, `contact.phone_number`
- Notes/transcript: `notes`, `summary`, `comment`, `transcript`
- Outcome hints: `outcome`, `disposition`, `status`, `event`, `type`

If not provided, the adapter infers outcome from note/transcript text.

## Public tunnel (so Aircall can reach your local app)

Start secure tunnel + token:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\start-aircall-webhook-tunnel.ps1
```

This command will:

- start/restart Operator Console on `localhost:3201`
- create/store `AIRCALL_WEBHOOK_TOKEN` in `marketing-agents/.env.local`
- start Cloudflare tunnel
- print your public webhook URL and required header

Stop tunnel:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\stop-aircall-webhook-tunnel.ps1
```

## Important

- `localhost` endpoints only work on your machine unless you expose them through a secure tunnel.
- Follow-up events are auto-created in:
- `marketing-agents/data/follow_up_events.csv`
- `marketing-agents/briefs/follow-up-events.ics`
