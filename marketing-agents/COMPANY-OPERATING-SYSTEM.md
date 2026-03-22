# Boss Key Company Operating System

This document extends the outbound and proposal stack into a full company-running system.

It now also folds in the reusable capabilities from the proposal-ops system developed around Eric's company, so the same internal OS can run:
- outbound and authority building
- proposals and capture work
- delivery and client success
- finance and collections
- engagement intake and communication monitoring
- knowledge promotion and reusable methodology

Use it when you need the agent architecture for:
- founder control
- revenue generation
- capture and proposals
- delivery execution
- client success
- staffing and hiring
- finance and collections
- compliance and operating memory
- communication monitoring across approved business channels
- cross-client engagement orchestration from one internal system

## Wave 1 Source of Truth

For Wave 1 (engagement and founder operations), `proposal-ops` is the system of record.
- `proposal-ops` is the durable source for engagement status, founder brief pipeline state, commitments, approvals, and operational decisions.
- `marketing-agents/data/*.csv` are generated projections for operator compatibility and reporting, not the canonical CRM/state source.
- `marketing-agents/briefs/*` are generated founder and intake artifacts and should be treated as consumable snapshots.

## Operating Principles (Wave 1)

- Manual-first ingress: process only approved exports and controlled file-drop inputs until wider capture channels are explicitly added.
- AI as assistant: use AI for extraction, summaries, and draft copy while keeping humans in the decision loop for execution.
- Tight operational scope first: keep engagement/founder workflows stable before automating additional adjacent domains.
- Human approval for external actions: no external calls, sends, post actions, or commitment updates without explicit approval.
- Visible provenance/disclosure: keep source IDs, decision provenance, and run metadata in generated outputs so operators can trace every routed decision.

## Operating Promise

The system should keep four truths visible at all times:
- what revenue is moving
- what delivery commitments are at risk
- what cash is actually coming in
- what only the founder can decide

The goal is not "autonomy."

The goal is a calm, auditable company where agents do prep work, watch the details, and keep handoffs tight while the owner stays in control of external commitments.

## System Shape

The full stack now runs across seven operating lanes:

1. `Engagement Core`
- Agents 26-31
- Watches approved communications, converts conversations into structured engagements, builds reverse timelines, routes approvals, and promotes lessons into reusable assets

2. `Revenue Engine`
- Agents 1-7, 12, 13, and 15
- Finds targets, writes tailored outreach, queues calls and email, and turns raw thinking into authority content

3. `Capture + Proposal`
- Agents 8-11 and 14
- Finds likely bids early, maps requirements, drafts proposals, and closes compliance gaps

4. `Delivery + Client Success`
- Agents 19 and 20
- Converts sold scope into a real work plan, monitors client health, and protects renewals

5. `People + Knowledge`
- Agents 21 and 22
- Keeps capacity ahead of demand and captures repeatable process knowledge

6. `Finance + Compliance`
- Agents 17, 18, and 23
- Forecasts revenue and cash, manages billing and collections, and keeps credentials current

7. `Founder Office`
- Agents 16, 24, and 25
- Produces the founder brief, KPI readout, meeting prep, and follow-through discipline

## New Internal Agents

The original stack stopped after growth, content, and proposal execution. To run the company end to end, add:

16. `Founder Control Tower`
17. `Revenue Forecast + Cashflow Controller`
18. `Billing + Collections Operator`
19. `Delivery Scope-to-Workplan Planner`
20. `Client Success + Renewal Manager`
21. `Staffing Bench + Hiring Coordinator`
22. `SOP + Knowledge Librarian`
23. `Compliance + Credential Watchtower`
24. `Executive Scoreboard Analyst`
25. `Meeting Brief + Follow-Through Operator`
26. `Communications Watchtower`
27. `Engagement Intake + Assessment Orchestrator`
28. `Timeline + Stakeholder Coordinator`
29. `Action + Artifact Builder`
30. `Approval + Notification Router`
31. `Lessons + Knowledge Promotion Manager`

## ProposalOps Capabilities Now Carried Forward

The engagement core is where the Eric-system capabilities show up inside the company OS:

- communication-triggered intake instead of waiting for someone to summarize the thread manually
- structured assessment and routing for every new request
- reverse timelines and countdown-based coordination
- stakeholder interview and contribution mapping
- source-document manifests and artifact scaffolding
- role-based approval routing and notification policy
- lessons learned, promotion queues, and approved knowledge assets
- cross-functional ops reporting instead of isolated delivery notes

