import uuid
from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class SourceSignal(Base):
    __tablename__ = "company_source_signals"
    __table_args__ = (UniqueConstraint("fingerprint", name="uq_company_source_signals_fingerprint"),)

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(60), nullable=False)
    source_system: Mapped[str] = mapped_column(String(80), nullable=False)
    thread_or_meeting_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    signal_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    signal_kind: Mapped[str] = mapped_column(String(60), nullable=False, default="communication-capture")
    client_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    route: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    content_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    provenance_ref: Mapped[str] = mapped_column(Text, nullable=False)
    source_payload_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    agent_id: Mapped[str] = mapped_column(String(40), nullable=False, default="26")
    run_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    owner: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="captured", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    engagements: Mapped[list["Engagement"]] = relationship(back_populates="last_signal")
    action_items: Mapped[list["ActionItem"]] = relationship(back_populates="source_signal")
    approvals: Mapped[list["ApprovalRequest"]] = relationship(back_populates="source_signal")
    commitments: Mapped[list["MeetingCommitment"]] = relationship(back_populates="source_signal")
    knowledge_candidates: Mapped[list["KnowledgePromotionCandidate"]] = relationship(back_populates="source_signal")


class Engagement(Base):
    __tablename__ = "company_engagements"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    engagement_name: Mapped[str] = mapped_column(String(255), nullable=False)
    engagement_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    workflow_stage: Mapped[str] = mapped_column(String(40), nullable=False, default="SIGNAL_CAPTURE", index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active", index=True)
    intake_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    owner: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    complexity_level: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    next_action: Mapped[str] = mapped_column(Text, nullable=False)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="medium", index=True)
    last_signal_id: Mapped[str | None] = mapped_column(String(120), ForeignKey("company_source_signals.id"), nullable=True, index=True)
    provenance_ref: Mapped[str] = mapped_column(Text, nullable=False)
    agent_id: Mapped[str] = mapped_column(String(40), nullable=False, default="27")
    run_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    last_signal: Mapped[SourceSignal | None] = relationship(back_populates="engagements")
    milestones: Mapped[list["TimelineMilestone"]] = relationship(back_populates="engagement")
    stakeholders: Mapped[list["Stakeholder"]] = relationship(back_populates="engagement")
    action_items: Mapped[list["ActionItem"]] = relationship(back_populates="engagement")
    approvals: Mapped[list["ApprovalRequest"]] = relationship(back_populates="engagement")
    commitments: Mapped[list["MeetingCommitment"]] = relationship(back_populates="engagement")
    knowledge_candidates: Mapped[list["KnowledgePromotionCandidate"]] = relationship(back_populates="engagement")


