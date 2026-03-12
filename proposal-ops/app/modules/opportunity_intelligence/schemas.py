from datetime import UTC, date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.opportunity_intake.schemas import OpportunityDetailResponse, PursuitStage


class SignalSourceType(StrEnum):
    BUDGET = "BUDGET"
    AGENDA = "AGENDA"
    LEGISLATION = "LEGISLATION"
    PROCUREMENT_PORTAL = "PROCUREMENT_PORTAL"
    GRANT_PROGRAM = "GRANT_PROGRAM"
    BOARD_PACKET = "BOARD_PACKET"
    NEWS = "NEWS"
    OTHER = "OTHER"


class SignalEventType(StrEnum):
    FUNDING = "FUNDING"
    GOVERNANCE = "GOVERNANCE"
    PROCUREMENT = "PROCUREMENT"
    PROGRAM = "PROGRAM"
    REGULATORY = "REGULATORY"
    REBID = "REBID"
    GRANT = "GRANT"
    OTHER = "OTHER"


class HypothesisStage(StrEnum):
    MONITORING = "MONITORING"
    QUALIFIED = "QUALIFIED"
    CAPTURE_READY = "CAPTURE_READY"
    PARKED = "PARKED"
    CONVERTED = "CONVERTED"
    CLOSED = "CLOSED"


class ConfidenceLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _choice_token(value: str) -> str:
    return str(value).strip().upper().replace("-", "_").replace("/", "_").replace(" ", "_")


def _coerce_enum_value(value: object, enum_cls: type[StrEnum]) -> object:
    if value is None or isinstance(value, enum_cls):
        return value
    text = str(value).strip()
    if not text:
        return value
    token = _choice_token(text)
    for member in enum_cls:
        if token in {_choice_token(member.name), _choice_token(member.value)}:
            return member.value
    return value


class SignalSourceBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    source_type: SignalSourceType = SignalSourceType.OTHER
    region: str | None = Field(default=None, max_length=120)
    owner_scope: str | None = Field(default=None, max_length=120)
    source_url: str | None = Field(default=None, max_length=255)
    notes: str | None = None

    @field_validator("source_type", mode="before")
    @classmethod
    def _normalize_source_type(cls, value: object) -> object:
        return _coerce_enum_value(value, SignalSourceType)


class SignalSourceCreate(SignalSourceBase):
    pass


class SignalSourceResponse(SignalSourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class SignalEventBase(BaseModel):
    source_id: str
    title: str = Field(min_length=3, max_length=255)
    signal_type: SignalEventType = SignalEventType.OTHER
    signal_date: date
    jurisdiction: str | None = Field(default=None, max_length=120)
    agency_name: str | None = Field(default=None, max_length=255)
    program_name: str | None = Field(default=None, max_length=255)
    summary: str = Field(min_length=5)
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    source_url: str | None = Field(default=None, max_length=255)
    source_reference: str | None = Field(default=None, max_length=255)
    recommended_action: str | None = None

    @field_validator("signal_type", mode="before")
    @classmethod
    def _normalize_signal_type(cls, value: object) -> object:
        return _coerce_enum_value(value, SignalEventType)

    @field_validator("confidence_level", mode="before")
    @classmethod
    def _normalize_confidence_level(cls, value: object) -> object:
        return _coerce_enum_value(value, ConfidenceLevel)


class SignalEventCreate(SignalEventBase):
    pass


class SignalEventResponse(SignalEventBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_name: str | None = None
    created_at: datetime
    updated_at: datetime


class OpportunityHypothesisBase(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    sector: str | None = Field(default=None, max_length=120)
    geography: str | None = Field(default=None, max_length=120)
    buying_organization: str | None = Field(default=None, max_length=255)
    buying_organization_id: str | None = None
    service_line: str | None = Field(default=None, max_length=120)
    stage: HypothesisStage = HypothesisStage.MONITORING
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    expected_release_start: date | None = None
    expected_release_end: date | None = None
    summary: str = Field(min_length=5)
    recommended_action: str | None = None
    primary_signal_event_id: str | None = None
    recommended_contractor_id: str | None = None

    @field_validator("stage", mode="before")
    @classmethod
    def _normalize_stage(cls, value: object) -> object:
        return _coerce_enum_value(value, HypothesisStage)

    @field_validator("confidence_level", mode="before")
    @classmethod
    def _normalize_confidence_level(cls, value: object) -> object:
        return _coerce_enum_value(value, ConfidenceLevel)


class OpportunityHypothesisCreate(OpportunityHypothesisBase):
    pass


class OpportunityHypothesisResponse(OpportunityHypothesisBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    buying_organization_name: str | None = None
    primary_signal_event_title: str | None = None
    recommended_contractor_name: str | None = None
    converted_opportunity_id: str | None = None
    converted_opportunity_name: str | None = None
    converted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class HypothesisConversionCreate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    client_name: str | None = Field(default=None, max_length=255)
    contractor_id: str | None = None
    estimated_contract_value: float = Field(gt=0)
    lead_time_days: int | None = Field(default=None, ge=1, le=3650)
    incumbent_status: bool = False
    strategic_alignment: int = Field(default=3, ge=1, le=5)
    estimated_probability_win: int | None = Field(default=None, ge=0, le=100)
    pursuit_stage: PursuitStage = PursuitStage.EARLY_QUALIFICATION
    expected_rfp_date: date | None = None
    actor: str = Field(default="operator", min_length=2, max_length=100)

    @field_validator("pursuit_stage", mode="before")
    @classmethod
    def _normalize_pursuit_stage(cls, value: object) -> object:
        return _coerce_enum_value(value, PursuitStage)


class HypothesisConversionResponse(BaseModel):
    hypothesis: OpportunityHypothesisResponse
    opportunity: OpportunityDetailResponse


class OpportunityIntelligenceSummaryResponse(BaseModel):
    generated_at: datetime = Field(default_factory=_utcnow)
    signal_sources_total: int
    signal_events_total: int
    open_hypotheses_total: int
    recent_signal_events: list[SignalEventResponse]
    active_hypotheses: list[OpportunityHypothesisResponse]
