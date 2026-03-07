"""intake rfp drafts

Revision ID: 0019_intake_rfp_drafts
Revises: 0018_proposal_outlines
Create Date: 2026-03-06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0019_intake_rfp_drafts"
down_revision: str | Sequence[str] | None = "0018_proposal_outlines"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "intake_rfp_drafts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("actor", sa.String(length=100), nullable=False),
        sa.Column("combined_text", sa.Text(), nullable=False),
        sa.Column("source_filename", sa.String(length=255), nullable=False),
        sa.Column("suggested_payload_json", sa.Text(), nullable=False),
        sa.Column("field_status_json", sa.Text(), nullable=False),
        sa.Column("parsed_files_json", sa.Text(), nullable=False),
        sa.Column("skipped_files_json", sa.Text(), nullable=False),
        sa.Column("warnings_json", sa.Text(), nullable=False),
        sa.Column("consumed_opportunity_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["consumed_opportunity_id"], ["opportunities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_intake_rfp_drafts_status", "intake_rfp_drafts", ["status"], unique=False)
    op.create_index(
        "ix_intake_rfp_drafts_consumed_opportunity_id",
        "intake_rfp_drafts",
        ["consumed_opportunity_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_intake_rfp_drafts_consumed_opportunity_id", table_name="intake_rfp_drafts")
    op.drop_index("ix_intake_rfp_drafts_status", table_name="intake_rfp_drafts")
    op.drop_table("intake_rfp_drafts")
