from pydantic import BaseModel, Field

from app.modules.compliance_matrix.schemas import ComplianceMatrixQualityResponse, ComplianceMatrixRowResponse
from app.modules.rfp_parser.schemas import RfpStructuredFields
from app.modules.submission_checklist.schemas import SubmissionChecklistItemResponse, SubmissionReadinessResponse


class CoordinationDateRecord(BaseModel):
    label: str
    value: str | None = None
    field_name: str | None = None
    provenance: list[str] = Field(default_factory=list)


class ReverseTimelineMilestoneRecord(BaseModel):
    code: str
    label: str
    target_date: str | None = None
    offset_days: int | None = None
    note: str
    status: str


class StakeholderAssignmentRecord(BaseModel):
    role_code: str
    role_label: str
    purpose: str
    owner_name: str = ""
    status: str = "UNASSIGNED"


class CoordinationChecklistItemRecord(BaseModel):
    category: str
    label: str
    owner_role: str
    status: str
    note: str | None = None


class OpportunityAssessmentResponse(BaseModel):
    overall_recommendation: str
    strategic_fit: str
    geographic_fit: str
    operational_fit: str
    revenue_scale_signal: str
    complexity_level: str
    risk_level: str
    missing_information: list[str] = Field(default_factory=list)
    recommended_next_action: str


class RfpCoordinationSummaryResponse(BaseModel):
    opportunity_id: str
    opportunity_name: str
    client: str
    summary: str
    assessment: OpportunityAssessmentResponse
    key_dates: list[CoordinationDateRecord] = Field(default_factory=list)
    reverse_timeline: list[ReverseTimelineMilestoneRecord] = Field(default_factory=list)
    stakeholders: list[StakeholderAssignmentRecord] = Field(default_factory=list)
    coordination_checklist: list[CoordinationChecklistItemRecord] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)
    document_gaps: list[str] = Field(default_factory=list)
    operator_prompts: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    structured_fields: RfpStructuredFields | None = None
    field_provenance: dict[str, list[str]] = Field(default_factory=dict)
    compliance_summary: ComplianceMatrixQualityResponse
    compliance_rows: list[ComplianceMatrixRowResponse] = Field(default_factory=list)
    submission_readiness: SubmissionReadinessResponse
    submission_items: list[SubmissionChecklistItemResponse] = Field(default_factory=list)


class RfpCoordinationQuestionRequest(BaseModel):
    question: str = Field(min_length=3)


class RfpCoordinationQuestionResponse(BaseModel):
    question: str
    answer: str
    status: str = Field(pattern="^(found|partial|not_found)$")
    matched_field: str | None = None
    snippets: list[str] = Field(default_factory=list)
