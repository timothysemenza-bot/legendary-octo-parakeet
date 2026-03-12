import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.core.policy import is_role_authorized_for_gate
from app.core.workflow import (
    GateCode,
    GateDecision,
    OpportunityStage,
    active_gate_for_stage,
    can_enter_stage,
    evaluate_gate_transition,
    normalize_gate_code,
)
from app.modules.capture_plan.service import CapturePlanService, build_bootstrap_capture_plan_content
from app.modules.compliance_matrix.service import ComplianceMatrixService
from app.modules.identity.service import IdentityService
from app.modules.opportunity_intake.draft_inference import infer_intake_draft_fields
from app.modules.opportunity_intake.models import CapturePlan, GateDecisionRecord, IntakeRfpDraft, Opportunity
from app.modules.opportunity_intake.repository import OpportunityRepository
from app.modules.opportunity_intake.scoring import (
    classify_recommendation,
    classify_tier,
    compute_intake_score,
)
from app.modules.rfp_parser.document_reader import BatchDocumentExtractionResult, SourceDocumentExtractionRecord
from app.modules.rfp_parser.schemas import RfpParseRequest, RfpSourceDocumentInput, RfpSourceDocumentRecord
from app.modules.rfp_parser.service import RfpParserService
from app.modules.review_manager.service import ReviewManagerService
from app.modules.submission_checklist.service import SubmissionChecklistService
from app.modules.knowledge.service import KnowledgeService
from app.modules.opportunity_intake.schemas import (
    ArchiveActionRequest,
    GateDecisionRequest,
    OpportunityDetailResponse,
    OpportunityIntakeDraftConfirmRequest,
    OpportunityIntakeDraftFieldStatuses,
    OpportunityIntakeDraftFields,
    OpportunityIntakeDraftResponse,
    OpportunityIntakeRequest,
    OpportunityIntakeResult,
    IntakeRfpDraftStatus,
    OpportunityIntakeWithRfpResult,
    PursuitStage,
    ScoreBreakdown,
    GateInboxItemResponse,
    StageTransitionRequest,
    StageTransitionResponse,
)


def _generate_capture_plan_template(opportunity: Opportunity) -> CapturePlan:
    content = build_bootstrap_capture_plan_content(opportunity)
    return CapturePlan(
        opportunity_id=opportunity.id,
        version=1,
        summary=content["summary"],
        client_priorities=content["client_priorities"],
        competitive_landscape=content["competitive_landscape"],
        win_themes_draft=content["win_themes_draft"],
        solution_positioning=content["solution_positioning"],
        timeline=content["timeline"],
    )


_PROPOSAL_TO_PURSUIT_STAGE = {
    OpportunityStage.INTAKE.value: PursuitStage.INTELLIGENCE.value,
    OpportunityStage.QUALIFICATION.value: PursuitStage.EARLY_QUALIFICATION.value,
    OpportunityStage.STRATEGY.value: PursuitStage.PRE_RFP_CAPTURE.value,
    OpportunityStage.COMPLIANCE.value: PursuitStage.ACTIVE_RFP.value,
    OpportunityStage.CONTENT_PLANNING.value: PursuitStage.ACTIVE_RFP.value,
    OpportunityStage.DRAFTING.value: PursuitStage.ACTIVE_RFP.value,
    OpportunityStage.REVIEW.value: PursuitStage.ACTIVE_RFP.value,
    OpportunityStage.SUBMISSION.value: PursuitStage.ACTIVE_RFP.value,
    OpportunityStage.ARCHIVE.value: PursuitStage.SUBMITTED.value,
}


def sync_pursuit_fields(opportunity: Opportunity, explicit_pursuit_stage: str | None = None) -> None:
    opportunity.proposal_stage = opportunity.stage
    if explicit_pursuit_stage:
        opportunity.pursuit_stage = explicit_pursuit_stage
        return
    if opportunity.pursuit_stage in {
        PursuitStage.AWARD.value,
        PursuitStage.LOST.value,
        PursuitStage.DORMANT.value,
    }:
        return
    opportunity.pursuit_stage = _PROPOSAL_TO_PURSUIT_STAGE.get(
        opportunity.stage, PursuitStage.INTELLIGENCE.value
    )


def weighted_pipeline_value(contract_value: float, qualification_score: float) -> float:
    return round(contract_value * (qualification_score / 100.0), 2)


