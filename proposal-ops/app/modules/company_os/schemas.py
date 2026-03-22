from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class EngagementType(StrEnum):
    PROPOSAL_CAPTURE = "proposal-capture"
    DELIVERY_CLIENT_SUCCESS = "delivery-client-success"
    FINANCE_COMMERCIAL = "finance-commercial"
    REVENUE_FOLLOW_UP = "revenue-follow-up"
    GENERAL_ENGAGEMENT = "general-engagement"


class EngagementWorkflowStage(StrEnum):
    SIGNAL_CAPTURE = "SIGNAL_CAPTURE"
    ENGAGEMENT_TRIAGE = "ENGAGEMENT_TRIAGE"
    TIMELINE_SEED = "TIMELINE_SEED"
    ACTION_SEED = "ACTION_SEED"
    APPROVAL_WAIT = "APPROVAL_WAIT"
    FOUNDER_BRIEF = "FOUNDER_BRIEF"
    FOLLOW_THROUGH = "FOLLOW_THROUGH"
    KNOWLEDGE_PROMOTION = "KNOWLEDGE_PROMOTION"
    CLOSED = "CLOSED"


class StatusUpdateRequest(BaseModel):
    status: str = Field(min_length=2, max_length=60)
    owner: str | None = Field(default=None, max_length=120)
    note: str | None = Field(default=None, max_length=2000)


class ProjectionRunRequest(BaseModel):
    marketing_agents_root: str | None = None


class IngestRunRequest(BaseModel):
    source_config_path: str | None = None
    marketing_agents_root: str | None = None
    owner: str = Field(default="Timmy Semenza", min_length=2, max_length=120)


class IngestRunResponse(BaseModel):
    run_id: str
    sources_scanned: int
    items_discovered: int
    signals_created: int
    engagements_created: int
    engagements_updated: int
    actions_created: int
    approvals_created: int
    commitments_created: int
    knowledge_candidates_created: int
    projections_written: list[str]
    founder_brief_id: str | None
    scoreboard_snapshot_id: str | None
    created_at: datetime


class SourceSignalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_id: str
    source_type: str
    source_system: str
    thread_or_meeting_id: str | None
    signal_date: date
    signal_kind: str
    client_name: str
    title: str
    route: str
    summary: str
    content_excerpt: str | None
    provenance_ref: str
    agent_id: str
    run_id: str
    owner: str
    status: str
    created_at: datetime
    updated_at: datetime


class TimelineMilestoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    engagement_id: str
    milestone_code: str
    milestone_label: str
    target_date: date | None
    owner: str
    status: str
    provenance_ref: str
    agent_id: str
    run_id: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class StakeholderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    engagement_id: str
    stakeholder_name: str
    role_code: str
    role_label: str
    organization: str | None
    email: str | None
    status: str
    interview_required: str
    approval_scope: str | None
    provenance_ref: str
    agent_id: str
    run_id: str
    owner: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ActionItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    engagement_id: str
    source_signal_id: str | None
    item_type: str
    task_or_artifact: str
    owner: str
    due_date: date | None
    status: str
    review_required: str
    provenance_ref: str
    agent_id: str
    run_id: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ApprovalRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    engagement_id: str
    source_signal_id: str | None
    approval_type: str
    requested_role: str
    requested_person: str | None
    status: str
    due_date: date | None
    channel: str
    policy_key: str
    provenance_ref: str
    agent_id: str
    run_id: str
    owner: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class MeetingCommitmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    engagement_id: str
    source_signal_id: str | None
    meeting_date: date
    account_or_client: str
    meeting_title: str
    owner: str
    commitment: str
    commitment_owner: str
    due_date: date | None
    status: str
    system_to_update: str
    provenance_ref: str
    agent_id: str
    run_id: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class KnowledgePromotionCandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    engagement_id: str
    source_signal_id: str | None
    candidate_type: str
    title: str
    status: str
    owner: str
    provenance_ref: str
    agent_id: str
    run_id: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class EngagementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    client_name: str
    engagement_name: str
    engagement_type: str
    workflow_stage: str
    status: str
    intake_date: date
    owner: str
    complexity_level: str
    next_action: str
    deadline: date | None
    risk_level: str
    last_signal_id: str | None
    provenance_ref: str
    agent_id: str
    run_id: str
    notes: str | None
    created_at: datetime
    updated_at: datetime
    milestones: list[TimelineMilestoneResponse] = Field(default_factory=list)
    stakeholders: list[StakeholderResponse] = Field(default_factory=list)
    action_items: list[ActionItemResponse] = Field(default_factory=list)
    approvals: list[ApprovalRequestResponse] = Field(default_factory=list)
    commitments: list[MeetingCommitmentResponse] = Field(default_factory=list)
    knowledge_candidates: list[KnowledgePromotionCandidateResponse] = Field(default_factory=list)


class RevenueForecastRow(BaseModel):
    snapshot_date: date
    forecast_window: str
    forecast_type: str
    account_name: str
    stage: str
    amount: float
    expected_close_date: date | None
    probability_percent: int
    weighted_amount: float
    owner: str
    next_action: str | None = None
    notes: str | None = None


class CashflowForecastRow(BaseModel):
    snapshot_date: date
    week_start: date
    projected_cash_in: float
    projected_cash_out: float
    net_cash_change: float
    ending_cash_balance: float | None = None
    confidence: str
    notes: str | None = None


class ScoreboardSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    snapshot_date: date
    pipeline_value: float
    weighted_pipeline: float
    meetings_booked: int
    proposal_count: int
    proposal_win_rate: float
    active_delivery_count: int
    overdue_invoices: int
    total_ar_over_30: float
    open_hiring_roles: int
    urgent_risks: int
    notes: str | None
    agent_id: str
    run_id: str
    owner: str
    status: str
    created_at: datetime
    updated_at: datetime
    revenue_rows: list[RevenueForecastRow] = Field(default_factory=list)
    cashflow_rows: list[CashflowForecastRow] = Field(default_factory=list)


class FounderDecision(BaseModel):
    title: str
    owner: str
    due_date: date | None = None
    cost_of_delay: str


class FounderBriefRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    brief_date: date
    executive_control_summary: str
    decisions_needed: list[FounderDecision] = Field(default_factory=list)
    revenue_watch: str
    delivery_risk_watch: str
    cash_collections_watch: str
    people_capacity_watch: str
    top_moves: list[str] = Field(default_factory=list)
    delegation_queue: list[str] = Field(default_factory=list)
    scoreboard_snapshot_id: str | None
    agent_id: str
    run_id: str
    owner: str
    status: str
    created_at: datetime
    updated_at: datetime
