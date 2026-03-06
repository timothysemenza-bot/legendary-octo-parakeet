"""notification deliveries

Revision ID: 0012_notification_deliveries
Revises: 0011_notification_routing_fields
Create Date: 2026-03-05
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0012_notification_deliveries"
down_revision: str | Sequence[str] | None = "0011_notification_routing_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notification_deliveries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("notification_id", sa.String(length=36), nullable=False),
        sa.Column("channel", sa.String(length=30), nullable=False),
        sa.Column("target", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("last_response", sa.Text(), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(), nullable=True),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["notification_id"], ["notification_events.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notification_deliveries_notification_id", "notification_deliveries", ["notification_id"], unique=False)
    op.create_index("ix_notification_deliveries_channel", "notification_deliveries", ["channel"], unique=False)
    op.create_index("ix_notification_deliveries_target", "notification_deliveries", ["target"], unique=False)
    op.create_index("ix_notification_deliveries_status", "notification_deliveries", ["status"], unique=False)
    op.create_index("ix_notification_deliveries_created_at", "notification_deliveries", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_notification_deliveries_created_at", table_name="notification_deliveries")
    op.drop_index("ix_notification_deliveries_status", table_name="notification_deliveries")
    op.drop_index("ix_notification_deliveries_target", table_name="notification_deliveries")
    op.drop_index("ix_notification_deliveries_channel", table_name="notification_deliveries")
    op.drop_index("ix_notification_deliveries_notification_id", table_name="notification_deliveries")
    op.drop_table("notification_deliveries")
