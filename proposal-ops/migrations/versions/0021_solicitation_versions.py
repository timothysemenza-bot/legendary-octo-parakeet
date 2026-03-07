"""solicitation versions

Revision ID: 0021_solicitation_versions
Revises: 0020_rfp_source_documents
Create Date: 2026-03-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0021_solicitation_versions"
down_revision: str | Sequence[str] | None = "0020_rfp_source_documents"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("solicitations", sa.Column("version", sa.Integer(), nullable=True, server_default="1"))

    bind = op.get_bind()
    rows = bind.execute(
        sa.text("SELECT id, opportunity_id FROM solicitations ORDER BY opportunity_id ASC, created_at ASC, id ASC")
    ).mappings()
    counters: dict[str, int] = {}
    for row in rows:
        opportunity_id = row["opportunity_id"]
        counters[opportunity_id] = counters.get(opportunity_id, 0) + 1
        bind.execute(
            sa.text("UPDATE solicitations SET version = :version WHERE id = :id"),
            {"version": counters[opportunity_id], "id": row["id"]},
        )

    with op.batch_alter_table("solicitations") as batch_op:
        batch_op.alter_column("version", nullable=False, server_default=None)
        batch_op.create_index("ix_solicitations_version", ["version"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("solicitations") as batch_op:
        batch_op.drop_index("ix_solicitations_version")
        batch_op.drop_column("version")
