"""add solicitation requirement and compliance matrix tables

Revision ID: 0002_rfp_and_compliance
Revises: 0001_opportunity_intake_core
Create Date: 2026-03-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0002_rfp_and_compliance"
down_revision: Union[str, None] = "0001_opportunity_intake_core"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "solicitations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("opportunity_id", sa.String(length=36), nullable=False),
        sa.Column("source_filename", sa.String(length=255), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("extracted_deadline", sa.String(length=40), nullable=True),
        sa.Column("extracted_evaluation_criteria", sa.Text(), nullable=True),
        sa.Column("extracted_submission_instructions", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_solicitations_opportunity_id", "solicitations", ["opportunity_id"], unique=False)

    op.create_table(
        "requirements",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("solicitation_id", sa.String(length=36), nullable=False),
        sa.Column("requirement_code", sa.String(length=30), nullable=False),
        sa.Column("requirement_text", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("mandatory", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["solicitation_id"], ["solicitations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_requirements_solicitation_id", "requirements", ["solicitation_id"], unique=False)
    op.create_index("ix_requirements_requirement_code", "requirements", ["requirement_code"], unique=False)

    op.create_table(
        "compliance_matrix_rows",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("opportunity_id", sa.String(length=36), nullable=False),
        sa.Column("requirement_id", sa.String(length=36), nullable=False),
        sa.Column("proposal_section", sa.String(length=100), nullable=False),
        sa.Column("owner", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.ForeignKeyConstraint(["requirement_id"], ["requirements.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_compliance_matrix_rows_opportunity_id",
        "compliance_matrix_rows",
        ["opportunity_id"],
        unique=False,
    )
    op.create_index(
        "ix_compliance_matrix_rows_requirement_id",
        "compliance_matrix_rows",
        ["requirement_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_compliance_matrix_rows_requirement_id", table_name="compliance_matrix_rows")
    op.drop_index("ix_compliance_matrix_rows_opportunity_id", table_name="compliance_matrix_rows")
    op.drop_table("compliance_matrix_rows")
    op.drop_index("ix_requirements_requirement_code", table_name="requirements")
    op.drop_index("ix_requirements_solicitation_id", table_name="requirements")
    op.drop_table("requirements")
    op.drop_index("ix_solicitations_opportunity_id", table_name="solicitations")
    op.drop_table("solicitations")

