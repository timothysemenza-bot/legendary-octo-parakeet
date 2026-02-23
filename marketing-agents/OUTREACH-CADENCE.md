# Outreach Cadence System

Use this to keep a steady follow-up rhythm for prospects who do not respond to first touch.

## Generate Plan

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\generate-email-followup-cadence.ps1 -StartDate 2026-02-23
```

Output:
- `marketing-agents/data/outreach_touch_plan.csv`

## Cadence Map

1. Day 0: initial email (`E1`)
2. Day 3: call + voicemail (`C1`)
3. Day 7: value follow-up email (`E2`)
4. Day 12: low-friction follow-up (`E3`)
5. Day 21: LinkedIn/text reconnect (`L1`)
6. Day 35: monthly nurture email (`E4`)

Templates:
- `marketing-agents/templates/outreach-cadence-templates.md`

## Daily Execution

1. Filter `outreach_touch_plan.csv` for today's date.
2. Execute touches by channel.
3. Log outcomes in `interaction_log.csv`.
4. Update stage/next touch using:

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\sync-interactions-to-pipeline.ps1
```

## Signature Files

- HTML: `marketing-agents/templates/email-signature-boss-key.html`
- Plain text: `marketing-agents/templates/email-signature-boss-key.txt`