## Core Operating Files

The existing revenue files stay in place. Add these internal operating files under `marketing-agents/data/`:

- `company_os_agents.json`
- `communication_signal_log.csv`
- `engagement_register.csv`
- `engagement_timeline.csv`
- `stakeholder_map.csv`
- `action_workbench.csv`
- `approval_router_queue.csv`
- `knowledge_promotion_queue.csv`
- `revenue_forecast.csv`
- `cashflow_forecast.csv`
- `invoice_queue.csv`
- `delivery_workboard.csv`
- `client_health.csv`
- `hiring_pipeline.csv`
- `sop_library_index.csv`
- `compliance_calendar.csv`
- `founder_decision_log.csv`
- `meeting_follow_through.csv`
- `executive_scoreboard.csv`

These files give the new agents stable inputs and outputs without forcing a CRM or PM migration first, and in Wave 1 they are projections generated from canonical `proposal-ops` state.

## Daily Rhythm

### Morning
- Agent 26 sweeps approved communications and extracts signals.
- Agent 27 converts new threads or requests into structured engagements.
- Agent 16 prepares the founder brief from engagement flow, pipeline, cash, delivery, and calendar signals.
- Agent 24 updates the executive scoreboard and flags unusual movement.
- Agent 7 refreshes the call queue.
- Agents 12 and 13 execute only approved outbound work.

### Midday
- Agent 28 builds reverse timelines and stakeholder plans for active engagements.
- Agent 29 converts discussion and source documents into work items and draft artifacts.
- Agent 19 checks sold work against near-term delivery commitments.
- Agent 20 reviews client health, renewal timing, and save-risk signals.
- Agent 18 updates invoice and collections priorities.

### End of Day
- Agent 25 captures commitments from meetings and routes follow-through.
- Agent 30 routes approvals and internal notifications.
- Agent 22 converts repeated work into process knowledge.
- Agent 31 promotes approved lessons into reusable assets.
- Agent 23 checks upcoming compliance deadlines and expiring credentials.

## Weekly Rhythm

### Monday
- communication and engagement review
- pipeline review
- weighted forecast review
- top-priority target accounts

### Tuesday
- delivery risk review
- client health review
- renewal and expansion check

### Wednesday
- public opportunity review
- proposal workload review
- compliance and submission readiness

### Thursday
- approval-routing and notification review
- staffing and hiring review
- SOP and process update review
- tool and handoff cleanup

### Friday
- founder scoreboard review
- approved lessons and asset-promotion review
- decisions closed vs. deferred
- next-week operating plan

## Human Approval Rules

Agents can prepare, rank, draft, and route.

Humans still approve:
- new communication sources or channel connections
- outbound call batches
- outbound email sends
- LinkedIn posts or direct messages
- final proposal submission
- scope or pricing changes
- sensitive invoice disputes or collection escalations
- hiring offers
- formal compliance filings or renewals
- promotion of draft lessons into company-standard assets

For operational hygiene:
- Treat `marketing-agents/data/*.csv` and `marketing-agents/briefs/*` as regenerated projections tied to `proposal-ops`, not as the source of truth.
- Keep approval gates and provenance fields visible in all generated routing or compliance outputs.

## What Good Looks Like

If the system is working:
- every meaningful client communication becomes either a logged signal, a structured engagement, or a tracked action
- no important account goes untouched for too long
- every sold engagement becomes a work plan within one business day
- overdue invoices are visible before they become surprises
- renewal risk shows up before the client asks hard questions
- hiring demand is visible before the bench breaks
- recurring founder decisions are logged instead of rediscovered
- meeting commitments do not disappear into chat or memory
- reusable knowledge compounds instead of being rediscovered on the next client

## Recommended Starting Sequence

If you want to stand this up in practical order, do it in five waves:

1. `Founder + Finance`
- Agents 16, 17, 18, and 24

2. `Engagement Core`
- Agents 26-31

3. `Delivery + Client Success`
- Agents 19, 20, and 25

4. `People + Knowledge`
- Agents 21 and 22

5. `Compliance`
- Agent 23

That order gives you control, cash visibility, a universal engagement layer, and delivery stability before you optimize the edges.
