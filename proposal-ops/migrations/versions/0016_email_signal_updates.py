"""email signal updates

Revision ID: 0016_email_signal_updates
Revises: 0015_notification_policy_client_mapping
Create Date: 2026-03-06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0016_email_signal_updates"
down_revision: str | Sequence[str] | None = "0015_notification_policy_client_mapping"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "email_signal_updates",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("external_message_id", sa.String(length=255), nullable=True),
        sa.Column("opportunity_id", sa.String(length=36), nullable=True),
        sa.Column("from_address", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=False),
        sa.Column("body_excerpt", sa.Text(), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("signal_type", sa.String(length=50), nullable=False),
        sa.Column("proposed_bid_status", sa.String(length=30), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("auto_applied", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("applied_at", sa.DateTime(), nullable=True),
        sa.Column("applied_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_email_signal_updates_external_message_id",
        "email_signal_updates",
        ["external_message_id"],
        unique=False,
    )
    op.create_index(
        "ix_email_signal_updates_opportunity_id",
        "email_signal_updates",
        ["opportunity_id"],
        unique=False,
    )
    op.create_index(
        "ix_email_signal_updates_received_at",
        "email_signal_updates",
        ["received_at"],
        unique=False,
    )
    op.create_index(
        "ix_email_signal_updates_signal_type",
        "email_signal_updates",
        ["signal_type"],
        unique=False,
    )
    op.create_index(
        "ix_email_signal_updates_status",
        "email_signal_updates",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_email_signal_updates_created_at",
        "email_signal_updates",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_email_signal_updates_created_at", table_name="email_signal_updates")
    op.drop_index("ix_email_signal_updates_status", table_name="email_signal_updates")
    op.drop_index("ix_email_signal_updates_signal_type", table_name="email_signal_updates")
    op.drop_index("ix_email_signal_updates_received_at", table_name="email_signal_updates")
    op.drop_index("ix_email_signal_updates_opportunity_id", table_name="email_signal_updates")
    op.drop_index("ix_email_signal_updates_external_message_id", table_name="email_signal_updates")
    op.drop_table("email_signal_updates")
