"""notifications

Revision ID: 0010_notifications
Revises: 0009_identity_and_signed_approvals
Create Date: 2026-03-05
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0010_notifications"
down_revision: str | Sequence[str] | None = "0009_identity_and_signed_approvals"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notification_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("opportunity_id", sa.String(length=36), nullable=True),
        sa.Column("gate_code", sa.String(length=30), nullable=True),
        sa.Column("notification_type", sa.String(length=30), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("acknowledged_by", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notification_events_opportunity_id", "notification_events", ["opportunity_id"], unique=False)
    op.create_index("ix_notification_events_gate_code", "notification_events", ["gate_code"], unique=False)
    op.create_index("ix_notification_events_notification_type", "notification_events", ["notification_type"], unique=False)
    op.create_index("ix_notification_events_severity", "notification_events", ["severity"], unique=False)
    op.create_index("ix_notification_events_status", "notification_events", ["status"], unique=False)
    op.create_index("ix_notification_events_created_at", "notification_events", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_notification_events_created_at", table_name="notification_events")
    op.drop_index("ix_notification_events_status", table_name="notification_events")
    op.drop_index("ix_notification_events_severity", table_name="notification_events")
    op.drop_index("ix_notification_events_notification_type", table_name="notification_events")
    op.drop_index("ix_notification_events_gate_code", table_name="notification_events")
    op.drop_index("ix_notification_events_opportunity_id", table_name="notification_events")
    op.drop_table("notification_events")
