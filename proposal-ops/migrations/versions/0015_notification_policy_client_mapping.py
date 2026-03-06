"""notification policy client mapping

Revision ID: 0015_notification_policy_client_mapping
Revises: 0014_notification_policy_config
Create Date: 2026-03-06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0015_notification_policy_client_mapping"
down_revision: str | Sequence[str] | None = "0014_notification_policy_config"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notification_policy_client_mappings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("client_name", sa.String(length=255), nullable=False),
        sa.Column("policy_key", sa.String(length=80), nullable=False),
        sa.Column("updated_by", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notification_policy_client_mappings_client_name",
        "notification_policy_client_mappings",
        ["client_name"],
        unique=True,
    )
    op.create_index(
        "ix_notification_policy_client_mappings_policy_key",
        "notification_policy_client_mappings",
        ["policy_key"],
        unique=False,
    )
    op.create_index(
        "ix_notification_policy_client_mappings_created_at",
        "notification_policy_client_mappings",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_notification_policy_client_mappings_created_at",
        table_name="notification_policy_client_mappings",
    )
    op.drop_index(
        "ix_notification_policy_client_mappings_policy_key",
        table_name="notification_policy_client_mappings",
    )
    op.drop_index(
        "ix_notification_policy_client_mappings_client_name",
        table_name="notification_policy_client_mappings",
    )
    op.drop_table("notification_policy_client_mappings")
