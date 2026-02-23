# Boss Key Client Implementation Playbook

## Purpose
This playbook codifies the Boss Key operating model into a repeatable client implementation you can deploy for service businesses and individual sellers.

Position it as: business development operations acceleration with human-in-the-loop automation.

Do not position it as generic "AI transformation."

## What You Are Selling
A practical operating system that helps clients:
- increase pursuit velocity
- reduce admin drag
- improve follow-up consistency
- protect margin through cleaner execution
- keep leadership focused on selling and delivery

## Productized Offer Structure
1. Diagnostic + Architecture Sprint (2 weeks)
- Map current pipeline, pursuit, proposal, and follow-up workflows.
- Identify the top 3 process leaks (time, conversion, handoff quality).
- Define target workflow and KPI baseline.

2. System Build + Enablement (4-6 weeks)
- Stand up the agent workflow and data files.
- Configure outreach, call planning, and review gates.
- Deploy operator console and daily brief process.

3. Run + Optimize (ongoing retainer)
- Weekly KPI review and queue quality tuning.
- Monthly message/process iteration.
- Quarterly capability expansion (proposal engine, channels, integrations).

## Core System Architecture

### 1) Data Layer (CSV-first, low-friction)
Primary files in `marketing-agents/data/`:
- `prospect_pipeline.csv`: source of truth for account status
- `interaction_log.csv`: complete relationship memory
- `daily_call_plan.csv`: day-level execution queue
- `email_outbox_queue.csv`: outbound email queue with approval fields
- `follow_up_events.csv`: next-touch schedule for cadence continuity
- `proposal_jobs.csv`: proposal work tracking
- `client_transcript_memory.csv`: transcript-derived client direction

Why this matters:
- low overhead
- easy to audit
- easy to migrate to CRM later

### 2) Agent Layer (specialized roles)
Prompt library in `marketing-agents/prompts/`:
- `01_account_research.md` through `13_outlook_email_execution_agent.md`

Canonical orchestration is documented in:
- `marketing-agents/AGENT-SYSTEM.md`

Use the stack as a controlled sequence, not free-form generation.

### 3) Automation Layer (PowerShell orchestration)
Key scripts in `marketing-agents/scripts/`:
- `run-daily-marketing.ps1`: end-to-end daily refresh
- `generate-daily-call-plan.ps1`: call schedule generation
- `generate-daily-brief.ps1`: daily action brief
- `generate-call-runbook.ps1`: call talk tracks
- `build-email-queue-from-pipeline.ps1`: queue creation
- `run-email-review-cycle.ps1`: review packet + decision table
- `apply-email-review-decisions.ps1`: apply approval edits
- `generate-email-followup-cadence.ps1`: follow-up plan generation
- `scan-public-renewals-naics561720.ps1`: contract renewal scanner pattern

### 4) Execution Interface
Operator app:
- `marketing-agents/operator-app.js`
- UI: `marketing-agents/app/index.html`
- docs: `marketing-agents/OPERATOR-CONSOLE.md`

Provides:
- morning refresh
- next-call routing
- script visibility
- outcome logging
- ICS follow-up export

### 5) Channel Integrations (human-approved)
Email:
- `marketing-agents/OUTLOOK-EMAIL-AUTOMATION.md`
- `marketing-agents/NEW-OUTLOOK-SIMPLE.md`
- `marketing-agents/NEW-OUTLOOK-DRAFTS.md`
- `marketing-agents/EMAIL-REVIEW-AUTOMATION.md`

Calling:
- `marketing-agents/CALL-AUTOMATION.md`
- `marketing-agents/AIRCALL-AUTOMATION.md`

LinkedIn ops:
- `marketing-agents/LINKEDIN-OPERATIONS.md`

Calendar:
- `marketing-agents/CALENDAR-AUTOMATION.md`

Rule:
- draft and queue automatically
- owner/client approves before send/post/call batch

## Implementation Phases For Client Delivery

### Phase 0: Intake and Constraints (Day 0-2)
Deliverables:
- ICP and segment definition
- channel rules (email, calls, LinkedIn)
- legal/compliance constraints
- business-hour windows
- tone and claim boundaries

