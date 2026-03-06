"""notification routing fields

Revision ID: 0011_notification_routing_fields
Revises: 0010_notifications
Create Date: 2026-03-05
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0011_notification_routing_fields"
down_revision: str | Sequence[str] | None = "0010_notifications"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("notification_events", sa.Column("escalation_tier", sa.Integer(), nullable=True))
    op.add_column("notification_events", sa.Column("recipients_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("notification_events", "recipients_json")
    op.drop_column("notification_events", "escalation_tier")
