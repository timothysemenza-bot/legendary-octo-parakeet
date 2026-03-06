# Domain Model v1

## Canonical ID Prefixes
- `cli_` client
- `ws_` workspace
- `opp_` opportunity
- `sol_` solicitation
- `req_` requirement
- `cmr_` compliance matrix row
- `rmr_` response matrix row
- `sdr_` section draft
- `gtd_` gate decision
- `sub_` submission package
- `llr_` lessons learned record

## Entities
- Client(id, name, status, isolation_tier, config_version)
- Workspace(id, client_id, name, timezone, default_roles)
- Opportunity(id, client_id, workspace_id, title, buyer, due_date, stage, status, owner_id, priority)
- Solicitation(id, client_id, workspace_id, opportunity_id, source, documents, raw_text_ref, version)
- Requirement(id, client_id, workspace_id, solicitation_id, req_code, text, atomic_index, category, mandatory, source_locator)
- ComplianceMatrixRow(id, client_id, workspace_id, opportunity_id, requirement_id, response_section_id, status, owner_id, evidence_refs)
- ResponseMatrixRow(id, client_id, workspace_id, opportunity_id, requirement_id, customer_issue_id, win_theme_id, benefit_statement)
- WinTheme(id, client_id, workspace_id, opportunity_id, theme, proof_point_ids, approved)
- CustomerIssueHotButton(id, client_id, workspace_id, opportunity_id, issue, impact, priority)
- ProofPoint(id, client_id, workspace_id, claim, evidence_type, source_asset_id, approval_status)
- ContentAsset(id, client_id, workspace_id, type, title, tags, uri, approved_for_use)
- SectionDraft(id, client_id, workspace_id, opportunity_id, section_code, owner_id, status, content_ref, citations, unsupported_claim_flags)
- ReviewCycle(id, client_id, workspace_id, opportunity_id, type, round, status, started_at, closed_at)
- ReviewComment(id, client_id, workspace_id, review_cycle_id, section_draft_id, severity, comment, resolution_status)
- GateDecision(id, client_id, workspace_id, opportunity_id, gate_code, decision, decider_id, rationale, rework_instructions)
- SubmissionPackage(id, client_id, workspace_id, opportunity_id, artifact_refs, checksum, authorized_by, submitted_at)
- LessonsLearnedRecord(id, client_id, workspace_id, opportunity_id, outcome, root_causes, actions, knowledge_promotions)

## Relationship Chain
Opportunity -> Solicitation -> Requirement -> ComplianceMatrixRow -> SectionDraft -> ReviewComment -> GateDecision -> SubmissionPackage -> LessonsLearnedRecord

## Lifecycle Constraints
- Opportunity cannot enter DRAFTING unless Gate C is APPROVED.
- Opportunity cannot enter SUBMISSION unless Gate D and Gate E are APPROVED.
- SubmissionPackage cannot be authorized unless Gate F is APPROVED.
- Archive completion requires Gate G decision.
