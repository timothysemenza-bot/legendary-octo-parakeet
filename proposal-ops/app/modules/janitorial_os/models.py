import uuid
from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    organization_type: Mapped[str] = mapped_column(String(50), nullable=False, default="OTHER", index=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    website_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    procurement_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    facilities: Mapped[list["Facility"]] = relationship(back_populates="organization")
    contracts: Mapped[list["ContractRecord"]] = relationship(back_populates="organization")


class Facility(Base):
    __tablename__ = "facilities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    parent_facility_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("facilities.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    facility_kind: Mapped[str] = mapped_column(String(20), nullable=False, default="FACILITY", index=True)
    facility_type: Mapped[str] = mapped_column(String(60), nullable=False, default="GENERAL", index=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    service_complexity: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")
    square_footage: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    organization: Mapped[Organization] = relationship(back_populates="facilities")
    parent_facility: Mapped["Facility | None"] = relationship(remote_side="Facility.id")


class ContractRecord(Base):
    __tablename__ = "contract_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    incumbent_vendor: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    estimated_annual_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_total_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    rebid_window_start: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    rebid_window_end: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    procurement_source_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False, default="PUBLIC", index=True)
    source_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    organization: Mapped[Organization] = relationship(back_populates="contracts")
    facilities: Mapped[list["ContractFacility"]] = relationship(back_populates="contract")


class ContractFacility(Base):
    __tablename__ = "contract_facilities"
    __table_args__ = (UniqueConstraint("contract_id", "facility_id", name="uq_contract_facility_pair"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contract_records.id"), nullable=False, index=True
    )
    facility_id: Mapped[str] = mapped_column(String(36), ForeignKey("facilities.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    contract: Mapped[ContractRecord] = relationship(back_populates="facilities")
    facility: Mapped[Facility] = relationship()


class ScoringProfile(Base):
    __tablename__ = "scoring_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    criteria: Mapped[list["ScoringCriterion"]] = relationship(back_populates="profile")


class ScoringCriterion(Base):
    __tablename__ = "scoring_criteria"
    __table_args__ = (UniqueConstraint("profile_id", "code", name="uq_scoring_profile_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scoring_profiles.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    profile: Mapped[ScoringProfile] = relationship(back_populates="criteria")


class Contractor(Base):
    __tablename__ = "contractors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    service_geographies: Mapped[str | None] = mapped_column(Text, nullable=True)
    headquarters_city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    headquarters_state: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    vertical_experience: Mapped[str | None] = mapped_column(Text, nullable=True)
    labor_profile: Mapped[str | None] = mapped_column(String(80), nullable=True)
    union_profile: Mapped[str | None] = mapped_column(String(80), nullable=True)
    diversity_certs: Mapped[str | None] = mapped_column(Text, nullable=True)
    airport_experience: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    healthcare_experience: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    education_experience: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    municipal_experience: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    scale_band: Mapped[str] = mapped_column(String(30), nullable=False, default="REGIONAL")
    relationship_strength: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    prospect_stage: Mapped[str] = mapped_column(String(30), nullable=False, default="TARGET", index=True)
    next_follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    last_touch_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    relationship_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    strategic_fit_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    touchpoints: Mapped[list["ContractorTouchpoint"]] = relationship(back_populates="contractor")


class ContractorTouchpoint(Base):
    __tablename__ = "contractor_touchpoints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contractor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contractors.id"), nullable=False, index=True
    )
    contact_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    touchpoint_type: Mapped[str] = mapped_column(String(30), nullable=False, default="NOTE", index=True)
    touchpoint_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    next_step: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    contractor: Mapped[Contractor] = relationship(back_populates="touchpoints")


class UxEvent(Base):
    __tablename__ = "ux_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    actor: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    page_key: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    path: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    referrer_path: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    form_name: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    target_key: Mapped[str | None] = mapped_column(String(160), nullable=True)
    field_name: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    count_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False, index=True)


class UxFeedback(Base):
    __tablename__ = "ux_feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    actor: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    page_key: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    path: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    form_name: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    feedback_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    note_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    context_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    voice_note_status: Mapped[str] = mapped_column(String(40), nullable=False, default="NOT_PROVIDED")
    voice_note_asset_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False, index=True)


class OpportunityMatch(Base):
    __tablename__ = "opportunity_matches"
    __table_args__ = (UniqueConstraint("opportunity_id", "contractor_id", name="uq_opportunity_match_pair"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("opportunities.id"), nullable=False, index=True
    )
    contractor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contractors.id"), nullable=False, index=True
    )
    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    explanation_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    contractor: Mapped[Contractor] = relationship()


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=True, index=True
    )
    contractor_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("contractors.id"), nullable=True, index=True
    )
    opportunity_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("opportunities.id"), nullable=True, index=True
    )
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role_title: Mapped[str | None] = mapped_column(String(120), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    contact_side: Mapped[str] = mapped_column(String(30), nullable=False, default="BUYER")
    source_type: Mapped[str] = mapped_column(String(30), nullable=False, default="PUBLIC")
    confidence_level: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )


class IntelligenceNote(Base):
    __tablename__ = "intelligence_notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("opportunities.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    note_type: Mapped[str] = mapped_column(String(40), nullable=False, default="INTELLIGENCE")
    note_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_class: Mapped[str] = mapped_column(String(30), nullable=False, default="PUBLIC")
    provenance: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_level: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")
    ethics_guidance_text: Mapped[str] = mapped_column(Text, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)


class EvidenceRecord(Base):
    __tablename__ = "evidence_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("opportunities.id"), nullable=False, index=True
    )
    intelligence_note_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("intelligence_notes.id"), nullable=True, index=True
    )
    contract_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("contract_records.id"), nullable=True, index=True
    )
    source_class: Mapped[str] = mapped_column(String(30), nullable=False, default="PUBLIC")
    provenance: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_level: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")
    ethics_guidance_text: Mapped[str] = mapped_column(Text, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)


class CaptureAction(Base):
    __tablename__ = "capture_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("opportunities.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    action_type: Mapped[str] = mapped_column(String(40), nullable=False, default="RESEARCH")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN", index=True)
    owner: Mapped[str] = mapped_column(String(120), nullable=False, default="operator")
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )


class CommercialEngagement(Base):
    __tablename__ = "commercial_engagements"
    __table_args__ = (UniqueConstraint("opportunity_id", name="uq_commercials_opportunity"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("opportunities.id"), nullable=False, index=True
    )
    contractor_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("contractors.id"), nullable=True, index=True
    )
    retainer_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    success_fee_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    success_fee_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    projected_payout_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    projected_payout_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    weighted_expected_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    realized_revenue: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    contractor: Mapped[Contractor | None] = relationship()


class ProposalWorkflowSummary(Base):
    __tablename__ = "proposal_workflow_summaries"
    __table_args__ = (UniqueConstraint("opportunity_id", name="uq_proposal_summary_opportunity"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("opportunities.id"), nullable=False, index=True
    )
    pricing_status: Mapped[str] = mapped_column(String(30), nullable=False, default="NOT_STARTED")
    compliance_status: Mapped[str] = mapped_column(String(30), nullable=False, default="NOT_STARTED")
    sme_assignments_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    review_gate_status: Mapped[str] = mapped_column(String(30), nullable=False, default="NOT_STARTED")
    submission_milestone: Mapped[str] = mapped_column(String(120), nullable=False, default="Not started")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )
