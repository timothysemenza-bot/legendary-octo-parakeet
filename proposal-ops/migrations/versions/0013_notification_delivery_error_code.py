"""notification delivery error code

Revision ID: 0013_notification_delivery_error_code
Revises: 0012_notification_deliveries
Create Date: 2026-03-05
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0013_notification_delivery_error_code"
down_revision: str | Sequence[str] | None = "0012_notification_deliveries"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("notification_deliveries", sa.Column("last_error_code", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("notification_deliveries", "last_error_code")
