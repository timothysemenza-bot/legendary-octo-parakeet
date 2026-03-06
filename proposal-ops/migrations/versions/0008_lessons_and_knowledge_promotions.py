"""add lessons learned and knowledge promotion tables

Revision ID: 0008_lessons_and_knowledge_promotions
Revises: 0007_submission_checklist
Create Date: 2026-03-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0008_lessons_and_knowledge_promotions"
down_revision: Union[str, None] = "0007_submission_checklist"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lessons_learned_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("opportunity_id", sa.String(length=36), nullable=False),
        sa.Column("outcome", sa.String(length=30), nullable=False),
        sa.Column("root_causes_json", sa.Text(), nullable=False),
        sa.Column("actions_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="DRAFT"),
        sa.Column("created_by", sa.String(length=100), nullable=False),
        sa.Column("approved_by", sa.String(length=100), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_lessons_learned_records_opportunity_id",
        "lessons_learned_records",
        ["opportunity_id"],
        unique=False,
    )
    op.create_index("ix_lessons_learned_records_status", "lessons_learned_records", ["status"], unique=False)

    op.create_table(
        "knowledge_promotions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("lessons_record_id", sa.String(length=36), nullable=False),
        sa.Column("asset_title", sa.String(length=255), nullable=False),
        sa.Column("asset_type", sa.String(length=50), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("promotion_status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("created_by", sa.String(length=100), nullable=False),
        sa.Column("decided_by", sa.String(length=100), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["lessons_record_id"], ["lessons_learned_records.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_knowledge_promotions_lessons_record_id",
        "knowledge_promotions",
        ["lessons_record_id"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_promotions_promotion_status",
        "knowledge_promotions",
        ["promotion_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_promotions_promotion_status", table_name="knowledge_promotions")
    op.drop_index("ix_knowledge_promotions_lessons_record_id", table_name="knowledge_promotions")
    op.drop_table("knowledge_promotions")
    op.drop_index("ix_lessons_learned_records_status", table_name="lessons_learned_records")
    op.drop_index("ix_lessons_learned_records_opportunity_id", table_name="lessons_learned_records")
    op.drop_table("lessons_learned_records")