### Phase 1: Pipeline Data Foundation (Week 1)
Build:
- prospect schema and status model
- interaction logging standard
- first 50-100 account records

Deploy:
- `prospect_pipeline.csv`
- `interaction_log.csv`
- `prospect_candidates.csv`

### Phase 2: Messaging and Review Control (Week 1-2)
Build:
- outreach templates + personalization rubric
- approval workflow and QA checkpoints

Deploy:
- `templates/outreach-cadence-templates.md`
- email review packet workflow scripts

Success criteria:
- all outbound has owner approval gates
- all outbound references at least one account-specific fact

### Phase 3: Daily Execution Engine (Week 2-3)
Build:
- call plan generator
- daily brief generator
- follow-up event generation

Deploy:
- `run-daily-marketing.ps1`
- operator console UX

Success criteria:
- team runs day from one queue
- no orphaned follow-ups

### Phase 4: Proposal Ops Module (Week 3-5, optional)
Build:
- opportunity scouting
- transcript-to-requirements mapper
- draft + compliance QA chain

Deploy:
- `marketing-agents/PROPOSAL-ENGINE.md`
- prompts `08`-`11`
- templates for submission QA

Success criteria:
- proposal cycle time drops
- requirement coverage becomes auditable

### Phase 5: Reporting and Optimization (Ongoing)
Weekly review:
- outbound volume
- response rate
- meeting rate
- follow-up SLA adherence
- pipeline stage movement

Monthly review:
- win/loss pattern analysis
- message angle performance
- script and queue tuning

## KPI Framework (Client-Facing)
Track at minimum:
- touches per week
- positive reply rate
- meetings booked per 100 touches
- average days between touches
- stale opportunities (>14 days no touch)
- proposal turnaround time
- conversion by stage

## Client Operating Rhythm
Daily (15-30 minutes admin):
1. Run morning refresh.
2. Review call plan and email drafts.
3. Execute approved calls and sends.
4. Log outcomes same day.

Weekly (60 minutes):
1. Review KPI dashboard and blocked opportunities.
2. Tune scripts and templates.
3. Refresh top account priorities.

Monthly (90 minutes):
1. Adjust ICP and offer angles from results.
2. Upgrade one system component (data quality, channel, proposal flow).

## Reusable Packaging For Your Own Services
Sell this as three implementation SKUs:

1. Foundation Build
- Pipeline + messaging + review controls
- Basic daily cadence

2. Full Outbound Engine
- Foundation + call planning + operator console + calendar/cadence automation

3. Proposal and Public-Sector Add-On
- Opportunity scan + proposal draft chain + compliance QA workflow

## Guardrails and Risk Controls
- No autonomous sending/posting without explicit approval state.
- No fabricated claims, case studies, or credentials.
- Preserve full interaction audit trail.
- Enforce business-hour windows by default.
- Keep sensitive credentials out of plain-text docs when possible.

## White-Label Adaptation Checklist
For each new client, customize:
- ICP definition and exclusions
- message voice and acceptable claims
- offer and CTA language
- local/remote service constraints
- call windows and calendar constraints
- compliance requirements by sector

Keep unchanged:
- agent sequence architecture
- review and approval gates
- logging standards
- daily/weekly operating cadence

## Repo Assets To Reuse Immediately
- System blueprint: `marketing-agents/AGENT-SYSTEM.md`
- Daily orchestration: `marketing-agents/scripts/run-daily-marketing.ps1`
- Operator UX: `marketing-agents/operator-app.js`, `marketing-agents/app/index.html`
- Proposal module: `marketing-agents/PROPOSAL-ENGINE.md`
- Email review loop: `marketing-agents/scripts/run-email-review-cycle.ps1`
- Call planning: `marketing-agents/scripts/generate-daily-call-plan.ps1`
- Briefing: `marketing-agents/scripts/generate-daily-brief.ps1`

## Delivery Handoff Template
At handoff, provide client:
- architecture map (what runs when)
- script runbook (daily/weekly commands)
- owner approval SOP
- data dictionary for CSV fields
- KPI sheet and review cadence
- escalation path for blocked sends/calls

## One-Sentence Positioning
"We implement a human-controlled business development operating system that removes admin drag, tightens follow-through, and increases pursuit velocity without adding headcount."
