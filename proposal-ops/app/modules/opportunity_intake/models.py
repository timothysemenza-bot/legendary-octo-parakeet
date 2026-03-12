import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.workflow import OpportunityStage


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    client: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    estimated_contract_value: Mapped[float] = mapped_column(Float, nullable=False)
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False)
    incumbent_status: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    strategic_alignment: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_probability_win: Mapped[int] = mapped_column(Integer, nullable=False)
    qualification_score: Mapped[float] = mapped_column(Float, nullable=False)
    tier: Mapped[str] = mapped_column(String(20), nullable=False)
    pursuit_recommendation: Mapped[str] = mapped_column(String(20), nullable=False)
    stage: Mapped[str] = mapped_column(
        String(30), nullable=False, default=OpportunityStage.INTAKE.value
    )
    pursuit_stage: Mapped[str] = mapped_column(String(30), nullable=False, default="INTELLIGENCE", index=True)
    proposal_stage: Mapped[str] = mapped_column(
        String(30), nullable=False, default=OpportunityStage.INTAKE.value, index=True
    )
    buying_organization_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    primary_contract_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    primary_facility_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    confidence_level: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")
    expected_rfp_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    provenance_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    provenance_last_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    score_breakdown_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    bidder_fit_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    weighted_pipeline_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    archived_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    archive_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    capture_plans: Mapped[list["CapturePlan"]] = relationship(back_populates="opportunity")
    gate_decisions: Mapped[list["GateDecisionRecord"]] = relationship(back_populates="opportunity")
    audit_events: Mapped[list["AuditEvent"]] = relationship(back_populates="opportunity")
    consumed_intake_rfp_drafts: Mapped[list["IntakeRfpDraft"]] = relationship(
        back_populates="consumed_opportunity",
        foreign_keys="IntakeRfpDraft.consumed_opportunity_id",
    )


class CapturePlan(Base):
    __tablename__ = "capture_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("opportunities.id"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    client_priorities: Mapped[str] = mapped_column(Text, nullable=False)
    competitive_landscape: Mapped[str] = mapped_column(Text, nullable=False)
    win_themes_draft: Mapped[str] = mapped_column(Text, nullable=False)
    solution_positioning: Mapped[str] = mapped_column(Text, nullable=False)
    timeline: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    opportunity: Mapped[Opportunity] = relationship(back_populates="capture_plans")


class GateDecisionRecord(Base):
    __tablename__ = "gate_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("opportunities.id"), nullable=False, index=True
    )
    gate_code: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(30), nullable=False)
    decider: Mapped[str] = mapped_column(String(100), nullable=False)
    decider_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    decider_role: Mapped[str] = mapped_column(String(100), nullable=False, default="proposal_manager")
    approval_signature: Mapped[str | None] = mapped_column(String(128), nullable=True)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    rework_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    rework_owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rework_due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    opportunity: Mapped[Opportunity] = relationship(back_populates="gate_decisions")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("opportunities.id"), nullable=True, index=True
    )
    actor: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    before_state_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_state_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    opportunity: Mapped[Opportunity | None] = relationship(back_populates="audit_events")


class IntakeRfpDraft(Base):
    __tablename__ = "intake_rfp_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", index=True)
    actor: Mapped[str] = mapped_column(String(100), nullable=False)
    combined_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    suggested_payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    field_status_json: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_files_json: Mapped[str] = mapped_column(Text, nullable=False)
    skipped_files_json: Mapped[str] = mapped_column(Text, nullable=False)
    warnings_json: Mapped[str] = mapped_column(Text, nullable=False)
    consumed_opportunity_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("opportunities.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    consumed_opportunity: Mapped[Opportunity | None] = relationship(
        back_populates="consumed_intake_rfp_drafts",
        foreign_keys=[consumed_opportunity_id],
    )
