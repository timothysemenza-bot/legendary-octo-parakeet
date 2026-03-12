from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.modules.rfp_parser.schemas import RfpSourceDocumentRecord


class Tier(StrEnum):
    TIER_1 = "TIER_1"
    TIER_2 = "TIER_2"
    TIER_3 = "TIER_3"


class PursuitRecommendation(StrEnum):
    BID = "BID"
    CONDITIONAL = "CONDITIONAL"
    NO_BID = "NO_BID"


class PursuitStage(StrEnum):
    INTELLIGENCE = "INTELLIGENCE"
    EARLY_QUALIFICATION = "EARLY_QUALIFICATION"
    PRE_RFP_CAPTURE = "PRE_RFP_CAPTURE"
    ACTIVE_RFP = "ACTIVE_RFP"
    SUBMITTED = "SUBMITTED"
    AWARD = "AWARD"
    LOST = "LOST"
    DORMANT = "DORMANT"


class IntakeRfpDraftStatus(StrEnum):
    PENDING = "PENDING"
    CONSUMED = "CONSUMED"


class IntakeRfpFieldStatus(StrEnum):
    INFERRED = "INFERRED"
    DEFAULTED = "DEFAULTED"
    MISSING = "MISSING"


class OpportunityIntakeRequest(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    client: str = Field(min_length=2, max_length=255)
    buying_organization_id: str | None = None
    estimated_contract_value: float = Field(gt=0)
    lead_time_days: int = Field(ge=1, le=3650)
    incumbent_status: bool
    strategic_alignment: int = Field(ge=1, le=5)
    estimated_probability_win: int = Field(ge=0, le=100)
    actor: str = Field(default="operator")


class ScoreBreakdown(BaseModel):
    strategic_alignment_component: float
    probability_component: float
    lead_time_component: float
    contract_value_component: float
    incumbent_component: float


class OpportunityIntakeResult(BaseModel):
    id: str
    qualification_score: float
    tier: Tier
    pursuit_recommendation: PursuitRecommendation
    capture_plan_id: str
    pursuit_stage: PursuitStage
    proposal_stage: str
    score_breakdown: ScoreBreakdown


class OpportunityIntakeWithRfpResult(OpportunityIntakeResult):
    solicitation_id: str
    requirement_count: int
    parsed_files: list[str]
    skipped_files: list[str]
    warnings: list[str]
    source_documents: list[RfpSourceDocumentRecord] = Field(default_factory=list)


class OpportunityIntakeDraftFields(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    client: str | None = Field(default=None, max_length=255)
    estimated_contract_value: float | None = Field(default=None, gt=0)
    lead_time_days: int | None = Field(default=None, ge=1, le=3650)
    incumbent_status: bool
    strategic_alignment: int = Field(ge=1, le=5)
    estimated_probability_win: int = Field(ge=0, le=100)


class OpportunityIntakeDraftFieldStatuses(BaseModel):
    name: IntakeRfpFieldStatus
    client: IntakeRfpFieldStatus
    estimated_contract_value: IntakeRfpFieldStatus
    lead_time_days: IntakeRfpFieldStatus
    incumbent_status: IntakeRfpFieldStatus
    strategic_alignment: IntakeRfpFieldStatus
    estimated_probability_win: IntakeRfpFieldStatus


class OpportunityIntakeDraftResponse(BaseModel):
    draft_id: str
    status: IntakeRfpDraftStatus
    actor: str
    suggested_fields: OpportunityIntakeDraftFields
    field_statuses: OpportunityIntakeDraftFieldStatuses
    parsed_files: list[str]
    skipped_files: list[str]
    warnings: list[str]
    extracted_deadline: str | None
    source_documents: list[RfpSourceDocumentRecord] = Field(default_factory=list)


class OpportunityIntakeDraftConfirmRequest(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    client: str = Field(min_length=2, max_length=255)
    buying_organization_id: str | None = None
    estimated_contract_value: float = Field(gt=0)
    lead_time_days: int = Field(ge=1, le=3650)
    incumbent_status: bool
    strategic_alignment: int = Field(ge=1, le=5)
    estimated_probability_win: int = Field(ge=0, le=100)
    actor: str | None = Field(default=None)


class ArchiveActionRequest(BaseModel):
    actor: str = Field(default="operator", min_length=2, max_length=120)
    reason: str | None = Field(default=None, max_length=2000)


class GateDecisionRequest(BaseModel):
    gate_code: str = Field(default="GATE_A")
    decision: str = Field(pattern="^(PENDING|APPROVED|REJECTED|REWORK_REQUIRED)$")
    decider: str = Field(min_length=2, max_length=100)
    decider_user_id: str | None = None
    decider_role: str = Field(default="proposal_manager", min_length=2, max_length=100)
    rationale: str = Field(min_length=3)
    rework_instructions: str | None = Field(default=None)
    rework_owner: str | None = Field(default=None, max_length=100)
    rework_due_date: date | None = None


class GateDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    opportunity_id: str
    gate_code: str
    decision: str
    decider: str
    decider_user_id: str | None
    decider_role: str
    approval_signature: str | None
    rationale: str
    rework_instructions: str | None
    rework_owner: str | None
    rework_due_date: datetime | None
    created_at: datetime


class StageTransitionRequest(BaseModel):
    next_stage: str = Field(
        pattern="^(INTAKE|QUALIFICATION|STRATEGY|COMPLIANCE|CONTENT_PLANNING|DRAFTING|REVIEW|SUBMISSION|ARCHIVE)$"
    )
    actor: str = Field(default="operator")
    actor_user_id: str | None = None
    actor_role: str = Field(default="proposal_manager", min_length=2, max_length=100)
    reason: str = Field(default="Manual stage transition")


class StageTransitionResponse(BaseModel):
    opportunity_id: str
    from_stage: str
    to_stage: str
    blockers: list[str]


class WorkflowTimelineEventResponse(BaseModel):
    timestamp: datetime
    actor: str
    action: str
    category: str
    summary: str
    details: dict


class GateInboxItemResponse(BaseModel):
    opportunity_id: str
    opportunity_name: str
    client: str
    stage: str
    gate_code: str
    gate_status: str
    latest_decider: str | None
    latest_decision_at: datetime | None
    days_in_stage: int
    sla_days: int
    sla_breached: bool
    blockers: list[str]


class CapturePlanTemplate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    opportunity_id: str
    version: int
    summary: str
    client_priorities: str
    competitive_landscape: str
    win_themes_draft: str
    solution_positioning: str
    timeline: str
    created_at: datetime


class AuditEventRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    opportunity_id: str | None
    actor: str
    action: str
    before_state_json: str | None
    after_state_json: str | None
    created_at: datetime


class OpportunityDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    client: str
    estimated_contract_value: float
    lead_time_days: int
    incumbent_status: bool
    strategic_alignment: int
    estimated_probability_win: int
    qualification_score: float
    tier: Tier
    pursuit_recommendation: PursuitRecommendation
    stage: str
    pursuit_stage: PursuitStage
    proposal_stage: str
    buying_organization_id: str | None
    buying_organization_name: str | None
    primary_contract_id: str | None
    primary_contract_title: str | None
    primary_facility_id: str | None
    primary_facility_name: str | None
    confidence_level: str
    expected_rfp_date: date | None
    provenance_summary: str | None
    provenance_last_verified_at: datetime | None
    score_breakdown_json: str | None
    bidder_fit_score: float | None
    weighted_pipeline_value: float | None
    archived_at: datetime | None
    archived_by: str | None
    archive_reason: str | None
    created_at: datetime
    updated_at: datetime
    capture_plan: CapturePlanTemplate | None
    gate_decisions: list[GateDecisionResponse]
    audit_events: list[AuditEventRecord]
