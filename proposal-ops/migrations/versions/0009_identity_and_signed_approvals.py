"""add identity tables and signed approvals

Revision ID: 0009_identity_and_signed_approvals
Revises: 0008_lessons_and_knowledge_promotions
Create Date: 2026-03-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0009_identity_and_signed_approvals"
down_revision: Union[str, None] = "0008_lessons_and_knowledge_promotions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "user_role_assignments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=False),
        sa.Column("scope_type", sa.String(length=20), nullable=False),
        sa.Column("scope_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_user_role_assignments_user_id",
        "user_role_assignments",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_user_role_assignments_scope",
        "user_role_assignments",
        ["scope_type", "scope_id"],
        unique=False,
    )

    op.add_column("gate_decisions", sa.Column("decider_user_id", sa.String(length=36), nullable=True))
    op.add_column("gate_decisions", sa.Column("approval_signature", sa.String(length=128), nullable=True))


def downgrade() -> None:
    op.drop_column("gate_decisions", "approval_signature")
    op.drop_column("gate_decisions", "decider_user_id")
    op.drop_index("ix_user_role_assignments_scope", table_name="user_role_assignments")
    op.drop_index("ix_user_role_assignments_user_id", table_name="user_role_assignments")
    op.drop_table("user_role_assignments")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

