"""proposal outlines

Revision ID: 0018_proposal_outlines
Revises: 0017_email_connections
Create Date: 2026-03-06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0018_proposal_outlines"
down_revision: str | Sequence[str] | None = "0017_email_connections"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "proposal_outlines",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("opportunity_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("sections_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_proposal_outlines_opportunity_id", "proposal_outlines", ["opportunity_id"], unique=False)
    op.create_index("ix_proposal_outlines_version", "proposal_outlines", ["version"], unique=False)
    op.create_index("ix_proposal_outlines_created_at", "proposal_outlines", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_proposal_outlines_created_at", table_name="proposal_outlines")
    op.drop_index("ix_proposal_outlines_version", table_name="proposal_outlines")
    op.drop_index("ix_proposal_outlines_opportunity_id", table_name="proposal_outlines")
    op.drop_table("proposal_outlines")
