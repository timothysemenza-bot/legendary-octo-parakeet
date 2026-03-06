"""add requirement_type classification column

Revision ID: 0003_requirement_type
Revises: 0002_rfp_and_compliance
Create Date: 2026-03-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0003_requirement_type"
down_revision: Union[str, None] = "0002_rfp_and_compliance"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "requirements",
        sa.Column(
            "requirement_type",
            sa.String(length=30),
            nullable=False,
            server_default="COMPLIANCE_REQUIRED",
        ),
    )
    op.create_index("ix_requirements_requirement_type", "requirements", ["requirement_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_requirements_requirement_type", table_name="requirements")
    op.drop_column("requirements", "requirement_type")

