"""add rework packet fields to gate decisions

Revision ID: 0004_gate_rework_packet
Revises: 0003_requirement_type
Create Date: 2026-03-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0004_gate_rework_packet"
down_revision: Union[str, None] = "0003_requirement_type"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("gate_decisions", sa.Column("rework_instructions", sa.Text(), nullable=True))
    op.add_column("gate_decisions", sa.Column("rework_owner", sa.String(length=100), nullable=True))
    op.add_column("gate_decisions", sa.Column("rework_due_date", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("gate_decisions", "rework_due_date")
    op.drop_column("gate_decisions", "rework_owner")
    op.drop_column("gate_decisions", "rework_instructions")

