# Marketing Agents Workspace

This folder is the operating system for outbound, capture, and proposal automation.

## Layout

- `scripts/`: executable automations (PowerShell/Node).
- `prompts/`: agent prompt specs.
- `templates/`: reusable artifacts for outreach/proposals.
- `data/`: CSV/state stores used by scripts.
- `briefs/`: generated and operator-facing outputs.
- `campaigns/`: campaign plans and long-form strategy docs.

## Output Conventions

- Keep generated capture artifacts under:
  - `briefs/generated/public-capture/`
  - `briefs/generated/go-no-go/`
- Keep daily operator summaries in `briefs/`.
- Keep reusable docs in root `marketing-agents/` or `templates/`, not `briefs/`.

## Operating Rule

Before adding a new script, define:
1. input files
2. output file path
3. whether output is generated/transient or reusable reference

If generated, default to `briefs/generated/*`.

## APMP LinkedIn ICP List

Use one command to generate a clean, ranked LinkedIn list from existing pipeline data:

`powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\generate-apmp-linkedin-targets.ps1`

Default behavior is APMP/manual-first (`apmp_member_prospects.csv`) with security lookalike disabled.

If you explicitly want to pull from existing pipelines, enable with flags:

`.\marketing-agents\scripts\generate-apmp-linkedin-targets.ps1 -IncludeProspectPipeline:$true`

Outputs:
- `marketing-agents/data/apmp_linkedin_targets.csv`
- `marketing-agents/briefs/apmp-linkedin-targets-YYYY-MM-DD.md`

Optional manual APMP contacts can be added to:
- `marketing-agents/data/apmp_member_prospects.csv`
