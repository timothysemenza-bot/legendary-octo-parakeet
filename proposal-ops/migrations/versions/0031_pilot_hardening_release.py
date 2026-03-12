"""pilot hardening release

Revision ID: 0031_pilot_hardening_release
Revises: 0030_hypothesis_recommended_contractor
Create Date: 2026-03-10
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0031_pilot_hardening_release"
down_revision: str | Sequence[str] | None = "0030_hypothesis_recommended_contractor"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "opportunity_hypotheses",
        sa.Column("buying_organization_id", sa.String(length=36), nullable=True),
    )
    op.create_index(
        "ix_opportunity_hypotheses_buying_organization_id",
        "opportunity_hypotheses",
        ["buying_organization_id"],
        unique=False,
    )

    op.add_column("contractors", sa.Column("archived_at", sa.DateTime(), nullable=True))
    op.add_column("contractors", sa.Column("archived_by", sa.String(length=120), nullable=True))
    op.add_column("contractors", sa.Column("archive_reason", sa.Text(), nullable=True))
    op.create_index("ix_contractors_archived_at", "contractors", ["archived_at"], unique=False)

    op.add_column("opportunities", sa.Column("archived_at", sa.DateTime(), nullable=True))
    op.add_column("opportunities", sa.Column("archived_by", sa.String(length=120), nullable=True))
    op.add_column("opportunities", sa.Column("archive_reason", sa.Text(), nullable=True))
    op.create_index("ix_opportunities_archived_at", "opportunities", ["archived_at"], unique=False)

    op.create_table(
        "ux_recommendation_checkpoints",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=120), nullable=False),
        sa.Column("page_key", sa.String(length=160), nullable=False),
        sa.Column("path", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("proposed_action", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="APPROVED"),
        sa.Column("owner", sa.String(length=120), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("approved_by", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ux_recommendation_checkpoints_code",
        "ux_recommendation_checkpoints",
        ["code"],
        unique=False,
    )
    op.create_index(
        "ix_ux_recommendation_checkpoints_page_key",
        "ux_recommendation_checkpoints",
        ["page_key"],
        unique=False,
    )
    op.create_index(
        "ix_ux_recommendation_checkpoints_path",
        "ux_recommendation_checkpoints",
        ["path"],
        unique=False,
    )
    op.create_index(
        "ix_ux_recommendation_checkpoints_status",
        "ux_recommendation_checkpoints",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_ux_recommendation_checkpoints_status", table_name="ux_recommendation_checkpoints")
    op.drop_index("ix_ux_recommendation_checkpoints_path", table_name="ux_recommendation_checkpoints")
    op.drop_index("ix_ux_recommendation_checkpoints_page_key", table_name="ux_recommendation_checkpoints")
    op.drop_index("ix_ux_recommendation_checkpoints_code", table_name="ux_recommendation_checkpoints")
    op.drop_table("ux_recommendation_checkpoints")

    op.drop_index("ix_opportunities_archived_at", table_name="opportunities")
    op.drop_column("opportunities", "archive_reason")
    op.drop_column("opportunities", "archived_by")
    op.drop_column("opportunities", "archived_at")

    op.drop_index("ix_contractors_archived_at", table_name="contractors")
    op.drop_column("contractors", "archive_reason")
    op.drop_column("contractors", "archived_by")
    op.drop_column("contractors", "archived_at")

    op.drop_index(
        "ix_opportunity_hypotheses_buying_organization_id",
        table_name="opportunity_hypotheses",
    )
    op.drop_column("opportunity_hypotheses", "buying_organization_id")
