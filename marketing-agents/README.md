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
