# Boss Key V1 Product Spec

## Status

Drafted on March 23, 2026 for the current `projects/pipeline/boss-key/bosc-pursuit-os/` prototype lane.

## 1. Objective

Ship Boss Key V1 as an AI-powered revenue execution system for service businesses that controls the path from opportunity intake through proposal planning and award-to-kickoff alignment.

V1 should answer four operator questions:

1. Should we pursue this work?
2. What does the buyer actually require and care about?
3. What is the cleanest proposal plan and story for this pursuit?
4. What did we sell that operations must be ready to deliver?

## 2. Why It Matters

Boss Key should not compete as a generic AI writing tool. It should win by reducing margin leakage in service firms through better qualification, faster controlled proposal development, and cleaner execution handoffs.

The first commercial wedge is labor-heavy B2B service businesses with meaningful proposal and kickoff friction:

- janitorial
- facilities management
- outsourced site support
- similar multi-site, labor-led service firms

## 3. V1 Product Promise

For service businesses with real bid and proposal workflows, Boss Key turns messy RFPs, notes, and emails into:

- a structured opportunity record
- a clear pursue / review / no-bid recommendation
- a proposal starter pack built around real requirements and buyer priorities
- a handoff risk register that protects delivery and margin after award

## 4. Ideal Customer Profile

### Primary ICP

- regional janitorial and facilities service providers
- 25 to 500 employees
- public-sector, healthcare, education, Class A office, or mixed commercial pursuits
- recurring contracts with mobilization, staffing, quality-control, and reporting complexity

### V1 Buyer / Operator Roles

- owner or president
- sales leader or business development lead
- proposal manager or coordinator
- operations leader responsible for mobilization

## 5. V1 Scope

V1 includes four tightly connected modules.

### 5.1 Opportunity Qualification Engine

Inputs:

- RFP files
- opportunity notes
- discovery notes
- structured form edits

Outputs:

- structured `Opportunity`
- qualification score
- pursue / review / no-bid recommendation
- risk flags
- recommended actions
- assumptions requiring validation

### 5.2 Proposal Intelligence System

Outputs:

- compliance starter
- evaluation-factor map
- response outline
- executive summary draft
- win themes
- objection counters
- proof needs and missing proof flags

### 5.3 Workflow Compression Layer

Outputs:

- current state and next checkpoint
- gate decisions
- review readiness
- open actions
- blocked items
- visible owner and due-state accountability

### 5.4 Execution Alignment Tracker

Outputs:

- sold commitments
- assumptions made during pursuit
- exclusions
- transition and mobilization risks
- unowned or weakly owned handoff items

## 6. Non-Goals For V1

- full CRM replacement
- generic task or project management
- broad chat-first document authoring
- automated pricing optimization
- multi-team collaboration complexity beyond light approvals and ownership
- custom model training

## 7. Current Codebase Baseline

The current prototype already contains useful V1 foundations.

### Existing assets to keep and extend

- `src/domain/opportunity.ts`
  - source of truth for structured opportunity intake
- `src/domain/operatorWorkspace.ts`
  - current pursuit draft, approvals, review checkpoints, assumptions, actions, and variants
- `src/domain/qualification.ts`
  - score, status, rationale, and risk flag result contract
- `src/domain/opportunityImportResult.ts`
  - model-backed import review payload
- `src/engine/qualificationEngine.ts`
  - current rules-based qualification engine
- `src/engine/operatorWorkspace.ts`
  - current workflow snapshot builder
- `src/services/importClient.ts`
  - browser import adapter
- `server/server.ts`
  - import API entrypoint
- `server/openai/importOpportunityWithModel.ts`
  - model-backed structured extraction path
- `src/ui/components/OpportunityWorkbench.tsx`
  - intake and upload surface
- `src/ui/components/QualificationPanel.tsx`
  - qualification rendering surface
- `src/ui/components/IdeaEnginePanel.tsx`
  - current pursuit-story generation surface
- `src/ui/components/OperatorWorkbench.tsx`
  - workflow controls

### V1 gap between current prototype and product

The prototype is already strong on local pursuit composition. The biggest missing product pieces are:

- import review before opportunity creation
- persistence beyond browser local storage
- explicit requirements and evaluation-factor records
- proposal starter pack artifacts as first-class objects
- execution alignment tracker as a visible post-award control surface

## 8. V1 Screen Map

V1 should ship with five primary screens.

### 8.1 Intake Queue

Purpose:
Create or reopen an opportunity and start the import workflow.

Primary user:
Sales lead, proposal lead, or owner.

Core actions:

- upload RFP files or JSON
- open an existing opportunity
- see import status and qualification status at a glance

Current basis:

