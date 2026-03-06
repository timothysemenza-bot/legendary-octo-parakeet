"""email connections

Revision ID: 0017_email_connections
Revises: 0016_email_signal_updates
Create Date: 2026-03-06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0017_email_connections"
down_revision: str | Sequence[str] | None = "0016_email_signal_updates"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "email_connections",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("inbox_address", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("config_json", sa.Text(), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_connections_provider", "email_connections", ["provider"], unique=False)
    op.create_index("ix_email_connections_inbox_address", "email_connections", ["inbox_address"], unique=True)
    op.create_index("ix_email_connections_status", "email_connections", ["status"], unique=False)
    op.create_index("ix_email_connections_created_at", "email_connections", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_email_connections_created_at", table_name="email_connections")
    op.drop_index("ix_email_connections_status", table_name="email_connections")
    op.drop_index("ix_email_connections_inbox_address", table_name="email_connections")
    op.drop_index("ix_email_connections_provider", table_name="email_connections")
    op.drop_table("email_connections")
