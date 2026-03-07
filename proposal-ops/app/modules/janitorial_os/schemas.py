from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class OrganizationType(StrEnum):
    AIRPORT = "AIRPORT"
    UNIVERSITY = "UNIVERSITY"
    HOSPITAL = "HOSPITAL"
    MUNICIPALITY = "MUNICIPALITY"
    SCHOOL_DISTRICT = "SCHOOL_DISTRICT"
    CORPORATE_CAMPUS = "CORPORATE_CAMPUS"
    OTHER = "OTHER"


class FacilityKind(StrEnum):
    FACILITY = "FACILITY"
    PORTFOLIO = "PORTFOLIO"


class ConfidenceLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class SourceClass(StrEnum):
    PUBLIC = "PUBLIC"
    INFERRED = "INFERRED"
    DIRECT_CONVERSATION = "DIRECT_CONVERSATION"


class ContractSourceType(StrEnum):
    PUBLIC = "PUBLIC"
    DIRECT = "DIRECT"
    INFERRED = "INFERRED"


class ProfileType(StrEnum):
    OPPORTUNITY = "OPPORTUNITY"
    CONTRACTOR_FIT = "CONTRACTOR_FIT"


class PursuitStageOption(StrEnum):
    INTELLIGENCE = "INTELLIGENCE"
    EARLY_QUALIFICATION = "EARLY_QUALIFICATION"
    PRE_RFP_CAPTURE = "PRE_RFP_CAPTURE"
    ACTIVE_RFP = "ACTIVE_RFP"
    SUBMITTED = "SUBMITTED"
    AWARD = "AWARD"
    LOST = "LOST"
    DORMANT = "DORMANT"


class OrganizationBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    organization_type: OrganizationType = OrganizationType.OTHER
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=40)
    website_url: str | None = Field(default=None, max_length=255)
    procurement_url: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(OrganizationBase):
    pass


class OrganizationResponse(OrganizationBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class FacilityBase(BaseModel):
    organization_id: str
    parent_facility_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    facility_kind: FacilityKind = FacilityKind.FACILITY
    facility_type: str = Field(default="GENERAL", min_length=2, max_length=60)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=40)
    service_complexity: str = Field(default="MEDIUM", min_length=2, max_length=20)
    square_footage: float | None = Field(default=None, ge=0)
    notes: str | None = None


class FacilityCreate(FacilityBase):
    pass


class FacilityUpdate(FacilityBase):
    pass


