"""rfp source document families

Revision ID: 0024_rfp_source_document_families
Revises: 0023_rfp_source_binary_storage
Create Date: 2026-03-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0024_rfp_source_document_families"
down_revision: str | Sequence[str] | None = "0023_rfp_source_binary_storage"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("rfp_source_documents", sa.Column("document_family_id", sa.String(length=36), nullable=True))
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE rfp_source_documents
            SET document_family_id = id
            WHERE document_family_id IS NULL
            """
        )
    )
    op.create_index(
        "ix_rfp_source_documents_document_family_id",
        "rfp_source_documents",
        ["document_family_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_rfp_source_documents_document_family_id", table_name="rfp_source_documents")
    op.drop_column("rfp_source_documents", "document_family_id")
