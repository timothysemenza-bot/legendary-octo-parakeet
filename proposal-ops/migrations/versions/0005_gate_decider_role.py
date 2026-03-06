"""add gate decider role field

Revision ID: 0005_gate_decider_role
Revises: 0004_gate_rework_packet
Create Date: 2026-03-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0005_gate_decider_role"
down_revision: Union[str, None] = "0004_gate_rework_packet"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "gate_decisions",
        sa.Column("decider_role", sa.String(length=100), nullable=False, server_default="proposal_manager"),
    )


def downgrade() -> None:
    op.drop_column("gate_decisions", "decider_role")

