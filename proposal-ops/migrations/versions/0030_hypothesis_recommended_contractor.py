"""hypothesis recommended contractor

Revision ID: 0030_hypothesis_recommended_contractor
Revises: 0029_hypothesis_pursuit_conversion
Create Date: 2026-03-10
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0030_hypothesis_recommended_contractor"
down_revision: str | Sequence[str] | None = "0029_hypothesis_pursuit_conversion"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "opportunity_hypotheses",
        sa.Column("recommended_contractor_id", sa.String(length=36), nullable=True),
    )
    op.create_index(
        "ix_opportunity_hypotheses_recommended_contractor_id",
        "opportunity_hypotheses",
        ["recommended_contractor_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_opportunity_hypotheses_recommended_contractor_id", table_name="opportunity_hypotheses")
    op.drop_column("opportunity_hypotheses", "recommended_contractor_id")
