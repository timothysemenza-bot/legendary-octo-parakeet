"""notification policy config

Revision ID: 0014_notification_policy_config
Revises: 0013_notification_delivery_error_code
Create Date: 2026-03-05
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0014_notification_policy_config"
down_revision: str | Sequence[str] | None = "0013_notification_delivery_error_code"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notification_policy_configs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("policy_key", sa.String(length=80), nullable=False),
        sa.Column("policy_json", sa.Text(), nullable=False),
        sa.Column("updated_by", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notification_policy_configs_policy_key", "notification_policy_configs", ["policy_key"], unique=True)
    op.create_index("ix_notification_policy_configs_created_at", "notification_policy_configs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_notification_policy_configs_created_at", table_name="notification_policy_configs")
    op.drop_index("ix_notification_policy_configs_policy_key", table_name="notification_policy_configs")
    op.drop_table("notification_policy_configs")