- `src/app/App.tsx`
- `src/ui/components/OpportunityWorkbench.tsx`

New build needed:

- `src/ui/components/OpportunityListView.tsx`
- persistent workspace storage

### 8.2 Import Review

Purpose:
Review extracted fields, evidence, warnings, and assumptions before creating the opportunity record.

Primary user:
Proposal lead.

Core actions:

- accept or edit extracted values
- see evidence snippets by field
- flag missing inputs
- start the opportunity only after review

Current basis:

- `src/domain/opportunityImportResult.ts`
- `src/services/importClient.ts`
- `server/buildOpportunityImportResult.ts`

New build needed:

- `src/ui/components/OpportunityImportReview.tsx`

### 8.3 Qualification Workspace

Purpose:
Make a controlled bid / no-bid decision with visible reasoning.

Primary user:
Owner, sales leader, operations leader.

Core actions:

- view score and recommendation
- see rationale, risks, and assumptions
- override recommendation with explanation
- assign follow-up actions before advancing

Current basis:

- `src/domain/qualification.ts`
- `src/engine/qualificationEngine.ts`
- `src/ui/components/QualificationPanel.tsx`

New build needed:

- weighted score breakdown
- override history
- explicit decision capture

### 8.4 Proposal Pack Workspace

Purpose:
Turn the qualified opportunity into a controlled proposal plan.

Primary user:
Proposal manager or sales lead.

Core actions:

- review requirements and evaluation factors
- generate proposal starter pack
- curate executive summary direction, themes, proof, and objections
- see missing proof and open questions

Current basis:

- `src/ui/components/IdeaEnginePanel.tsx`
- `src/ui/components/WorkingStoryPanel.tsx`
- `src/engine/ideaPackBuilder.ts`
- `src/services/ideas/RuleBasedIdeaGenerationService.ts`

New build needed:

- compliance matrix view
- evaluation-factor map
- response outline view
- approved-content governance surface

### 8.5 Execution Alignment Tracker

Purpose:
Protect delivery by showing what was sold versus what is operationally ready.

Primary user:
Operations lead and owner.

Core actions:

- review commitments, assumptions, exclusions, and transition risks
- assign owners and due dates
- confirm kickoff readiness

Current basis:

- `src/domain/operatorWorkspace.ts`
- `src/engine/operatorWorkspace.ts`
- `src/ui/components/OperatorWorkbench.tsx`
- `src/ui/components/NextCheckpointPanel.tsx`

New build needed:

- commitment register
- sold-vs-ready diff view
- kickoff signoff state

## 9. Core Data Model

V1 should keep the current `Opportunity` and `OperatorWorkspaceState`, then add a small set of first-class records around them.

### 9.1 Existing records

- `Opportunity`
- `QualificationResult`
- `PursuitDraft`
- `OperatorWorkspaceState`
- `OpportunityImportResult`

### 9.2 New records to add

#### `Requirement`

Purpose:
Represent a solicitation requirement as a reviewable unit.

Suggested fields:

- `id`
- `opportunityId`
- `sourceSection`
- `category`
- `requirementText`
- `responseType` (`must`, `should`, `informational`)
- `owner`
- `status`
- `evidence[]`

#### `EvaluationFactor`

Purpose:
Track what the buyer will likely score or weigh.

Suggested fields:

- `id`
- `opportunityId`
- `title`
- `weighting` or `relativeImportance`
- `evidence[]`
- `recommendedResponseStrategy`

#### `ProposalStarterPack`

Purpose:
Store the structured planning outputs for proposal development.

Suggested fields:

- `id`
- `opportunityId`
- `executiveSummaryDraft`
- `complianceMatrix`
- `outline`
- `winThemes[]`
- `objectionCounters[]`
- `proofNeeds[]`
- `generatedAt`

#### `Commitment`

Purpose:
Track what the pursuit team sold or implied.

Suggested fields:

- `id`
- `opportunityId`
- `type` (`service`, `staffing`, `transition`, `reporting`, `commercial`)
- `text`
- `source`
- `owner`
- `status`
- `deliveryRisk`

#### `HandoffRisk`

Purpose:
Track operational risk discovered between award and kickoff.

Suggested fields:

- `id`
- `opportunityId`
- `commitmentId | null`
- `title`
- `detail`
- `severity`
- `owner`
- `dueDate`
- `status`

## 10. API Contract

Keep the API narrow. V1 only needs a few clear routes.

### 10.1 Existing routes

#### `GET /api/health`

Purpose:
Confirm import service health and model availability.

Current response:

```json
{
  "ok": true,
  "modelEnabled": true,
  "fallbackEnabled": true,
  "model": "gpt-5.4-mini"
}
```

