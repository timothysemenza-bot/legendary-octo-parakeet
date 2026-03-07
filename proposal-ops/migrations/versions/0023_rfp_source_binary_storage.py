"""rfp source binary storage

Revision ID: 0023_rfp_source_binary_storage
Revises: 0022_rfp_source_document_content
Create Date: 2026-03-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0023_rfp_source_binary_storage"
down_revision: str | Sequence[str] | None = "0022_rfp_source_document_content"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("rfp_source_documents", sa.Column("source_sha256", sa.String(length=64), nullable=True))
    op.add_column("rfp_source_documents", sa.Column("storage_path", sa.String(length=255), nullable=True))
    op.create_index(
        "ix_rfp_source_documents_source_sha256",
        "rfp_source_documents",
        ["source_sha256"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_rfp_source_documents_source_sha256", table_name="rfp_source_documents")
    op.drop_column("rfp_source_documents", "storage_path")
    op.drop_column("rfp_source_documents", "source_sha256")
