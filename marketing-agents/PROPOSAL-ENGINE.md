# Public-Sector Proposal Engine

This module supports a client-service offering where Boss Key runs proposal operations under owner supervision.

## Service Positioning

Deliver compliant, higher-quality public-sector janitorial proposals faster by combining:

- transcript-driven requirement capture
- structured compliance checks
- human judgment and final approval

Do not present this as generic AI transformation.

## Core Workflow

1. Opportunity target:
- Run Agent 8 (`prompts/08_public_bid_scout.md`).
- Log targets in `data/public_opportunity_log.csv`.

2. Extract client direction:
- Add transcript notes to `data/client_transcript_memory.csv`.
- Run Agent 9 (`prompts/09_transcript_requirements_mapper.md`).

3. Build draft:
- Run Agent 10 (`prompts/10_proposal_draft_builder.md`).
- Save draft metadata in `data/proposal_jobs.csv`.

4. QA for compliance:
- Run Agent 11 (`prompts/11_compliance_qa_submission_pack.md`).
- Use checklist in `templates/submission_checklist.md`.

5. Owner review gate:
- Review claims, pricing assumptions, and risk statements.
- Submit only after explicit owner approval.

## Minimum Inputs per Proposal

- Solicitation ID + due date
- scope of work
- evaluation criteria
- forms/attachments list
- client capabilities and constraints
- transcript-derived priorities

## Guardrails

- No fabricated past performance, certifications, or staffing levels.
- Label every assumption clearly.
- Cite requirement coverage for each major section.
