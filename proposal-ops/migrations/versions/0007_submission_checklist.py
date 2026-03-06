"""add submission checklist tables

Revision ID: 0007_submission_checklist
Revises: 0006_review_cycles_and_comments
Create Date: 2026-03-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0007_submission_checklist"
down_revision: Union[str, None] = "0006_review_cycles_and_comments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "submission_checklists",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("opportunity_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="OPEN"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_submission_checklists_opportunity_id", "submission_checklists", ["opportunity_id"], unique=False)

    op.create_table(
        "submission_checklist_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("checklist_id", sa.String(length=36), nullable=False),
        sa.Column("item_code", sa.String(length=50), nullable=False),
        sa.Column("item_label", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=30), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("updated_by", sa.String(length=100), nullable=False, server_default="system"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["checklist_id"], ["submission_checklists.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_submission_checklist_items_checklist_id",
        "submission_checklist_items",
        ["checklist_id"],
        unique=False,
    )
    op.create_index(
        "ix_submission_checklist_items_item_code",
        "submission_checklist_items",
        ["item_code"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_submission_checklist_items_item_code", table_name="submission_checklist_items")
    op.drop_index("ix_submission_checklist_items_checklist_id", table_name="submission_checklist_items")
    op.drop_table("submission_checklist_items")
    op.drop_index("ix_submission_checklists_opportunity_id", table_name="submission_checklists")
    op.drop_table("submission_checklists")

