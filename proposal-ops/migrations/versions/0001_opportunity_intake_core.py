"""create opportunity intake core tables

Revision ID: 0001_opportunity_intake_core
Revises:
Create Date: 2026-03-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0001_opportunity_intake_core"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "opportunities",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client", sa.String(length=255), nullable=False),
        sa.Column("estimated_contract_value", sa.Float(), nullable=False),
        sa.Column("lead_time_days", sa.Integer(), nullable=False),
        sa.Column("incumbent_status", sa.Boolean(), nullable=False),
        sa.Column("strategic_alignment", sa.Integer(), nullable=False),
        sa.Column("estimated_probability_win", sa.Integer(), nullable=False),
        sa.Column("qualification_score", sa.Float(), nullable=False),
        sa.Column("tier", sa.String(length=20), nullable=False),
        sa.Column("pursuit_recommendation", sa.String(length=20), nullable=False),
        sa.Column("stage", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_opportunities_name", "opportunities", ["name"], unique=False)
    op.create_index("ix_opportunities_client", "opportunities", ["client"], unique=False)

    op.create_table(
        "capture_plans",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("opportunity_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("client_priorities", sa.Text(), nullable=False),
        sa.Column("competitive_landscape", sa.Text(), nullable=False),
        sa.Column("win_themes_draft", sa.Text(), nullable=False),
        sa.Column("solution_positioning", sa.Text(), nullable=False),
        sa.Column("timeline", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_capture_plans_opportunity_id", "capture_plans", ["opportunity_id"], unique=False)

    op.create_table(
        "gate_decisions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("opportunity_id", sa.String(length=36), nullable=False),
        sa.Column("gate_code", sa.String(length=30), nullable=False),
        sa.Column("decision", sa.String(length=30), nullable=False),
        sa.Column("decider", sa.String(length=100), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_gate_decisions_opportunity_id", "gate_decisions", ["opportunity_id"], unique=False)
    op.create_index("ix_gate_decisions_gate_code", "gate_decisions", ["gate_code"], unique=False)

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("opportunity_id", sa.String(length=36), nullable=True),
        sa.Column("actor", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("before_state_json", sa.Text(), nullable=True),
        sa.Column("after_state_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_opportunity_id", "audit_events", ["opportunity_id"], unique=False)
    op.create_index("ix_audit_events_action", "audit_events", ["action"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_events_action", table_name="audit_events")
    op.drop_index("ix_audit_events_opportunity_id", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_gate_decisions_gate_code", table_name="gate_decisions")
    op.drop_index("ix_gate_decisions_opportunity_id", table_name="gate_decisions")
    op.drop_table("gate_decisions")
    op.drop_index("ix_capture_plans_opportunity_id", table_name="capture_plans")
    op.drop_table("capture_plans")
    op.drop_index("ix_opportunities_client", table_name="opportunities")
    op.drop_index("ix_opportunities_name", table_name="opportunities")
    op.drop_table("opportunities")