class FacilityResponse(FacilityBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
    organization_name: str | None = None


class ContractRecordBase(BaseModel):
    organization_id: str
    title: str = Field(min_length=3, max_length=255)
    incumbent_vendor: str | None = Field(default=None, max_length=255)
    estimated_annual_value: float | None = Field(default=None, ge=0)
    estimated_total_value: float | None = Field(default=None, ge=0)
    start_date: date | None = None
    expiration_date: date | None = None
    rebid_window_start: date | None = None
    rebid_window_end: date | None = None
    procurement_source_url: str | None = Field(default=None, max_length=255)
    source_type: ContractSourceType = ContractSourceType.PUBLIC
    source_notes: str | None = None
    facility_ids: list[str] = Field(default_factory=list)


class ContractRecordCreate(ContractRecordBase):
    pass


class ContractRecordUpdate(ContractRecordBase):
    pass


class ContractRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    organization_name: str | None
    title: str
    incumbent_vendor: str | None
    estimated_annual_value: float | None
    estimated_total_value: float | None
    start_date: date | None
    expiration_date: date | None
    rebid_window_start: date | None
    rebid_window_end: date | None
    procurement_source_url: str | None
    source_type: str
    source_notes: str | None
    facility_ids: list[str]
    facility_names: list[str]
    created_at: datetime
    updated_at: datetime


class ContractImportResult(BaseModel):
    imported_count: int
    organization_count: int
    facility_count: int
    warnings: list[str]
    contract_ids: list[str]


class ScoringCriterionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    label: str
    weight: int
    sort_order: int


class ScoringProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profile_type: str
    name: str
    is_default: bool
    criteria: list[ScoringCriterionResponse]


class ScoringCriterionUpdate(BaseModel):
    code: str = Field(min_length=2, max_length=60)
    weight: int = Field(ge=0, le=100)


class ScoringProfileUpdateRequest(BaseModel):
    criteria: list[ScoringCriterionUpdate]


class ContractorBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    service_geographies: str | None = None
    headquarters_city: str | None = Field(default=None, max_length=120)
    headquarters_state: str | None = Field(default=None, max_length=40)
    vertical_experience: str | None = None
    labor_profile: str | None = Field(default=None, max_length=80)
    union_profile: str | None = Field(default=None, max_length=80)
    diversity_certs: str | None = None
    airport_experience: bool = False
    healthcare_experience: bool = False
    education_experience: bool = False
    municipal_experience: bool = False
    scale_band: str = Field(default="REGIONAL", min_length=2, max_length=30)
    relationship_strength: int = Field(default=3, ge=1, le=5)
    relationship_notes: str | None = None
    strategic_fit_notes: str | None = None


class ContractorCreate(ContractorBase):
    pass


class ContractorUpdate(ContractorBase):
    pass


class ContractorResponse(ContractorBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class CreatePursuitFromContractRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    primary_facility_id: str | None = None
    pursuit_stage: PursuitStageOption = PursuitStageOption.INTELLIGENCE
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    expected_rfp_date: date | None = None
    provenance_summary: str = Field(min_length=5)
    strategic_fit: int = Field(default=3, ge=1, le=5)
    incumbent_vulnerability: int = Field(default=3, ge=1, le=5)
    rebid_probability: int = Field(default=3, ge=1, le=5)
    relationship_access: int = Field(default=3, ge=1, le=5)
    contractor_fit: int = Field(default=3, ge=1, le=5)
    operational_complexity: int = Field(default=3, ge=1, le=5)
    margin_potential: int = Field(default=3, ge=1, le=5)
    pre_rfp_influence: int = Field(default=3, ge=1, le=5)
    timeline_urgency: int = Field(default=3, ge=1, le=5)
    actor: str = Field(default="operator", min_length=2, max_length=100)


class MatchFactorResponse(BaseModel):
    code: str
    score: float
    reason: str


class OpportunityMatchResponse(BaseModel):
    contractor_id: str
    contractor_name: str
    match_score: float
    factors: list[MatchFactorResponse]
    updated_at: datetime


class ContactBase(BaseModel):
    organization_id: str | None = None
    contractor_id: str | None = None
    full_name: str = Field(min_length=2, max_length=120)
    role_title: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=80)
    contact_side: str = Field(default="BUYER", min_length=2, max_length=30)
    source_type: str = Field(default="PUBLIC", min_length=2, max_length=30)
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    notes: str | None = None


class ContactCreate(ContactBase):
    pass


class ContactResponse(ContactBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    opportunity_id: str | None
    created_at: datetime
    updated_at: datetime


class IntelligenceNoteCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    note_type: str = Field(default="INTELLIGENCE", min_length=2, max_length=40)
    note_text: str = Field(min_length=5)
    source_class: SourceClass = SourceClass.PUBLIC
    provenance: str = Field(min_length=5)
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM


class IntelligenceNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    opportunity_id: str
    title: str
    note_type: str
    note_text: str
    source_class: SourceClass
    provenance: str
    confidence_level: ConfidenceLevel
    ethics_guidance_text: str
    recorded_at: datetime
    created_at: datetime


class EvidenceRecordCreate(BaseModel):
    intelligence_note_id: str | None = None
    contract_id: str | None = None
    source_class: SourceClass = SourceClass.PUBLIC
    provenance: str = Field(min_length=5)
    source_url: str | None = Field(default=None, max_length=255)
    summary: str = Field(min_length=5)
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM


class EvidenceRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    opportunity_id: str
    intelligence_note_id: str | None
    contract_id: str | None
    source_class: SourceClass
    provenance: str
    source_url: str | None
    summary: str
    confidence_level: ConfidenceLevel
    ethics_guidance_text: str
    captured_at: datetime
    created_at: datetime


class CaptureActionCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    action_type: str = Field(default="RESEARCH", min_length=2, max_length=40)
    status: str = Field(default="OPEN", min_length=2, max_length=20)
    owner: str = Field(default="operator", min_length=2, max_length=120)
    due_date: date | None = None
    notes: str | None = None


class CaptureActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    opportunity_id: str
    title: str
    action_type: str
    status: str
    owner: str
    due_date: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class CommercialCreate(BaseModel):
    contractor_id: str | None = None
    retainer_amount: float | None = Field(default=None, ge=0)
    success_fee_type: str | None = Field(default=None, max_length=40)
    success_fee_value: float | None = Field(default=None, ge=0)
    projected_payout_date: date | None = None
    projected_payout_amount: float | None = Field(default=None, ge=0)
    realized_revenue: float | None = Field(default=None, ge=0)
    notes: str | None = None


class CommercialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    opportunity_id: str
    contractor_id: str | None
    contractor_name: str | None = None
    retainer_amount: float | None
    success_fee_type: str | None
    success_fee_value: float | None
    projected_payout_date: date | None
    projected_payout_amount: float | None
    weighted_expected_value: float | None
    realized_revenue: float | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class DashboardContractSummary(BaseModel):
    contract_id: str
    title: str
    organization_name: str
    expiration_date: date | None
    rebid_window_start: date | None
    estimated_annual_value: float | None
    state: str | None


class DashboardOpportunitySummary(BaseModel):
    opportunity_id: str
    name: str
    organization_name: str | None
    pursuit_stage: str
    qualification_score: float
    estimated_contract_value: float
    weighted_pipeline_value: float | None


class DashboardMatchSummary(BaseModel):
    opportunity_id: str
    opportunity_name: str
    contractor_name: str
    match_score: float


class DashboardSummaryResponse(BaseModel):
    generated_at: datetime
    organizations_total: int
    facilities_total: int
    contracts_total: int
    contractors_total: int
    pursuits_total: int
    upcoming_rebids: list[DashboardContractSummary]
    hottest_opportunities: list[DashboardOpportunitySummary]
    top_matches: list[DashboardMatchSummary]
    active_pursuit_counts: dict[str, int]
    total_weighted_pipeline_value: float
    expected_consulting_revenue: float
    stage_conversion_metrics: dict[str, int]
