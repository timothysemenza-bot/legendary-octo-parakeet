"""rfp source documents

Revision ID: 0020_rfp_source_documents
Revises: 0019_intake_rfp_drafts
Create Date: 2026-03-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0020_rfp_source_documents"
down_revision: str | Sequence[str] | None = "0019_intake_rfp_drafts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "rfp_source_documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("intake_rfp_draft_id", sa.String(length=36), nullable=True),
        sa.Column("solicitation_id", sa.String(length=36), nullable=True),
        sa.Column("source_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("parse_status", sa.String(length=20), nullable=False),
        sa.Column("skip_reason", sa.Text(), nullable=True),
        sa.Column("upload_order", sa.Integer(), nullable=False),
        sa.Column("source_size_bytes", sa.Integer(), nullable=False),
        sa.Column("extracted_text_length", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["intake_rfp_draft_id"], ["intake_rfp_drafts.id"]),
        sa.ForeignKeyConstraint(["solicitation_id"], ["solicitations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_rfp_source_documents_intake_rfp_draft_id",
        "rfp_source_documents",
        ["intake_rfp_draft_id"],
        unique=False,
    )
    op.create_index(
        "ix_rfp_source_documents_solicitation_id",
        "rfp_source_documents",
        ["solicitation_id"],
        unique=False,
    )
    op.create_index(
        "ix_rfp_source_documents_parse_status",
        "rfp_source_documents",
        ["parse_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_rfp_source_documents_parse_status", table_name="rfp_source_documents")
    op.drop_index("ix_rfp_source_documents_solicitation_id", table_name="rfp_source_documents")
    op.drop_index("ix_rfp_source_documents_intake_rfp_draft_id", table_name="rfp_source_documents")
    op.drop_table("rfp_source_documents")
