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

## Boss Key Authority Stack

LinkedIn-first Boss Key campaign assets live here:
- strategy: `marketing-agents/campaigns/boss-key-modern-authority-campaign-2026-03-13.md`
- calendar: `marketing-agents/campaigns/boss-key-30-day-linkedin-authority-calendar-2026-03-13.md`
- launch posts and video scripts: `marketing-agents/campaigns/boss-key-launch-content-pack-2026-03-13.md`
- profile rewrite: `marketing-agents/templates/boss-key-linkedin-profile-rebuild.md`
- comment and DM workflow: `marketing-agents/templates/boss-key-comment-dm-funnel.md`
- video production workflow: `marketing-agents/templates/boss-key-video-recording-runbook.md`
- handoff asset: `marketing-agents/templates/facilities-capture-to-proposal-handoff-checklist.md`
- scheduled post queue: `marketing-agents/data/boss_key_linkedin_post_queue_2026-03-13.csv`
- performance tracker: `marketing-agents/data/boss_key_creator_scoreboard.csv`
- content source template: `marketing-agents/templates/boss-key-content-source-template.md`
- content operator prompt: `marketing-agents/prompts/15_boss_key_content_operator.md`
- content operator runner: `marketing-agents/scripts/run-boss-key-content-operator.ps1`

### Boss Key Content Operator

Turn one rough note, transcript, or recording into a Boss Key content packet:

`pwsh -File .\marketing-agents\scripts\run-boss-key-content-operator.ps1 -InputFile .\marketing-agents\templates\boss-key-content-source-template.md -PromptOnly`

Or from an open PowerShell 7 session:

`& .\marketing-agents\scripts\run-boss-key-content-operator.ps1 -InputFile .\marketing-agents\templates\boss-key-content-source-template.md -PromptOnly`

If `OPENAI_API_KEY` is set in `.env` or `.env.local`, the same script will call the OpenAI Responses API and generate a finished packet automatically.

Audio/video inputs are supported when local transcription is installed:

`pwsh -File .\marketing-agents\scripts\run-boss-key-content-operator.ps1 -InputFile .\path\to\clip.mp4`

## Boss Key Company OS

The full company-running agent stack now lives in:
- blueprint: `marketing-agents/COMPANY-OPERATING-SYSTEM.md`
- structured agent catalog: `marketing-agents/data/company_os_agents.json`
- prompt specs: `marketing-agents/prompts/16_founder_control_tower.md` through `marketing-agents/prompts/31_lessons_knowledge_promotion_manager.md`
- operator app dashboard: `http://localhost:3201/company-os.html`

Use this layer when you need internal operating coverage beyond outbound and proposals:
- founder control
- finance and cash visibility
- billing and collections
- delivery planning
- client success and renewals
- staffing and hiring
- SOP and knowledge capture
- compliance and credential tracking
- approved communication monitoring across email, transcripts, and meeting notes
- structured engagement intake, routing, reverse timelines, and stakeholder coordination
- one internal OS that can run every client engagement instead of separate systems by client

The communication intake runner is now wired into the OS:
- source registry: `marketing-agents/data/approved_communication_sources.csv`
- manual drop zone for approved exports: `marketing-agents/data/engagement-inbox/`
- runner: `marketing-agents/scripts/run-engagement-intake.ps1`
- latest summary outputs:
  - `marketing-agents/data/engagement_intake_summary.json`
  - `marketing-agents/briefs/engagement-intake-latest.md`

It writes directly into:
- `marketing-agents/data/communication_signal_log.csv`
- `marketing-agents/data/engagement_register.csv`
- `marketing-agents/data/engagement_timeline.csv`
- `marketing-agents/data/stakeholder_map.csv`
- `marketing-agents/data/action_workbench.csv`
- `marketing-agents/data/approval_router_queue.csv`
- `marketing-agents/data/meeting_follow_through.csv`
