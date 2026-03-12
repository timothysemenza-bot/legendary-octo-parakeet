"""hypothesis pursuit conversion

Revision ID: 0029_hypothesis_pursuit_conversion
Revises: 0028_opportunity_intelligence_foundation
Create Date: 2026-03-09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0029_hypothesis_pursuit_conversion"
down_revision: str | Sequence[str] | None = "0028_opportunity_intelligence_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "opportunity_hypotheses",
        sa.Column("converted_opportunity_id", sa.String(length=36), nullable=True),
    )
    op.add_column(
        "opportunity_hypotheses",
        sa.Column("converted_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_opportunity_hypotheses_converted_opportunity_id",
        "opportunity_hypotheses",
        ["converted_opportunity_id"],
        unique=False,
    )
    op.create_index(
        "ix_opportunity_hypotheses_converted_at",
        "opportunity_hypotheses",
        ["converted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_opportunity_hypotheses_converted_at", table_name="opportunity_hypotheses")
    op.drop_index("ix_opportunity_hypotheses_converted_opportunity_id", table_name="opportunity_hypotheses")
    op.drop_column("opportunity_hypotheses", "converted_at")
    op.drop_column("opportunity_hypotheses", "converted_opportunity_id")
