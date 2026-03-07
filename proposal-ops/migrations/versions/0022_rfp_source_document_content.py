"""rfp source document content

Revision ID: 0022_rfp_source_document_content
Revises: 0021_solicitation_versions
Create Date: 2026-03-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0022_rfp_source_document_content"
down_revision: str | Sequence[str] | None = "0021_solicitation_versions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _extract_document_text(solicitation_text: str, filename: str, next_filename: str | None) -> str | None:
    marker = f"Source file: {filename}\n"
    start = solicitation_text.find(marker)
    if start < 0:
        return None
    content_start = start + len(marker)
    if next_filename:
        next_marker = f"\n\nSource file: {next_filename}\n"
        end = solicitation_text.find(next_marker, content_start)
        if end >= 0:
            return solicitation_text[content_start:end].strip() or None
    return solicitation_text[content_start:].strip() or None


def upgrade() -> None:
    op.add_column("rfp_source_documents", sa.Column("content_text", sa.Text(), nullable=True))

    bind = op.get_bind()
    solicitations = bind.execute(
        sa.text("SELECT id, content_text FROM solicitations ORDER BY created_at ASC, id ASC")
    ).mappings()
    for solicitation in solicitations:
        documents = list(
            bind.execute(
                sa.text(
                    """
                    SELECT id, source_filename, parse_status, upload_order
                    FROM rfp_source_documents
                    WHERE solicitation_id = :solicitation_id
                    ORDER BY upload_order ASC, created_at ASC, id ASC
                    """
                ),
                {"solicitation_id": solicitation["id"]},
            ).mappings()
        )
        parsed_documents = [row for row in documents if row["parse_status"] == "PARSED"]
        if not parsed_documents:
            continue

        if len(parsed_documents) == 1:
            bind.execute(
                sa.text("UPDATE rfp_source_documents SET content_text = :content_text WHERE id = :id"),
                {"content_text": solicitation["content_text"], "id": parsed_documents[0]["id"]},
            )
            continue

        for idx, row in enumerate(parsed_documents):
            next_filename = parsed_documents[idx + 1]["source_filename"] if idx + 1 < len(parsed_documents) else None
            extracted = _extract_document_text(solicitation["content_text"], row["source_filename"], next_filename)
            if extracted is not None:
                bind.execute(
                    sa.text("UPDATE rfp_source_documents SET content_text = :content_text WHERE id = :id"),
                    {"content_text": extracted, "id": row["id"]},
                )


def downgrade() -> None:
    op.drop_column("rfp_source_documents", "content_text")
