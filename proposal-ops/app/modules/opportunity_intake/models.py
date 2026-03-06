import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    capture_plans: Mapped[list["CapturePlan"]] = relationship(back_populates="opportunity")
    gate_decisions: Mapped[list["GateDecisionRecord"]] = relationship(back_populates="opportunity")
    audit_events: Mapped[list["AuditEvent"]] = relationship(back_populates="opportunity")


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