def _safe_json_parse(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _safe_json_list_parse(raw: str | None) -> list[Any]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _timeline_category(action: str) -> str:
    if action.startswith("gate_") or action.startswith("bid_decision"):
        return "GATE"
    if action.startswith("stage_transition"):
        return "STAGE"
    if action.startswith("review_"):
        return "REVIEW"
    if action.startswith("submission_"):
        return "SUBMISSION"
    if action.startswith("compliance_") or action.startswith("rfp_"):
        return "COMPLIANCE"
    if action.startswith("knowledge_"):
        return "KNOWLEDGE"
    return "SYSTEM"


def _timeline_summary(action: str, details: dict[str, Any]) -> str:
    if action == "stage_transition_recorded":
        return f"Stage transitioned to {details.get('stage', 'UNKNOWN')}."
    if action == "gate_decision_recorded":
        return f"{details.get('gate_code', 'GATE')} decision: {details.get('decision', 'UNKNOWN')}."
    if action == "bid_decision_recorded":
        return f"Bid decision recorded: {details.get('decision', 'UNKNOWN')}."
    if action == "review_cycle_created":
        return f"{details.get('review_type', 'REVIEW')} review cycle created."
    if action == "review_cycle_closed":
        return f"{details.get('review_type', 'REVIEW')} review cycle closed."
    if action == "review_comment_created":
        return f"Review comment added ({details.get('severity', 'UNKNOWN')})."
    if action == "review_comment_resolved":
        return "Review comment resolved."
    if action == "submission_checklist_item_updated":
        return f"Submission checklist item updated ({details.get('item_code', 'ITEM')})."
    if action == "submission_filename_validation_ran":
        return "Submission file naming validation executed."
    if action == "compliance_matrix_row_updated":
        return "Compliance matrix row updated."
    if action == "rfp_parsed":
        return "RFP parsed into structured requirements."
    return action.replace("_", " ").capitalize() + "."


def _source_document_inputs_from_batch(batch: BatchDocumentExtractionResult) -> list[RfpSourceDocumentInput]:
    return [
        RfpSourceDocumentInput(
            source_filename=item.source_filename,
            content_type=item.content_type,
            parse_status=item.parse_status,
            skip_reason=item.skip_reason,
            upload_order=item.upload_order,
            source_size_bytes=item.source_size_bytes,
            extracted_text_length=item.extracted_text_length,
            content_text=item.content_text,
            source_sha256=item.source_sha256,
            storage_path=item.storage_path,
            source_payload=item.source_payload,
        )
        for item in batch.documents
    ]


def _source_document_records(rows: list[Any]) -> list[RfpSourceDocumentRecord]:
    return [RfpSourceDocumentRecord.model_validate(row, from_attributes=True) for row in rows]


def _fallback_batch_documents(
    parsed_files: list[str],
    skipped_files: list[str],
    warnings: list[str],
) -> list[SourceDocumentExtractionRecord]:
    skip_reasons: dict[str, str] = {}
    for warning in warnings:
        if ": " not in warning:
            continue
        filename, reason = warning.split(": ", 1)
        skip_reasons[filename] = reason

    documents: list[SourceDocumentExtractionRecord] = []
    upload_order = 1
    for filename in parsed_files:
        documents.append(
            SourceDocumentExtractionRecord(
                source_filename=filename,
                content_type="application/octet-stream",
                parse_status="PARSED",
                skip_reason=None,
                upload_order=upload_order,
                source_size_bytes=0,
                extracted_text_length=0,
                content_text=None,
                source_sha256=None,
                storage_path=None,
                source_payload=None,
            )
        )
        upload_order += 1
    for filename in skipped_files:
        documents.append(
            SourceDocumentExtractionRecord(
                source_filename=filename,
                content_type="application/octet-stream",
                parse_status="SKIPPED",
                skip_reason=skip_reasons.get(filename),
                upload_order=upload_order,
                source_size_bytes=0,
                extracted_text_length=0,
                content_text=None,
                source_sha256=None,
                storage_path=None,
                source_payload=None,
            )
        )
        upload_order += 1
    return documents


class OpportunityIntakeService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = OpportunityRepository(db)

    def _organization_name(self, organization_id: str | None) -> str | None:
        if not organization_id:
            return None
        from app.modules.janitorial_os.models import Organization

        organization = self.db.get(Organization, organization_id)
        return organization.name if organization else None

    def _resolve_client_name(self, client: str, buying_organization_id: str | None) -> str:
        organization_name = self._organization_name(buying_organization_id)
        if buying_organization_id and not organization_name:
            raise ValueError("buying_organization_id is not valid.")
        return organization_name or client

    def _create_intake_records(
        self,
        payload: OpportunityIntakeRequest,
        *,
        explicit_pursuit_stage: str | None = None,
    ) -> tuple[Opportunity, CapturePlan, OpportunityIntakeResult]:
        score, breakdown = compute_intake_score(
            strategic_alignment=payload.strategic_alignment,
            probability_win=payload.estimated_probability_win,
            lead_time_days=payload.lead_time_days,
            contract_value=payload.estimated_contract_value,
            incumbent_status=payload.incumbent_status,
        )
        recommendation = classify_recommendation(score)
        tier = classify_tier(score, payload.estimated_contract_value)

        opportunity = Opportunity(
            name=payload.name,
            client=self._resolve_client_name(payload.client, payload.buying_organization_id),
            estimated_contract_value=payload.estimated_contract_value,
            lead_time_days=payload.lead_time_days,
            incumbent_status=payload.incumbent_status,
            strategic_alignment=payload.strategic_alignment,
            estimated_probability_win=payload.estimated_probability_win,
            qualification_score=score,
            tier=tier.value,
            pursuit_recommendation=recommendation.value,
            stage=OpportunityStage.INTAKE.value,
            confidence_level="MEDIUM",
            provenance_summary="Manual intake created without linked contract radar record.",
            score_breakdown_json=json.dumps(breakdown),
            weighted_pipeline_value=weighted_pipeline_value(payload.estimated_contract_value, score),
            buying_organization_id=payload.buying_organization_id,
        )
        sync_pursuit_fields(opportunity, explicit_pursuit_stage)
        self.repo.add_opportunity(opportunity)
        log_audit_event(
            self.db,
            opportunity_id=opportunity.id,
            actor=payload.actor,
            action="intake_submitted",
            after_state_json=payload.model_dump_json(),
        )

        log_audit_event(
            self.db,
            opportunity_id=opportunity.id,
            actor=payload.actor,
            action="intake_scored",
            after_state_json=json.dumps({"score": score, "tier": tier.value, "recommendation": recommendation.value}),
        )

        capture_plan = _generate_capture_plan_template(opportunity)
        self.repo.add_capture_plan(capture_plan)

        log_audit_event(
            self.db,
            opportunity_id=opportunity.id,
            actor=payload.actor,
            action="capture_plan_generated",
            after_state_json=json.dumps({"capture_plan_id": capture_plan.id, "version": capture_plan.version}),
        )
        result = OpportunityIntakeResult(
            id=opportunity.id,
            qualification_score=score,
            tier=tier,
            pursuit_recommendation=recommendation,
            capture_plan_id=capture_plan.id,
            pursuit_stage=PursuitStage(opportunity.pursuit_stage),
            proposal_stage=opportunity.proposal_stage,
            score_breakdown=ScoreBreakdown(**breakdown),
        )
        return opportunity, capture_plan, result

    def intake(self, payload: OpportunityIntakeRequest) -> OpportunityIntakeResult:
        _opportunity, _capture_plan, result = self._create_intake_records(payload)
        self.db.commit()
        return result

    def create_bootstrapped_pursuit(
        self,
        payload: OpportunityIntakeRequest,
        *,
        explicit_pursuit_stage: str,
        buying_organization_id: str | None = None,
        primary_contract_id: str | None = None,
        primary_facility_id: str | None = None,
        confidence_level: str = "MEDIUM",
        expected_rfp_date: date | None = None,
        provenance_summary: str | None = None,
        provenance_last_verified_at: datetime | None = None,
        commit: bool = True,
    ) -> Opportunity:
        opportunity, _capture_plan, _result = self._create_intake_records(
            payload,
            explicit_pursuit_stage=explicit_pursuit_stage,
        )
        if buying_organization_id:
            opportunity.buying_organization_id = buying_organization_id
            opportunity.client = self._resolve_client_name(opportunity.client, buying_organization_id)
        opportunity.primary_contract_id = primary_contract_id
        opportunity.primary_facility_id = primary_facility_id
        opportunity.confidence_level = confidence_level
        opportunity.expected_rfp_date = expected_rfp_date
        opportunity.provenance_summary = provenance_summary
        opportunity.provenance_last_verified_at = provenance_last_verified_at
        self.db.flush()
        if commit:
            self.db.commit()
            self.db.refresh(opportunity)
        return opportunity

    def _build_rfp_intake_result(
        self,
        *,
        intake_result: OpportunityIntakeResult,
        capture_plan: CapturePlan,
        parse_result: Any,
        batch: BatchDocumentExtractionResult,
    ) -> OpportunityIntakeWithRfpResult:
        return OpportunityIntakeWithRfpResult(
            id=intake_result.id,
            qualification_score=intake_result.qualification_score,
            tier=intake_result.tier,
            pursuit_recommendation=intake_result.pursuit_recommendation,
            capture_plan_id=capture_plan.id,
            pursuit_stage=intake_result.pursuit_stage,
            proposal_stage=intake_result.proposal_stage,
            score_breakdown=intake_result.score_breakdown,
            solicitation_id=parse_result.solicitation_id,
            requirement_count=parse_result.requirement_count,
            parsed_files=batch.parsed_files,
            skipped_files=batch.skipped_files,
            warnings=batch.warnings,
            source_documents=parse_result.source_documents,
        )

    def _persist_intake_with_batch(
        self,
        payload: OpportunityIntakeRequest,
        batch: BatchDocumentExtractionResult,
    ) -> tuple[Opportunity, CapturePlan, OpportunityIntakeResult, Any]:
        if not batch.parsed_files or len(batch.combined_text.strip()) < 20:
            raise ValueError("No uploaded RFP files produced parsable text.")

        opportunity, capture_plan, intake_result = self._create_intake_records(
            payload,
            explicit_pursuit_stage=PursuitStage.ACTIVE_RFP.value,
        )
        log_audit_event(
            self.db,
            opportunity_id=opportunity.id,
            actor=payload.actor,
            action="intake_rfp_batch_ingested",
            after_state_json=json.dumps(
                {
                    "parsed_files": batch.parsed_files,
                    "skipped_files": batch.skipped_files,
                    "warnings": batch.warnings,
                    "source_filename": batch.source_filename,
                }
            ),
        )
        parse_result = RfpParserService(self.db).parse_and_persist(
            opportunity.id,
            RfpParseRequest(
                raw_text=batch.combined_text,
                source_filename=batch.source_filename,
                actor=payload.actor,
                source_documents=_source_document_inputs_from_batch(batch),
            ),
            commit=False,
        )
        return opportunity, capture_plan, intake_result, parse_result

    def intake_with_rfp_batch(
        self,
        payload: OpportunityIntakeRequest,
        batch: BatchDocumentExtractionResult,
    ) -> OpportunityIntakeWithRfpResult:
        try:
            _opportunity, capture_plan, intake_result, parse_result = self._persist_intake_with_batch(payload, batch)
            self.db.commit()
            return self._build_rfp_intake_result(
                intake_result=intake_result,
                capture_plan=capture_plan,
                parse_result=parse_result,
                batch=batch,
            )
        except Exception:
            self.db.rollback()
            raise

    def _serialize_intake_rfp_draft(self, draft: IntakeRfpDraft) -> OpportunityIntakeDraftResponse:
        suggested_fields = OpportunityIntakeDraftFields.model_validate(_safe_json_parse(draft.suggested_payload_json))
        field_statuses = OpportunityIntakeDraftFieldStatuses.model_validate(_safe_json_parse(draft.field_status_json))
        inference = infer_intake_draft_fields(
            draft.combined_text,
            [str(value) for value in _safe_json_list_parse(draft.parsed_files_json)],
        )
        source_documents = _source_document_records(RfpParserService(self.db).list_source_documents_for_draft(draft.id))
        return OpportunityIntakeDraftResponse(
            draft_id=draft.id,
            status=IntakeRfpDraftStatus(draft.status),
            actor=draft.actor,
            suggested_fields=suggested_fields,
            field_statuses=field_statuses,
            parsed_files=[str(value) for value in _safe_json_list_parse(draft.parsed_files_json)],
            skipped_files=[str(value) for value in _safe_json_list_parse(draft.skipped_files_json)],
            warnings=[str(value) for value in _safe_json_list_parse(draft.warnings_json)],
            extracted_deadline=inference.extracted_deadline,
            source_documents=source_documents,
        )

    def create_intake_rfp_draft(
        self,
        actor: str,
        batch: BatchDocumentExtractionResult,
    ) -> OpportunityIntakeDraftResponse:
        if not batch.parsed_files or len(batch.combined_text.strip()) < 20:
            raise ValueError("No uploaded RFP files produced parsable text.")

        inference = infer_intake_draft_fields(batch.combined_text, batch.parsed_files)
        draft = IntakeRfpDraft(
            status=IntakeRfpDraftStatus.PENDING.value,
            actor=actor,
            combined_text=batch.combined_text,
            source_filename=batch.source_filename,
            suggested_payload_json=json.dumps(inference.suggested_fields),
            field_status_json=json.dumps(inference.field_statuses),
            parsed_files_json=json.dumps(batch.parsed_files),
            skipped_files_json=json.dumps(batch.skipped_files),
            warnings_json=json.dumps(batch.warnings),
        )
        self.repo.add_intake_rfp_draft(draft)
        RfpParserService(self.db).persist_draft_source_documents(draft.id, _source_document_inputs_from_batch(batch))
        self.db.commit()
        return self._serialize_intake_rfp_draft(draft)

    def get_intake_rfp_draft(self, draft_id: str) -> OpportunityIntakeDraftResponse | None:
        draft = self.repo.get_intake_rfp_draft(draft_id)
        if not draft:
            return None
        return self._serialize_intake_rfp_draft(draft)

    def confirm_intake_rfp_draft(
        self,
        draft_id: str,
        payload: OpportunityIntakeDraftConfirmRequest,
    ) -> OpportunityIntakeWithRfpResult:
        draft = self.repo.get_intake_rfp_draft(draft_id)
        if not draft:
            raise LookupError("RFP intake draft not found.")
        if draft.status == IntakeRfpDraftStatus.CONSUMED.value:
            raise ValueError("RFP intake draft has already been consumed.")

        draft_source_documents = RfpParserService(self.db).list_source_documents_for_draft(draft.id)
        batch = BatchDocumentExtractionResult(
            combined_text=draft.combined_text,
            parsed_files=[str(value) for value in _safe_json_list_parse(draft.parsed_files_json)],
            skipped_files=[str(value) for value in _safe_json_list_parse(draft.skipped_files_json)],
            warnings=[str(value) for value in _safe_json_list_parse(draft.warnings_json)],
            source_filename=draft.source_filename,
            documents=(
                [
                    SourceDocumentExtractionRecord(
                        source_filename=row.source_filename,
                        content_type=row.content_type,
                        parse_status=row.parse_status,
                        skip_reason=row.skip_reason,
                        upload_order=row.upload_order,
                        source_size_bytes=row.source_size_bytes,
                        extracted_text_length=row.extracted_text_length,
                        content_text=row.content_text,
                        source_sha256=row.source_sha256,
                        storage_path=row.storage_path,
                        source_payload=None,
                    )
                    for row in draft_source_documents
                ]
                if draft_source_documents
                else _fallback_batch_documents(
                    [str(value) for value in _safe_json_list_parse(draft.parsed_files_json)],
                    [str(value) for value in _safe_json_list_parse(draft.skipped_files_json)],
                    [str(value) for value in _safe_json_list_parse(draft.warnings_json)],
                )
            ),
        )
        effective_payload = OpportunityIntakeRequest(
            name=payload.name,
            client=payload.client,
            buying_organization_id=payload.buying_organization_id,
            estimated_contract_value=payload.estimated_contract_value,
            lead_time_days=payload.lead_time_days,
            incumbent_status=payload.incumbent_status,
            strategic_alignment=payload.strategic_alignment,
            estimated_probability_win=payload.estimated_probability_win,
            actor=payload.actor or draft.actor,
        )

        try:
            opportunity, capture_plan, intake_result, parse_result = self._persist_intake_with_batch(effective_payload, batch)
            draft.status = IntakeRfpDraftStatus.CONSUMED.value
            draft.consumed_opportunity_id = opportunity.id
            draft.consumed_at = datetime.now()
            self.db.flush()
            log_audit_event(
                self.db,
                opportunity_id=opportunity.id,
                actor=effective_payload.actor,
                action="intake_rfp_draft_confirmed",
                after_state_json=json.dumps({"draft_id": draft.id}),
            )
            self.db.commit()
            return self._build_rfp_intake_result(
                intake_result=intake_result,
                capture_plan=capture_plan,
                parse_result=parse_result,
                batch=batch,
            )
        except Exception:
            self.db.rollback()
            raise

    def list_opportunities(self, *, include_archived: bool = False) -> list[Opportunity]:
        return self.repo.list_opportunities(include_archived=include_archived)

    def workflow_timeline(
        self, opportunity_id: str, *, category: str = "ALL", limit: int = 200
    ) -> list[dict[str, Any]]:
        events = self.repo.list_audit_events(opportunity_id)
        normalized_category = category.upper()
        rows: list[dict[str, Any]] = []
        for event in events[:limit]:
            details = _safe_json_parse(event.after_state_json)
            row_category = _timeline_category(event.action)
            if normalized_category != "ALL" and row_category != normalized_category:
                continue
            rows.append(
                {
                    "timestamp": event.created_at,
                    "actor": event.actor,
                    "action": event.action,
                    "category": row_category,
                    "summary": _timeline_summary(event.action, details),
                    "details": details,
                }
            )
        return rows

    def _contract_title(self, contract_id: str | None) -> str | None:
        if not contract_id:
            return None
        from app.modules.janitorial_os.models import ContractRecord

        contract = self.db.get(ContractRecord, contract_id)
        return contract.title if contract else None

    def _facility_name(self, facility_id: str | None) -> str | None:
        if not facility_id:
            return None
        from app.modules.janitorial_os.models import Facility

        facility = self.db.get(Facility, facility_id)
        return facility.name if facility else None

    def get_detail(self, opportunity_id: str) -> OpportunityDetailResponse | None:
        opportunity = self.repo.get_opportunity(opportunity_id)
        if not opportunity:
            return None
        capture_plan = self.repo.get_latest_capture_plan(opportunity_id)
        gate_decisions = self.repo.list_gate_decisions(opportunity_id)
        audit_events = self.repo.list_audit_events(opportunity_id)

        return OpportunityDetailResponse(
            id=opportunity.id,
            name=opportunity.name,
            client=opportunity.client,
            estimated_contract_value=opportunity.estimated_contract_value,
            lead_time_days=opportunity.lead_time_days,
            incumbent_status=opportunity.incumbent_status,
            strategic_alignment=opportunity.strategic_alignment,
            estimated_probability_win=opportunity.estimated_probability_win,
            qualification_score=opportunity.qualification_score,
            tier=opportunity.tier,
            pursuit_recommendation=opportunity.pursuit_recommendation,
            stage=opportunity.stage,
            pursuit_stage=opportunity.pursuit_stage,
            proposal_stage=opportunity.proposal_stage,
            buying_organization_id=opportunity.buying_organization_id,
            buying_organization_name=self._organization_name(opportunity.buying_organization_id),
            primary_contract_id=opportunity.primary_contract_id,
            primary_contract_title=self._contract_title(opportunity.primary_contract_id),
            primary_facility_id=opportunity.primary_facility_id,
            primary_facility_name=self._facility_name(opportunity.primary_facility_id),
            confidence_level=opportunity.confidence_level,
            expected_rfp_date=opportunity.expected_rfp_date,
            provenance_summary=opportunity.provenance_summary,
            provenance_last_verified_at=opportunity.provenance_last_verified_at,
            score_breakdown_json=opportunity.score_breakdown_json,
            bidder_fit_score=opportunity.bidder_fit_score,
            weighted_pipeline_value=opportunity.weighted_pipeline_value,
            archived_at=opportunity.archived_at,
            archived_by=opportunity.archived_by,
            archive_reason=opportunity.archive_reason,
            created_at=opportunity.created_at,
            updated_at=opportunity.updated_at,
            capture_plan=capture_plan,
            gate_decisions=gate_decisions,
            audit_events=audit_events,
        )

    def archive_opportunity(self, opportunity_id: str, payload: ArchiveActionRequest) -> Opportunity:
        opportunity = self.repo.get_opportunity(opportunity_id)
        if not opportunity:
            raise ValueError("Opportunity not found.")
        opportunity.archived_at = datetime.now(UTC).replace(tzinfo=None)
        opportunity.archived_by = payload.actor
        opportunity.archive_reason = payload.reason
        self.db.commit()
        self.db.refresh(opportunity)
        return opportunity

    def restore_opportunity(self, opportunity_id: str, payload: ArchiveActionRequest) -> Opportunity:
        opportunity = self.repo.get_opportunity(opportunity_id)
        if not opportunity:
            raise ValueError("Opportunity not found.")
        opportunity.archived_at = None
        opportunity.archived_by = None
        opportunity.archive_reason = None
        self.db.commit()
        self.db.refresh(opportunity)
        return opportunity

    def add_gate_decision(self, opportunity_id: str, payload: GateDecisionRequest) -> GateDecisionRecord | None:
        opportunity = self.repo.get_opportunity(opportunity_id)
        if not opportunity:
            return None

        gate_code = normalize_gate_code(payload.gate_code)
        expected_gate_code = active_gate_for_stage(opportunity.stage)
        GateCode(gate_code)  # raises ValueError if unknown
        GateDecision(payload.decision)  # raises ValueError if unknown
        if gate_code != expected_gate_code:
            log_audit_event(
                self.db,
                opportunity_id=opportunity_id,
                actor=payload.decider,
                action="gate_policy_violation",
                after_state_json=json.dumps(
                    {
                        "gate_code": gate_code,
                        "expected_gate_code": expected_gate_code,
                        "stage": opportunity.stage,
                        "decision": payload.decision,
                        "reason": "Gate decision does not match active stage gate",
                    }
                ),
            )
            self.db.commit()
            raise ValueError(
                f"{gate_code} cannot be decided while opportunity is in {opportunity.stage}. Active gate is {expected_gate_code}."
            )

        if payload.decision == GateDecision.REWORK_REQUIRED.value and not payload.rework_instructions:
            raise ValueError("rework_instructions are required when decision is REWORK_REQUIRED.")

        resolved_decider = payload.decider
        resolved_decider_role = payload.decider_role
        resolved_decider_user_id = payload.decider_user_id

        if payload.decider_user_id:
            identity = IdentityService(self.db)
            user = identity.get_user(payload.decider_user_id)
            if not user or user.status != "ACTIVE":
                raise ValueError("decider_user_id is not an active user.")
            allowed_role = identity.resolve_authorized_role_for_gate(payload.decider_user_id, gate_code, opportunity_id)
            if not allowed_role:
                log_audit_event(
                    self.db,
                    opportunity_id=opportunity_id,
                    actor=payload.decider,
                    action="gate_policy_violation",
                    after_state_json=json.dumps(
                        {
                            "gate_code": gate_code,
                            "decision": payload.decision,
                            "decider_user_id": payload.decider_user_id,
                            "reason": "User lacks scoped authorized role for gate",
                        }
                    ),
                )
                self.db.commit()
                raise ValueError(f"User '{payload.decider_user_id}' is not authorized to act on {gate_code}.")
            resolved_decider = user.display_name
            resolved_decider_role = allowed_role
        elif not is_role_authorized_for_gate(gate_code, payload.decider_role):
            log_audit_event(
                self.db,
                opportunity_id=opportunity_id,
                actor=payload.decider,
                action="gate_policy_violation",
                after_state_json=json.dumps(
                    {
                        "gate_code": gate_code,
                        "decision": payload.decision,
                        "decider_role": payload.decider_role,
                        "reason": "Role is not authorized for gate action",
                    }
                ),
            )
            self.db.commit()
            raise ValueError(
                f"Role '{payload.decider_role}' is not authorized to act on {gate_code}."
            )

        # Gate C cannot be approved unless matrix quality is ready.
        if gate_code == GateCode.GATE_C.value and payload.decision == GateDecision.APPROVED.value:
            quality = ComplianceMatrixService(self.db).matrix_quality(opportunity_id)
            if not quality["gate_c_ready"]:
                raise ValueError(
                    f"Gate C cannot be approved: {'; '.join(quality['gate_c_blockers'])}"
                )
        if gate_code == GateCode.GATE_B.value and payload.decision == GateDecision.APPROVED.value:
            readiness = CapturePlanService(self.db).readiness(opportunity_id)
            if not readiness.ready_for_gate_b:
                raise ValueError(f"Gate B cannot be approved: {'; '.join(readiness.blockers)}")
        if gate_code == GateCode.GATE_D.value and payload.decision == GateDecision.APPROVED.value:
            readiness = ReviewManagerService(self.db).review_readiness(opportunity_id)
            if not readiness.gate_d_ready:
                raise ValueError(f"Gate D cannot be approved: {'; '.join(readiness.gate_d_blockers)}")
        if gate_code == GateCode.GATE_E.value and payload.decision == GateDecision.APPROVED.value:
            readiness = ReviewManagerService(self.db).review_readiness(opportunity_id)
            if not readiness.gate_e_ready:
                raise ValueError(f"Gate E cannot be approved: {'; '.join(readiness.gate_e_blockers)}")
        if gate_code == GateCode.GATE_F.value and payload.decision == GateDecision.APPROVED.value:
            submission = SubmissionChecklistService(self.db).readiness(opportunity_id)
            if not submission.ready_for_gate_f:
                raise ValueError(f"Gate F cannot be approved: {'; '.join(submission.blockers)}")
        if gate_code == GateCode.GATE_G.value and payload.decision == GateDecision.APPROVED.value:
            knowledge = KnowledgeService(self.db).readiness(opportunity_id)
            if not knowledge.gate_g_ready:
                raise ValueError(f"Gate G cannot be approved: {'; '.join(knowledge.blockers)}")

        before_stage = opportunity.stage
        _, next_stage = evaluate_gate_transition(opportunity.stage, gate_code, payload.decision)
        decision_timestamp = datetime.now()
        approval_signature = None
        if payload.decider_user_id and payload.decision in {
            GateDecision.APPROVED.value,
            GateDecision.REJECTED.value,
            GateDecision.REWORK_REQUIRED.value,
        }:
            approval_signature = IdentityService(self.db).sign_gate_approval(
                user_id=payload.decider_user_id,
                opportunity_id=opportunity_id,
                gate_code=gate_code,
                decision=payload.decision,
                rationale=payload.rationale,
                timestamp=decision_timestamp,
            )

        record = GateDecisionRecord(
            opportunity_id=opportunity_id,
            gate_code=gate_code,
            decision=payload.decision,
            decider=resolved_decider,
            decider_user_id=resolved_decider_user_id,
            decider_role=resolved_decider_role,
            approval_signature=approval_signature,
            rationale=payload.rationale,
            rework_instructions=payload.rework_instructions,
            rework_owner=payload.rework_owner,
            rework_due_date=(
                datetime.combine(payload.rework_due_date, datetime.min.time())
                if payload.rework_due_date
                else None
            ),
        )
        self.repo.add_gate_decision(record)

        opportunity.stage = next_stage
        sync_pursuit_fields(opportunity)
        self.db.flush()

        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=payload.decider,
            action="gate_decision_recorded",
            before_state_json=json.dumps({"stage": before_stage}),
            after_state_json=json.dumps(
                {
                    "gate_code": gate_code,
                    "decision": payload.decision,
                    "decider_user_id": resolved_decider_user_id,
                    "decider_role": resolved_decider_role,
                    "approval_signature": approval_signature,
                    "stage": next_stage,
                    "rationale": payload.rationale,
                    "rework_instructions": payload.rework_instructions,
                    "rework_owner": payload.rework_owner,
                    "rework_due_date": payload.rework_due_date.isoformat() if payload.rework_due_date else None,
                }
            ),
        )
        if gate_code == GateCode.GATE_A.value:
            # Backward-compatible audit action for existing analytics/tests.
            log_audit_event(
                self.db,
                opportunity_id=opportunity_id,
                actor=payload.decider,
                action="bid_decision_recorded",
                after_state_json=payload.model_dump_json(),
            )
        self.db.commit()
        return record

    def preview_stage_transition(self, opportunity_id: str, payload: StageTransitionRequest) -> StageTransitionResponse | None:
        opportunity = self.repo.get_opportunity(opportunity_id)
        if not opportunity:
            return None

        transition_gate = active_gate_for_stage(opportunity.stage)
        blockers: list[str] = []
        if payload.actor_user_id:
            identity = IdentityService(self.db)
            user = identity.get_user(payload.actor_user_id)
            if not user or user.status != "ACTIVE":
                blockers.append("actor_user_id is not an active user.")
            else:
                allowed_role = identity.resolve_authorized_role_for_gate(
                    payload.actor_user_id, transition_gate, opportunity_id
                )
                if not allowed_role:
                    blockers.append(
                        f"User '{payload.actor_user_id}' is not authorized to transition from {opportunity.stage}."
                    )
        elif not is_role_authorized_for_gate(transition_gate, payload.actor_role):
            blockers.append(f"Role '{payload.actor_role}' is not authorized to transition from {opportunity.stage}.")

        gate_decisions = self.repo.list_gate_decisions(opportunity_id)
        latest_by_gate: dict[str, str] = {}
        for decision in gate_decisions:
            if decision.gate_code not in latest_by_gate:
                latest_by_gate[decision.gate_code] = decision.decision
        approved_gates = {gate for gate, decision in latest_by_gate.items() if decision == GateDecision.APPROVED.value}

        allowed, stage_blockers = can_enter_stage(opportunity.stage, payload.next_stage, approved_gates)
        blockers.extend(stage_blockers)
        _ = allowed  # clarity: included via blockers aggregation
        return StageTransitionResponse(
            opportunity_id=opportunity_id,
            from_stage=opportunity.stage,
            to_stage=payload.next_stage,
            blockers=blockers,
        )

    def transition_stage(self, opportunity_id: str, payload: StageTransitionRequest) -> StageTransitionResponse | None:
        preview = self.preview_stage_transition(opportunity_id, payload)
        if not preview:
            return None
        if preview.blockers:
            if any("not authorized" in b.lower() or "active user" in b.lower() for b in preview.blockers):
                opportunity = self.repo.get_opportunity(opportunity_id)
                if opportunity:
                    log_audit_event(
                        self.db,
                        opportunity_id=opportunity_id,
                        actor=payload.actor,
                        action="stage_transition_policy_violation",
                        after_state_json=json.dumps(
                            {
                                "from_stage": opportunity.stage,
                                "to_stage": payload.next_stage,
                                "reason": "; ".join(preview.blockers),
                            }
                        ),
                    )
                    self.db.commit()
            return preview

        opportunity = self.repo.get_opportunity(opportunity_id)
        if not opportunity:
            return None
        transition_gate = active_gate_for_stage(opportunity.stage)
        resolved_actor = payload.actor
        resolved_actor_role = payload.actor_role
        resolved_actor_user_id = payload.actor_user_id

        if payload.actor_user_id:
            identity = IdentityService(self.db)
            user = identity.get_user(payload.actor_user_id)
            if not user or user.status != "ACTIVE":
                return preview
            allowed_role = identity.resolve_authorized_role_for_gate(
                payload.actor_user_id, transition_gate, opportunity_id
            )
            if not allowed_role:
                return preview
            resolved_actor = user.display_name
            resolved_actor_role = allowed_role
        elif not is_role_authorized_for_gate(transition_gate, payload.actor_role):
            return preview

        before_stage = opportunity.stage
        opportunity.stage = payload.next_stage
        sync_pursuit_fields(opportunity)
        self.db.flush()
        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=resolved_actor,
            action="stage_transition_recorded",
            before_state_json=json.dumps({"stage": before_stage}),
            after_state_json=json.dumps(
                {
                    "stage": payload.next_stage,
                    "reason": payload.reason,
                    "actor_user_id": resolved_actor_user_id,
                    "actor_role": resolved_actor_role,
                    "transition_gate": transition_gate,
                }
            ),
        )
        self.db.commit()
        return StageTransitionResponse(
            opportunity_id=opportunity_id,
            from_stage=before_stage,
            to_stage=payload.next_stage,
            blockers=[],
        )

    def list_gate_inbox(self) -> list[GateInboxItemResponse]:
        opportunities = self.repo.list_opportunities()
        now = datetime.now()
        sla_days_by_gate = {
            GateCode.GATE_A.value: 2,
            GateCode.GATE_B.value: 3,
            GateCode.GATE_C.value: 5,
            GateCode.GATE_D.value: 5,
            GateCode.GATE_E.value: 3,
            GateCode.GATE_F.value: 2,
            GateCode.GATE_G.value: 7,
        }
        items: list[GateInboxItemResponse] = []

        for opp in opportunities:
            gate_code = active_gate_for_stage(opp.stage)
            decisions = self.repo.list_gate_decisions(opp.id)
            latest_for_gate = next((d for d in decisions if normalize_gate_code(d.gate_code) == gate_code), None)
            gate_status = latest_for_gate.decision if latest_for_gate else GateDecision.PENDING.value
            if gate_status == GateDecision.APPROVED.value:
                continue

            age_source = opp.updated_at or opp.created_at
            days_in_stage = max(0, (now - age_source).days)
            sla_days = sla_days_by_gate[gate_code]
            blockers: list[str] = []
            if gate_code == GateCode.GATE_B.value:
                strategy = CapturePlanService(self.db).readiness(opp.id)
                blockers.extend(strategy.blockers)
            if gate_code == GateCode.GATE_C.value:
                quality = ComplianceMatrixService(self.db).matrix_quality(opp.id)
                blockers.extend(quality["gate_c_blockers"])
            if gate_code == GateCode.GATE_F.value:
                submission = SubmissionChecklistService(self.db).readiness(opp.id)
                blockers.extend(submission.blockers)
            if gate_code == GateCode.GATE_G.value:
                knowledge = KnowledgeService(self.db).readiness(opp.id)
                blockers.extend(knowledge.blockers)

            items.append(
                GateInboxItemResponse(
                    opportunity_id=opp.id,
                    opportunity_name=opp.name,
                    client=opp.client,
                    stage=opp.stage,
                    gate_code=gate_code,
                    gate_status=gate_status,
                    latest_decider=latest_for_gate.decider if latest_for_gate else None,
                    latest_decision_at=latest_for_gate.created_at if latest_for_gate else None,
                    days_in_stage=days_in_stage,
                    sla_days=sla_days,
                    sla_breached=days_in_stage > sla_days,
                    blockers=blockers,
                )
            )
        return items