#### `POST /api/import-opportunity`

Purpose:
Accept uploaded source files and return an `OpportunityImportResult`.

Current response shape:

```json
{
  "opportunity": {},
  "extractionMethod": "model",
  "summary": "Boss Key imported 1 source file and drafted a new opportunity.",
  "warnings": [],
  "assumptions": [],
  "evidence": []
}
```

### 10.2 New routes for V1

#### `POST /api/opportunities`

Purpose:
Create a reviewed opportunity record after import review.

Request:

```json
{
  "opportunity": {},
  "importResult": {},
  "createdBy": "tim@example.com"
}
```

Response:

```json
{
  "opportunityId": "opp_123",
  "workspaceState": {}
}
```

#### `GET /api/opportunities/:opportunityId`

Purpose:
Load the full opportunity workspace.

Response:

```json
{
  "opportunity": {},
  "qualification": {},
  "starterPack": null,
  "handoff": null,
  "workspaceState": {}
}
```

#### `POST /api/opportunities/:opportunityId/qualification/run`

Purpose:
Run or rerun qualification using the current opportunity record.

Response:

```json
{
  "qualification": {}
}
```

#### `POST /api/opportunities/:opportunityId/proposal-pack/run`

Purpose:
Generate the proposal starter pack.

Response:

```json
{
  "starterPack": {}
}
```

#### `POST /api/opportunities/:opportunityId/handoff/run`

Purpose:
Generate or refresh sold-vs-ready commitments and handoff risks.

Response:

```json
{
  "commitments": [],
  "handoffRisks": []
}
```

#### `PATCH /api/opportunities/:opportunityId/workspace`

Purpose:
Persist operator edits, approvals, assumptions, and actions.

Response:

```json
{
  "workspaceState": {}
}
```

## 11. Technical Design

### Frontend

- keep React + Vite
- maintain operator-first navigation
- add a lightweight route/state layer once there is more than one persisted opportunity

### Backend

- keep the current Node server pattern for speed
- add persistence before adding orchestration complexity
- prefer small, explicit route handlers over framework-heavy abstractions

### Storage

- Postgres or Supabase for structured data
- object storage for uploaded RFP source files
- store import runs, qualification runs, and proposal-pack runs as auditable events

### AI usage

- use model-backed extraction and generation only behind service boundaries
- require structured outputs for extraction and pack generation
- preserve evidence snippets and reviewer edits
- keep decision math and workflow states deterministic where possible

### Security and trust

- keep API keys server-side only
- make every model-produced field reviewable
- record operator overrides for qualification and proposal outputs

## 12. V1 Delivery Milestones

### Milestone 1: Import Review and Persistence

Ship:

- `OpportunityImportReview` screen
- reviewed opportunity creation flow
- persisted opportunities
- persisted workspace state

Success signal:

- user can upload a new RFP and create a reviewed opportunity without touching raw JSON

### Milestone 2: Qualification Control

Ship:

- score breakdown
- override flow
- decision capture
- follow-up actions before advance

Success signal:

- user can make a visible, auditable pursue / review / no-bid call

### Milestone 3: Proposal Starter Pack

Ship:

- requirements list
- evaluation-factor map
- compliance starter
- response outline
- executive summary draft

Success signal:

- user can go from import to a credible proposal starter pack in one controlled workflow

### Milestone 4: Execution Alignment

Ship:

- commitment register
- assumptions register
- handoff risk tracker
- kickoff readiness signoff

Success signal:

- user can see what was sold and what still threatens delivery or margin

## 13. Acceptance Metrics

Boss Key V1 is working if a design partner can:

- import a live opportunity packet in under 10 minutes
- reach a defendable pursue / review / no-bid decision in under 20 minutes
- produce a proposal starter pack in under 30 minutes
- identify at least three real handoff or margin risks before kickoff

## 14. Immediate Build Sequence

1. Build `OpportunityImportReview.tsx` and stop auto-creating opportunities immediately after import.
2. Add server-side persistence for `Opportunity`, `OpportunityImportResult`, and `OperatorWorkspaceState`.
3. Add an opportunity list / reopen view so Boss Key can handle more than one pursuit.
4. Add `Requirement` and `EvaluationFactor` records derived from import.
5. Generate the first `ProposalStarterPack` object and render it as a controlled workspace.
6. Add `Commitment` and `HandoffRisk` generation to close the sold-to-delivery loop.

## 15. Product Guardrails

If a proposed feature does not improve one of these outcomes, it should wait:

- better bid selection
- faster proposal planning
- cleaner review discipline
- lower handoff risk
- stronger margin protection

That keeps Boss Key positioned as a revenue execution system for service businesses, not a horizontal AI workbench.
