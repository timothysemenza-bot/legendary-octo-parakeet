# Proposal Automation Workflow (Human-Supervised)

Use this to run proposal delivery as a managed service while keeping owner judgment in control.

## Data Files

- Opportunities: `marketing-agents/data/public_opportunity_log.csv`
- Proposal jobs: `marketing-agents/data/proposal_jobs.csv`
- Transcript memory: `marketing-agents/data/client_transcript_memory.csv`
- Worklist output: `marketing-agents/data/proposal_worklist.csv`

## Daily/Weekly Operating Sequence

1. Refresh target opportunities with Agent 8.
2. Log client conversation takeaways in `client_transcript_memory.csv`.
3. Run Agent 9 to convert transcript direction into proposal inputs.
4. Run Agent 10 to produce/update draft proposal.
5. Run Agent 11 for compliance matrix and redline fixes.
6. Run worklist script for deadline-driven task ordering.
7. Send owner approval brief before any submission.

## Script Command

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\generate-proposal-worklist.ps1 -LookaheadDays 14
```

## Service Packaging Suggestion

- Offer name: `Managed Proposal Operations for Public Contracts`
- Core promise: faster, more compliant proposal output with less admin load on owner/GM.
- Engagement model:
  - setup sprint (templates, compliance matrix, workflow)
  - ongoing monthly proposal operations support
