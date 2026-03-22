# Proposal Ops Workspace

This repository is organized as a Codex-first workspace.

`proposal-ops/` remains the flagship product. The rest of the repo is arranged so Codex can work in parallel with clearer project roots, reusable skills, predictable output locations, and cleaner review boundaries across the app, CLI, and IDE extension.

## Primary roots

- `proposal-ops/`: flagship product codebase and demo surface
- `boss-key-website/`: market-facing website and microsite layer
- `marketing-agents/`: automation, intake, growth, and operator workflows
- `projects/`: active, internal, pipeline, completed, and shared work that should not compete with the product roots
- `outputs/`: generated deliverables, reports, scratch captures, and packaging artifacts
- `templates/`: reusable proposal and project templates
- `.agents/skills/`: repo-local Codex skills
- `.codex/agents/`: repo-local custom agent definitions
- `archive/`: retired or non-core experiments

## Codex usage

For Codex app:

- Use the repo root for cross-repo architecture, restructuring, and coordination work.
- Add `proposal-ops/`, `boss-key-website/`, `marketing-agents/`, and any high-touch folder under `projects/` as separate app projects when you want tighter threads and cleaner worktrees.
- Prefer worktree threads for long-running or parallel tasks. Keep local threads for small edits or flows that depend on the exact local runtime you already have running.

For Codex CLI:

```bash
codex
codex --path proposal-ops
codex --path marketing-agents
codex --path projects/active/client/jwblng-mvp
```

For the IDE extension:

- Open the folder that matches the task scope.
- Repo-local `AGENTS.md`, `.agents/skills/`, and `.codex/agents/` apply there too.

## Local development

For the website/server layer:

```bash
npm install
npm start
```

The local server defaults to `http://localhost:3000`.

For the flagship product:

```bash
cd proposal-ops
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

## Useful scripts

- `npm start`: run the local site/server layer
- `npm run test:writing-center-tribute`: smoke-test the writing center tribute flow
- `npm run pw:bosskey:demo`: run the ProposalOps demo flow
- `npm run pw:bosskey:kb`: run the ProposalOps knowledge-base walkthroughs
- `npm run pw:jwblng:phase1pages`: run the JWBLNG page sync flow from `projects/active/client/jwblng-mvp`

## Placement rules

- Put flagship product work in `proposal-ops/`.
- Put market-facing packaging in `boss-key-website/` or `marketing-agents/`.
- Put client, internal, pipeline, and shared working material in `projects/`.
- Put generated artifacts in `outputs/`, not beside source work.
- Put reusable starting points in `templates/`.
- Put retired systems and dead-end experiments in `archive/`.

## Orientation docs

- `AGENTS.md`: repo-wide Codex operating rules
- `docs/codex-workspace-guide.md`: app, CLI, IDE, worktree, and parallel-task guide
- `docs/codex-git-workflow.md`: Git review and staging workflow for Codex
- `docs/apmp-foundation-agent-map.md`: APMP Foundation V4 competency-to-agent registry
- `docs/apmp-helpjuice-export.md`: how to export your licensed APMP Helpjuice pages locally for Codex use
- `docs/apmp-automation-reference-map.md`: APMP workflow guidance distilled from the local Helpjuice export for automation-safe use
- `docs/apmp-automation-workflows.md`: APMP automation pack, stage fit, and prompt patterns
- `docs/focus-map.md`: repo focus and placement rules
- `docs/top-level-triage.md`: active vs archived vs generated top-level classification
