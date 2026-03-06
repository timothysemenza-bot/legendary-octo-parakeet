"""add review cycles and comments tables

Revision ID: 0006_review_cycles_and_comments
Revises: 0005_gate_decider_role
Create Date: 2026-03-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0006_review_cycles_and_comments"
down_revision: Union[str, None] = "0005_gate_decider_role"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "review_cycles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("opportunity_id", sa.String(length=36), nullable=False),
        sa.Column("review_type", sa.String(length=20), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="OPEN"),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_cycles_opportunity_id", "review_cycles", ["opportunity_id"], unique=False)
    op.create_index("ix_review_cycles_review_type", "review_cycles", ["review_type"], unique=False)

    op.create_table(
        "review_comments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("review_cycle_id", sa.String(length=36), nullable=False),
        sa.Column("requirement_id", sa.String(length=36), nullable=True),
        sa.Column("section_code", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("comment_text", sa.Text(), nullable=False),
        sa.Column("resolution_status", sa.String(length=20), nullable=False, server_default="OPEN"),
        sa.Column("owner", sa.String(length=100), nullable=False, server_default="UNASSIGNED"),
        sa.Column("created_by", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["review_cycle_id"], ["review_cycles.id"]),
        sa.ForeignKeyConstraint(["requirement_id"], ["requirements.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_comments_review_cycle_id", "review_comments", ["review_cycle_id"], unique=False)
    op.create_index("ix_review_comments_severity", "review_comments", ["severity"], unique=False)
    op.create_index("ix_review_comments_resolution_status", "review_comments", ["resolution_status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_review_comments_resolution_status", table_name="review_comments")
    op.drop_index("ix_review_comments_severity", table_name="review_comments")
    op.drop_index("ix_review_comments_review_cycle_id", table_name="review_comments")
    op.drop_table("review_comments")
    op.drop_index("ix_review_cycles_review_type", table_name="review_cycles")
    op.drop_index("ix_review_cycles_opportunity_id", table_name="review_cycles")
    op.drop_table("review_cycles")

