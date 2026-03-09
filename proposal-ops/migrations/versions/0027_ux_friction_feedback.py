"""ux friction feedback

Revision ID: 0027_ux_friction_feedback
Revises: 0026_contractor_prospect_pipeline
Create Date: 2026-03-08
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0027_ux_friction_feedback"
down_revision: str | Sequence[str] | None = "0026_contractor_prospect_pipeline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ux_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=120), nullable=False),
        sa.Column("actor", sa.String(length=120), nullable=True),
        sa.Column("page_key", sa.String(length=160), nullable=False),
        sa.Column("path", sa.String(length=255), nullable=False),
        sa.Column("referrer_path", sa.String(length=255), nullable=True),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("form_name", sa.String(length=160), nullable=True),
        sa.Column("target_key", sa.String(length=160), nullable=True),
        sa.Column("field_name", sa.String(length=160), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("count_value", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ux_events_actor", "ux_events", ["actor"], unique=False)
    op.create_index("ix_ux_events_created_at", "ux_events", ["created_at"], unique=False)
    op.create_index("ix_ux_events_event_type", "ux_events", ["event_type"], unique=False)
    op.create_index("ix_ux_events_field_name", "ux_events", ["field_name"], unique=False)
    op.create_index("ix_ux_events_form_name", "ux_events", ["form_name"], unique=False)
    op.create_index("ix_ux_events_page_key", "ux_events", ["page_key"], unique=False)
    op.create_index("ix_ux_events_path", "ux_events", ["path"], unique=False)
    op.create_index("ix_ux_events_referrer_path", "ux_events", ["referrer_path"], unique=False)
    op.create_index("ix_ux_events_session_id", "ux_events", ["session_id"], unique=False)

    op.create_table(
        "ux_feedback",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=120), nullable=False),
        sa.Column("actor", sa.String(length=120), nullable=True),
        sa.Column("page_key", sa.String(length=160), nullable=False),
        sa.Column("path", sa.String(length=255), nullable=False),
        sa.Column("form_name", sa.String(length=160), nullable=True),
        sa.Column("feedback_type", sa.String(length=40), nullable=False),
        sa.Column("note_text", sa.Text(), nullable=True),
        sa.Column("context_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("voice_note_status", sa.String(length=40), nullable=False, server_default="NOT_PROVIDED"),
        sa.Column("voice_note_asset_ref", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ux_feedback_actor", "ux_feedback", ["actor"], unique=False)
    op.create_index("ix_ux_feedback_created_at", "ux_feedback", ["created_at"], unique=False)
    op.create_index("ix_ux_feedback_feedback_type", "ux_feedback", ["feedback_type"], unique=False)
    op.create_index("ix_ux_feedback_form_name", "ux_feedback", ["form_name"], unique=False)
    op.create_index("ix_ux_feedback_page_key", "ux_feedback", ["page_key"], unique=False)
    op.create_index("ix_ux_feedback_path", "ux_feedback", ["path"], unique=False)
    op.create_index("ix_ux_feedback_session_id", "ux_feedback", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ux_feedback_session_id", table_name="ux_feedback")
    op.drop_index("ix_ux_feedback_path", table_name="ux_feedback")
    op.drop_index("ix_ux_feedback_page_key", table_name="ux_feedback")
    op.drop_index("ix_ux_feedback_form_name", table_name="ux_feedback")
    op.drop_index("ix_ux_feedback_feedback_type", table_name="ux_feedback")
    op.drop_index("ix_ux_feedback_created_at", table_name="ux_feedback")
    op.drop_index("ix_ux_feedback_actor", table_name="ux_feedback")
    op.drop_table("ux_feedback")

    op.drop_index("ix_ux_events_session_id", table_name="ux_events")
    op.drop_index("ix_ux_events_referrer_path", table_name="ux_events")
    op.drop_index("ix_ux_events_path", table_name="ux_events")
    op.drop_index("ix_ux_events_page_key", table_name="ux_events")
    op.drop_index("ix_ux_events_form_name", table_name="ux_events")
    op.drop_index("ix_ux_events_field_name", table_name="ux_events")
    op.drop_index("ix_ux_events_event_type", table_name="ux_events")
    op.drop_index("ix_ux_events_created_at", table_name="ux_events")
    op.drop_index("ix_ux_events_actor", table_name="ux_events")
    op.drop_table("ux_events")
