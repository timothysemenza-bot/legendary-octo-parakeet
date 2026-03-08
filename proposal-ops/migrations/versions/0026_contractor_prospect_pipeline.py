"""contractor prospect pipeline

Revision ID: 0026_contractor_prospect_pipeline
Revises: 0025_janitorial_capture_os_foundation
Create Date: 2026-03-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0026_contractor_prospect_pipeline"
down_revision: str | Sequence[str] | None = "0025_janitorial_capture_os_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "contractors",
        sa.Column("prospect_stage", sa.String(length=30), nullable=False, server_default="TARGET"),
    )
    op.add_column("contractors", sa.Column("next_follow_up_date", sa.Date(), nullable=True))
    op.add_column("contractors", sa.Column("last_touch_at", sa.DateTime(), nullable=True))
    op.create_index("ix_contractors_prospect_stage", "contractors", ["prospect_stage"], unique=False)
    op.create_index("ix_contractors_next_follow_up_date", "contractors", ["next_follow_up_date"], unique=False)
    op.create_index("ix_contractors_last_touch_at", "contractors", ["last_touch_at"], unique=False)

    op.create_table(
        "contractor_touchpoints",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("contractor_id", sa.String(length=36), nullable=False),
        sa.Column("contact_name", sa.String(length=120), nullable=True),
        sa.Column("touchpoint_type", sa.String(length=30), nullable=False),
        sa.Column("touchpoint_at", sa.DateTime(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("next_step", sa.Text(), nullable=True),
        sa.Column("next_follow_up_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["contractor_id"], ["contractors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_contractor_touchpoints_contractor_id", "contractor_touchpoints", ["contractor_id"], unique=False)
    op.create_index("ix_contractor_touchpoints_touchpoint_type", "contractor_touchpoints", ["touchpoint_type"], unique=False)
    op.create_index("ix_contractor_touchpoints_touchpoint_at", "contractor_touchpoints", ["touchpoint_at"], unique=False)
    op.create_index(
        "ix_contractor_touchpoints_next_follow_up_date",
        "contractor_touchpoints",
        ["next_follow_up_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_contractor_touchpoints_next_follow_up_date", table_name="contractor_touchpoints")
    op.drop_index("ix_contractor_touchpoints_touchpoint_at", table_name="contractor_touchpoints")
    op.drop_index("ix_contractor_touchpoints_touchpoint_type", table_name="contractor_touchpoints")
    op.drop_index("ix_contractor_touchpoints_contractor_id", table_name="contractor_touchpoints")
    op.drop_table("contractor_touchpoints")

    op.drop_index("ix_contractors_last_touch_at", table_name="contractors")
    op.drop_index("ix_contractors_next_follow_up_date", table_name="contractors")
    op.drop_index("ix_contractors_prospect_stage", table_name="contractors")
    op.drop_column("contractors", "last_touch_at")
    op.drop_column("contractors", "next_follow_up_date")
    op.drop_column("contractors", "prospect_stage")
