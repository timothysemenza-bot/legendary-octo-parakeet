"""company os wave 1

Revision ID: 0033_company_os_wave1
Revises: 0032_growth_relationship_source_of_truth
Create Date: 2026-03-17
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0033_company_os_wave1"
down_revision: str | Sequence[str] | None = "0032_growth_relationship_source_of_truth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "company_source_signals",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=120), nullable=False),
        sa.Column("source_type", sa.String(length=60), nullable=False),
        sa.Column("source_system", sa.String(length=80), nullable=False),
        sa.Column("thread_or_meeting_id", sa.String(length=255), nullable=True),
        sa.Column("signal_date", sa.Date(), nullable=False),
        sa.Column("signal_kind", sa.String(length=60), nullable=False),
        sa.Column("client_name", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("route", sa.String(length=60), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("content_excerpt", sa.Text(), nullable=True),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("provenance_ref", sa.Text(), nullable=False),
        sa.Column("source_payload_json", sa.Text(), nullable=False),
        sa.Column("agent_id", sa.String(length=40), nullable=False),
        sa.Column("run_id", sa.String(length=120), nullable=False),
        sa.Column("owner", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fingerprint", name="uq_company_source_signals_fingerprint"),
    )
    op.create_index("ix_company_source_signals_client_name", "company_source_signals", ["client_name"], unique=False)
    op.create_index("ix_company_source_signals_fingerprint", "company_source_signals", ["fingerprint"], unique=False)
    op.create_index("ix_company_source_signals_route", "company_source_signals", ["route"], unique=False)
    op.create_index("ix_company_source_signals_run_id", "company_source_signals", ["run_id"], unique=False)
    op.create_index("ix_company_source_signals_signal_date", "company_source_signals", ["signal_date"], unique=False)
    op.create_index("ix_company_source_signals_status", "company_source_signals", ["status"], unique=False)
    op.create_index("ix_company_source_signals_thread_or_meeting_id", "company_source_signals", ["thread_or_meeting_id"], unique=False)

    op.create_table(
        "company_engagements",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("client_name", sa.String(length=255), nullable=False),
        sa.Column("engagement_name", sa.String(length=255), nullable=False),
        sa.Column("engagement_type", sa.String(length=60), nullable=False),
        sa.Column("workflow_stage", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("intake_date", sa.Date(), nullable=False),
        sa.Column("owner", sa.String(length=120), nullable=False),
        sa.Column("complexity_level", sa.String(length=20), nullable=False),
        sa.Column("next_action", sa.Text(), nullable=False),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("last_signal_id", sa.String(length=120), nullable=True),
        sa.Column("provenance_ref", sa.Text(), nullable=False),
        sa.Column("agent_id", sa.String(length=40), nullable=False),
        sa.Column("run_id", sa.String(length=120), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["last_signal_id"], ["company_source_signals.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_company_engagements_client_name", "company_engagements", ["client_name"], unique=False)
    op.create_index("ix_company_engagements_deadline", "company_engagements", ["deadline"], unique=False)
    op.create_index("ix_company_engagements_engagement_type", "company_engagements", ["engagement_type"], unique=False)
    op.create_index("ix_company_engagements_intake_date", "company_engagements", ["intake_date"], unique=False)
    op.create_index("ix_company_engagements_last_signal_id", "company_engagements", ["last_signal_id"], unique=False)
    op.create_index("ix_company_engagements_owner", "company_engagements", ["owner"], unique=False)
    op.create_index("ix_company_engagements_risk_level", "company_engagements", ["risk_level"], unique=False)
    op.create_index("ix_company_engagements_run_id", "company_engagements", ["run_id"], unique=False)
    op.create_index("ix_company_engagements_status", "company_engagements", ["status"], unique=False)
    op.create_index("ix_company_engagements_workflow_stage", "company_engagements", ["workflow_stage"], unique=False)

    op.create_table(
        "company_timeline_milestones",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("engagement_id", sa.String(length=120), nullable=False),
        sa.Column("milestone_code", sa.String(length=80), nullable=False),
        sa.Column("milestone_label", sa.String(length=255), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("owner", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("source_signal_id", sa.String(length=120), nullable=True),
        sa.Column("provenance_ref", sa.Text(), nullable=False),
        sa.Column("agent_id", sa.String(length=40), nullable=False),
        sa.Column("run_id", sa.String(length=120), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["engagement_id"], ["company_engagements.id"]),
        sa.ForeignKeyConstraint(["source_signal_id"], ["company_source_signals.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("engagement_id", "milestone_code", name="uq_company_timeline_engagement_code"),
    )
    op.create_index("ix_company_timeline_milestones_engagement_id", "company_timeline_milestones", ["engagement_id"], unique=False)
    op.create_index("ix_company_timeline_milestones_run_id", "company_timeline_milestones", ["run_id"], unique=False)
    op.create_index("ix_company_timeline_milestones_source_signal_id", "company_timeline_milestones", ["source_signal_id"], unique=False)
    op.create_index("ix_company_timeline_milestones_status", "company_timeline_milestones", ["status"], unique=False)
    op.create_index("ix_company_timeline_milestones_target_date", "company_timeline_milestones", ["target_date"], unique=False)

    op.create_table(
        "company_stakeholders",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("engagement_id", sa.String(length=120), nullable=False),
        sa.Column("stakeholder_name", sa.String(length=255), nullable=False),
        sa.Column("role_code", sa.String(length=80), nullable=False),
        sa.Column("role_label", sa.String(length=255), nullable=False),
        sa.Column("organization", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("interview_required", sa.String(length=10), nullable=False),
        sa.Column("approval_scope", sa.String(length=120), nullable=True),
        sa.Column("source_signal_id", sa.String(length=120), nullable=True),
        sa.Column("provenance_ref", sa.Text(), nullable=False),
        sa.Column("agent_id", sa.String(length=40), nullable=False),
        sa.Column("run_id", sa.String(length=120), nullable=False),
        sa.Column("owner", sa.String(length=120), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["engagement_id"], ["company_engagements.id"]),
        sa.ForeignKeyConstraint(["source_signal_id"], ["company_source_signals.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("engagement_id", "role_code", "stakeholder_name", name="uq_company_stakeholder_key"),
    )
    op.create_index("ix_company_stakeholders_engagement_id", "company_stakeholders", ["engagement_id"], unique=False)
    op.create_index("ix_company_stakeholders_run_id", "company_stakeholders", ["run_id"], unique=False)
    op.create_index("ix_company_stakeholders_source_signal_id", "company_stakeholders", ["source_signal_id"], unique=False)

    op.create_table(
        "company_action_items",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("engagement_id", sa.String(length=120), nullable=False),
        sa.Column("source_signal_id", sa.String(length=120), nullable=True),
        sa.Column("item_type", sa.String(length=60), nullable=False),
        sa.Column("task_or_artifact", sa.Text(), nullable=False),
        sa.Column("owner", sa.String(length=120), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("review_required", sa.String(length=10), nullable=False),
        sa.Column("provenance_ref", sa.Text(), nullable=False),
        sa.Column("agent_id", sa.String(length=40), nullable=False),
        sa.Column("run_id", sa.String(length=120), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["engagement_id"], ["company_engagements.id"]),
        sa.ForeignKeyConstraint(["source_signal_id"], ["company_source_signals.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_company_action_items_due_date", "company_action_items", ["due_date"], unique=False)
    op.create_index("ix_company_action_items_engagement_id", "company_action_items", ["engagement_id"], unique=False)
    op.create_index("ix_company_action_items_run_id", "company_action_items", ["run_id"], unique=False)
    op.create_index("ix_company_action_items_source_signal_id", "company_action_items", ["source_signal_id"], unique=False)
    op.create_index("ix_company_action_items_status", "company_action_items", ["status"], unique=False)

    op.create_table(
        "company_approval_requests",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("engagement_id", sa.String(length=120), nullable=False),
        sa.Column("source_signal_id", sa.String(length=120), nullable=True),
        sa.Column("approval_type", sa.String(length=80), nullable=False),
        sa.Column("requested_role", sa.String(length=120), nullable=False),
        sa.Column("requested_person", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("channel", sa.String(length=60), nullable=False),
        sa.Column("policy_key", sa.String(length=120), nullable=False),
        sa.Column("provenance_ref", sa.Text(), nullable=False),
        sa.Column("agent_id", sa.String(length=40), nullable=False),
        sa.Column("run_id", sa.String(length=120), nullable=False),
        sa.Column("owner", sa.String(length=120), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["engagement_id"], ["company_engagements.id"]),
        sa.ForeignKeyConstraint(["source_signal_id"], ["company_source_signals.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_company_approval_requests_due_date", "company_approval_requests", ["due_date"], unique=False)
    op.create_index("ix_company_approval_requests_engagement_id", "company_approval_requests", ["engagement_id"], unique=False)
    op.create_index("ix_company_approval_requests_run_id", "company_approval_requests", ["run_id"], unique=False)
    op.create_index("ix_company_approval_requests_source_signal_id", "company_approval_requests", ["source_signal_id"], unique=False)
    op.create_index("ix_company_approval_requests_status", "company_approval_requests", ["status"], unique=False)

    op.create_table(
        "company_meeting_commitments",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("engagement_id", sa.String(length=120), nullable=False),
        sa.Column("source_signal_id", sa.String(length=120), nullable=True),
        sa.Column("meeting_date", sa.Date(), nullable=False),
        sa.Column("account_or_client", sa.String(length=255), nullable=False),
        sa.Column("meeting_title", sa.String(length=255), nullable=False),
        sa.Column("owner", sa.String(length=120), nullable=False),
        sa.Column("commitment", sa.Text(), nullable=False),
        sa.Column("commitment_owner", sa.String(length=120), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("system_to_update", sa.String(length=80), nullable=False),
        sa.Column("provenance_ref", sa.Text(), nullable=False),
        sa.Column("agent_id", sa.String(length=40), nullable=False),
        sa.Column("run_id", sa.String(length=120), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["engagement_id"], ["company_engagements.id"]),
        sa.ForeignKeyConstraint(["source_signal_id"], ["company_source_signals.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_company_meeting_commitments_due_date", "company_meeting_commitments", ["due_date"], unique=False)
    op.create_index("ix_company_meeting_commitments_engagement_id", "company_meeting_commitments", ["engagement_id"], unique=False)
    op.create_index("ix_company_meeting_commitments_meeting_date", "company_meeting_commitments", ["meeting_date"], unique=False)
    op.create_index("ix_company_meeting_commitments_run_id", "company_meeting_commitments", ["run_id"], unique=False)
    op.create_index("ix_company_meeting_commitments_source_signal_id", "company_meeting_commitments", ["source_signal_id"], unique=False)
    op.create_index("ix_company_meeting_commitments_status", "company_meeting_commitments", ["status"], unique=False)

    op.create_table(
        "company_knowledge_promotion_candidates",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("engagement_id", sa.String(length=120), nullable=False),
        sa.Column("source_signal_id", sa.String(length=120), nullable=True),
        sa.Column("candidate_type", sa.String(length=60), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("owner", sa.String(length=120), nullable=False),
        sa.Column("provenance_ref", sa.Text(), nullable=False),
        sa.Column("agent_id", sa.String(length=40), nullable=False),
        sa.Column("run_id", sa.String(length=120), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["engagement_id"], ["company_engagements.id"]),
        sa.ForeignKeyConstraint(["source_signal_id"], ["company_source_signals.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_company_knowledge_promotion_candidates_engagement_id", "company_knowledge_promotion_candidates", ["engagement_id"], unique=False)
    op.create_index("ix_company_knowledge_promotion_candidates_run_id", "company_knowledge_promotion_candidates", ["run_id"], unique=False)
    op.create_index("ix_company_knowledge_promotion_candidates_source_signal_id", "company_knowledge_promotion_candidates", ["source_signal_id"], unique=False)
    op.create_index("ix_company_knowledge_promotion_candidates_status", "company_knowledge_promotion_candidates", ["status"], unique=False)

    op.create_table(
        "company_scoreboard_snapshots",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("pipeline_value", sa.Float(), nullable=False),
        sa.Column("weighted_pipeline", sa.Float(), nullable=False),
        sa.Column("meetings_booked", sa.Integer(), nullable=False),
        sa.Column("proposal_count", sa.Integer(), nullable=False),
        sa.Column("proposal_win_rate", sa.Float(), nullable=False),
        sa.Column("active_delivery_count", sa.Integer(), nullable=False),
        sa.Column("overdue_invoices", sa.Integer(), nullable=False),
        sa.Column("total_ar_over_30", sa.Float(), nullable=False),
        sa.Column("open_hiring_roles", sa.Integer(), nullable=False),
        sa.Column("urgent_risks", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("revenue_rows_json", sa.Text(), nullable=False),
        sa.Column("cashflow_rows_json", sa.Text(), nullable=False),
        sa.Column("agent_id", sa.String(length=40), nullable=False),
        sa.Column("run_id", sa.String(length=120), nullable=False),
        sa.Column("owner", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_company_scoreboard_snapshots_run_id", "company_scoreboard_snapshots", ["run_id"], unique=False)
    op.create_index("ix_company_scoreboard_snapshots_snapshot_date", "company_scoreboard_snapshots", ["snapshot_date"], unique=False)

    op.create_table(
        "company_founder_brief_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("brief_date", sa.Date(), nullable=False),
        sa.Column("executive_control_summary", sa.Text(), nullable=False),
        sa.Column("decisions_needed_json", sa.Text(), nullable=False),
        sa.Column("revenue_watch", sa.Text(), nullable=False),
        sa.Column("delivery_risk_watch", sa.Text(), nullable=False),
        sa.Column("cash_collections_watch", sa.Text(), nullable=False),
        sa.Column("people_capacity_watch", sa.Text(), nullable=False),
        sa.Column("top_moves_json", sa.Text(), nullable=False),
        sa.Column("delegation_queue_json", sa.Text(), nullable=False),
        sa.Column("scoreboard_snapshot_id", sa.String(length=36), nullable=True),
        sa.Column("agent_id", sa.String(length=40), nullable=False),
        sa.Column("run_id", sa.String(length=120), nullable=False),
        sa.Column("owner", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["scoreboard_snapshot_id"], ["company_scoreboard_snapshots.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_company_founder_brief_runs_brief_date", "company_founder_brief_runs", ["brief_date"], unique=False)
    op.create_index("ix_company_founder_brief_runs_run_id", "company_founder_brief_runs", ["run_id"], unique=False)
    op.create_index("ix_company_founder_brief_runs_scoreboard_snapshot_id", "company_founder_brief_runs", ["scoreboard_snapshot_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_company_founder_brief_runs_scoreboard_snapshot_id", table_name="company_founder_brief_runs")
    op.drop_index("ix_company_founder_brief_runs_run_id", table_name="company_founder_brief_runs")
    op.drop_index("ix_company_founder_brief_runs_brief_date", table_name="company_founder_brief_runs")
    op.drop_table("company_founder_brief_runs")

    op.drop_index("ix_company_scoreboard_snapshots_snapshot_date", table_name="company_scoreboard_snapshots")
    op.drop_index("ix_company_scoreboard_snapshots_run_id", table_name="company_scoreboard_snapshots")
    op.drop_table("company_scoreboard_snapshots")

    op.drop_index("ix_company_knowledge_promotion_candidates_status", table_name="company_knowledge_promotion_candidates")
    op.drop_index("ix_company_knowledge_promotion_candidates_source_signal_id", table_name="company_knowledge_promotion_candidates")
    op.drop_index("ix_company_knowledge_promotion_candidates_run_id", table_name="company_knowledge_promotion_candidates")
    op.drop_index("ix_company_knowledge_promotion_candidates_engagement_id", table_name="company_knowledge_promotion_candidates")
    op.drop_table("company_knowledge_promotion_candidates")

    op.drop_index("ix_company_meeting_commitments_status", table_name="company_meeting_commitments")
    op.drop_index("ix_company_meeting_commitments_source_signal_id", table_name="company_meeting_commitments")
    op.drop_index("ix_company_meeting_commitments_run_id", table_name="company_meeting_commitments")
    op.drop_index("ix_company_meeting_commitments_meeting_date", table_name="company_meeting_commitments")
    op.drop_index("ix_company_meeting_commitments_engagement_id", table_name="company_meeting_commitments")
    op.drop_index("ix_company_meeting_commitments_due_date", table_name="company_meeting_commitments")
    op.drop_table("company_meeting_commitments")

    op.drop_index("ix_company_approval_requests_status", table_name="company_approval_requests")
    op.drop_index("ix_company_approval_requests_source_signal_id", table_name="company_approval_requests")
    op.drop_index("ix_company_approval_requests_run_id", table_name="company_approval_requests")
    op.drop_index("ix_company_approval_requests_engagement_id", table_name="company_approval_requests")
    op.drop_index("ix_company_approval_requests_due_date", table_name="company_approval_requests")
    op.drop_table("company_approval_requests")

    op.drop_index("ix_company_action_items_status", table_name="company_action_items")
    op.drop_index("ix_company_action_items_source_signal_id", table_name="company_action_items")
    op.drop_index("ix_company_action_items_run_id", table_name="company_action_items")
    op.drop_index("ix_company_action_items_engagement_id", table_name="company_action_items")
    op.drop_index("ix_company_action_items_due_date", table_name="company_action_items")
    op.drop_table("company_action_items")

    op.drop_index("ix_company_stakeholders_source_signal_id", table_name="company_stakeholders")
    op.drop_index("ix_company_stakeholders_run_id", table_name="company_stakeholders")
    op.drop_index("ix_company_stakeholders_engagement_id", table_name="company_stakeholders")
    op.drop_table("company_stakeholders")

    op.drop_index("ix_company_timeline_milestones_target_date", table_name="company_timeline_milestones")
    op.drop_index("ix_company_timeline_milestones_status", table_name="company_timeline_milestones")
    op.drop_index("ix_company_timeline_milestones_source_signal_id", table_name="company_timeline_milestones")
    op.drop_index("ix_company_timeline_milestones_run_id", table_name="company_timeline_milestones")
    op.drop_index("ix_company_timeline_milestones_engagement_id", table_name="company_timeline_milestones")
    op.drop_table("company_timeline_milestones")

    op.drop_index("ix_company_engagements_workflow_stage", table_name="company_engagements")
    op.drop_index("ix_company_engagements_status", table_name="company_engagements")
    op.drop_index("ix_company_engagements_run_id", table_name="company_engagements")
    op.drop_index("ix_company_engagements_risk_level", table_name="company_engagements")
    op.drop_index("ix_company_engagements_owner", table_name="company_engagements")
    op.drop_index("ix_company_engagements_last_signal_id", table_name="company_engagements")
    op.drop_index("ix_company_engagements_intake_date", table_name="company_engagements")
    op.drop_index("ix_company_engagements_engagement_type", table_name="company_engagements")
    op.drop_index("ix_company_engagements_deadline", table_name="company_engagements")
    op.drop_index("ix_company_engagements_client_name", table_name="company_engagements")
    op.drop_table("company_engagements")

    op.drop_index("ix_company_source_signals_thread_or_meeting_id", table_name="company_source_signals")
    op.drop_index("ix_company_source_signals_status", table_name="company_source_signals")
    op.drop_index("ix_company_source_signals_signal_date", table_name="company_source_signals")
    op.drop_index("ix_company_source_signals_run_id", table_name="company_source_signals")
    op.drop_index("ix_company_source_signals_route", table_name="company_source_signals")
    op.drop_index("ix_company_source_signals_fingerprint", table_name="company_source_signals")
    op.drop_index("ix_company_source_signals_client_name", table_name="company_source_signals")
    op.drop_table("company_source_signals")
