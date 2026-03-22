# Codex Workspace Guide

This repo is arranged so Codex can work across the app, CLI, and IDE extension without guessing where work belongs.

## What Codex reads here

- `AGENTS.md`: repo-wide operating rules
- nested `AGENTS.md` files inside focused project roots
- `.agents/skills/`: repo-local skills available from the current working directory up to the repo root
- `.codex/config.toml`: repo-local Codex settings
- `.codex/agents/`: repo-local custom agents for parallel work
- `docs/apmp-foundation-agent-map.md`: registry for the APMP-focused proposal agent library
- `docs/apmp-automation-reference-map.md`: APMP workflow guidance distilled from the local Helpjuice export
- `docs/apmp-automation-workflows.md`: recurring-run and automation usage patterns for the APMP automation pack

## Repository map

- `proposal-ops/`: flagship product
- `boss-key-website/`: public site and microsites
- `marketing-agents/`: growth and operator automation
- `projects/active/`: active client work
- `projects/internal/`: internal and personal work
- `projects/pipeline/`: near-product or incubating work
- `projects/completed/`: completed project roots kept available for reference or light follow-up
- `projects/shared/`: shared records and data
- `outputs/`: generated artifacts only
- `templates/`: reusable templates
- `archive/`: retired work
- `workspace/`: legacy local scratch only

## Recommended Codex app project roots

Use the repo root when:

- moving files across multiple roots
- restructuring the workspace
- updating shared docs, skills, or custom agents
- coordinating work that spans more than one product root

Use a subdirectory root when:

- the task lives inside `proposal-ops/`
- the task lives inside `boss-key-website/`
- the task lives inside `marketing-agents/`
- the task is specific to one project under `projects/`

Good focused roots in this repo:

- `proposal-ops/`
- `boss-key-website/`
- `marketing-agents/`
- `projects/active/client/jwblng-mvp/`
- `projects/pipeline/federal-bid-cockpit/`
- `projects/pipeline/demo/apmp-client-automation-poc/`

## App, CLI, and IDE usage

Codex app:

- use worktree threads for parallel or risky work
- use local threads for quick edits or when a single local dev server must stay attached
- keep one thread per project root when possible

Codex CLI:

```bash
codex --path proposal-ops
codex --path marketing-agents
codex --path projects/active/client/jwblng-mvp
```

IDE extension:

- open the folder that matches the task scope
- the IDE extension uses the same agent and shares the same configuration model as the CLI, so the same `AGENTS.md`, skills, and custom agents apply

## Local threads vs worktree threads

Use local threads when:

- you need the exact already-running local environment
- the task is small and low-risk
- you need to inspect or tweak changes in your main checkout immediately

Use worktree threads when:

- multiple tasks should run in parallel
- the task is long-running or backgroundable
- the work may conflict with your current local branch or dev setup
- you want cleaner review and handoff boundaries

## Parallel task safety rules

- assign one clear root per thread or agent
- do not let multiple threads write to the same deliverable folder
- use separate `outputs/` subfolders per task
- avoid mixing product code and client work in one thread unless the task is explicitly cross-repo
- keep branch and review scope narrow

## Output locations

- `outputs/deliverables/`: handoff-ready or review-ready packages
- `outputs/generated/`: generated reports, exports, and compatibility outputs
- `outputs/scratch/`: recordings, quick captures, and disposable operator artifacts

Naming convention:

- deliverables: `<slug>-YYYY-MM-DD`
- scratch: `<source-or-task>-YYYY-MM-DD` when the folder is likely to persist

## Review and staging

- review per project root when possible
- use the app review pane or `/review`
- stage by hunk when one thread touched more than one concern
- leave outputs unstaged unless the generated artifact itself is the deliverable under review