class TimelineMilestone(Base):
    __tablename__ = "company_timeline_milestones"
    __table_args__ = (UniqueConstraint("engagement_id", "milestone_code", name="uq_company_timeline_engagement_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    engagement_id: Mapped[str] = mapped_column(String(120), ForeignKey("company_engagements.id"), nullable=False, index=True)
    milestone_code: Mapped[str] = mapped_column(String(80), nullable=False)
    milestone_label: Mapped[str] = mapped_column(String(255), nullable=False)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    owner: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending", index=True)
    source_signal_id: Mapped[str | None] = mapped_column(String(120), ForeignKey("company_source_signals.id"), nullable=True, index=True)
    provenance_ref: Mapped[str] = mapped_column(Text, nullable=False)
    agent_id: Mapped[str] = mapped_column(String(40), nullable=False, default="28")
    run_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    engagement: Mapped[Engagement] = relationship(back_populates="milestones")


class Stakeholder(Base):
    __tablename__ = "company_stakeholders"
    __table_args__ = (UniqueConstraint("engagement_id", "role_code", "stakeholder_name", name="uq_company_stakeholder_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    engagement_id: Mapped[str] = mapped_column(String(120), ForeignKey("company_engagements.id"), nullable=False, index=True)
    stakeholder_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role_code: Mapped[str] = mapped_column(String(80), nullable=False)
    role_label: Mapped[str] = mapped_column(String(255), nullable=False)
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    interview_required: Mapped[str] = mapped_column(String(10), nullable=False, default="no")
    approval_scope: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source_signal_id: Mapped[str | None] = mapped_column(String(120), ForeignKey("company_source_signals.id"), nullable=True, index=True)
    provenance_ref: Mapped[str] = mapped_column(Text, nullable=False)
    agent_id: Mapped[str] = mapped_column(String(40), nullable=False, default="28")
    run_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    owner: Mapped[str] = mapped_column(String(120), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    engagement: Mapped[Engagement] = relationship(back_populates="stakeholders")


class ActionItem(Base):
    __tablename__ = "company_action_items"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(String(120), ForeignKey("company_engagements.id"), nullable=False, index=True)
    source_signal_id: Mapped[str | None] = mapped_column(String(120), ForeignKey("company_source_signals.id"), nullable=True, index=True)
    item_type: Mapped[str] = mapped_column(String(60), nullable=False, default="follow-up")
    task_or_artifact: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str] = mapped_column(String(120), nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="open", index=True)
    review_required: Mapped[str] = mapped_column(String(10), nullable=False, default="no")
    provenance_ref: Mapped[str] = mapped_column(Text, nullable=False)
    agent_id: Mapped[str] = mapped_column(String(40), nullable=False, default="29")
    run_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    engagement: Mapped[Engagement] = relationship(back_populates="action_items")
    source_signal: Mapped[SourceSignal | None] = relationship(back_populates="action_items")


class ApprovalRequest(Base):
    __tablename__ = "company_approval_requests"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(String(120), ForeignKey("company_engagements.id"), nullable=False, index=True)
    source_signal_id: Mapped[str | None] = mapped_column(String(120), ForeignKey("company_source_signals.id"), nullable=True, index=True)
    approval_type: Mapped[str] = mapped_column(String(80), nullable=False)
    requested_role: Mapped[str] = mapped_column(String(120), nullable=False)
    requested_person: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending", index=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(60), nullable=False, default="company-os")
    policy_key: Mapped[str] = mapped_column(String(120), nullable=False)
    provenance_ref: Mapped[str] = mapped_column(Text, nullable=False)
    agent_id: Mapped[str] = mapped_column(String(40), nullable=False, default="30")
    run_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    owner: Mapped[str] = mapped_column(String(120), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    engagement: Mapped[Engagement] = relationship(back_populates="approvals")
    source_signal: Mapped[SourceSignal | None] = relationship(back_populates="approvals")


class MeetingCommitment(Base):
    __tablename__ = "company_meeting_commitments"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(String(120), ForeignKey("company_engagements.id"), nullable=False, index=True)
    source_signal_id: Mapped[str | None] = mapped_column(String(120), ForeignKey("company_source_signals.id"), nullable=True, index=True)
    meeting_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    account_or_client: Mapped[str] = mapped_column(String(255), nullable=False)
    meeting_title: Mapped[str] = mapped_column(String(255), nullable=False)
    owner: Mapped[str] = mapped_column(String(120), nullable=False)
    commitment: Mapped[str] = mapped_column(Text, nullable=False)
    commitment_owner: Mapped[str] = mapped_column(String(120), nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="open", index=True)
    system_to_update: Mapped[str] = mapped_column(String(80), nullable=False, default="company-os")
    provenance_ref: Mapped[str] = mapped_column(Text, nullable=False)
    agent_id: Mapped[str] = mapped_column(String(40), nullable=False, default="25")
    run_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    engagement: Mapped[Engagement] = relationship(back_populates="commitments")
    source_signal: Mapped[SourceSignal | None] = relationship(back_populates="commitments")


class KnowledgePromotionCandidate(Base):
    __tablename__ = "company_knowledge_promotion_candidates"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(String(120), ForeignKey("company_engagements.id"), nullable=False, index=True)
    source_signal_id: Mapped[str | None] = mapped_column(String(120), ForeignKey("company_source_signals.id"), nullable=True, index=True)
    candidate_type: Mapped[str] = mapped_column(String(60), nullable=False, default="lesson")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="candidate", index=True)
    owner: Mapped[str] = mapped_column(String(120), nullable=False)
    provenance_ref: Mapped[str] = mapped_column(Text, nullable=False)
    agent_id: Mapped[str] = mapped_column(String(40), nullable=False, default="31")
    run_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    engagement: Mapped[Engagement] = relationship(back_populates="knowledge_candidates")
    source_signal: Mapped[SourceSignal | None] = relationship(back_populates="knowledge_candidates")


class ScoreboardSnapshot(Base):
    __tablename__ = "company_scoreboard_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    pipeline_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    weighted_pipeline: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    meetings_booked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    proposal_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    proposal_win_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    active_delivery_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    overdue_invoices: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_ar_over_30: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    open_hiring_roles: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    urgent_risks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    revenue_rows_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    cashflow_rows_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    agent_id: Mapped[str] = mapped_column(String(40), nullable=False, default="24")
    run_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    owner: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="generated")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)


class FounderBriefRun(Base):
    __tablename__ = "company_founder_brief_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    brief_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    executive_control_summary: Mapped[str] = mapped_column(Text, nullable=False)
    decisions_needed_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    revenue_watch: Mapped[str] = mapped_column(Text, nullable=False)
    delivery_risk_watch: Mapped[str] = mapped_column(Text, nullable=False)
    cash_collections_watch: Mapped[str] = mapped_column(Text, nullable=False)
    people_capacity_watch: Mapped[str] = mapped_column(Text, nullable=False)
    top_moves_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    delegation_queue_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    scoreboard_snapshot_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("company_scoreboard_snapshots.id"), nullable=True, index=True)
    agent_id: Mapped[str] = mapped_column(String(40), nullable=False, default="16")
    run_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    owner: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="generated")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    scoreboard_snapshot: Mapped[ScoreboardSnapshot | None] = relationship()
