"""opportunity intelligence foundation

Revision ID: 0028_opportunity_intelligence_foundation
Revises: 0027_ux_friction_feedback
Create Date: 2026-03-09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0028_opportunity_intelligence_foundation"
down_revision: str | Sequence[str] | None = "0027_ux_friction_feedback"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "signal_sources",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("region", sa.String(length=120), nullable=True),
        sa.Column("owner_scope", sa.String(length=120), nullable=True),
        sa.Column("source_url", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_signal_sources_name", "signal_sources", ["name"], unique=True)
    op.create_index("ix_signal_sources_owner_scope", "signal_sources", ["owner_scope"], unique=False)
    op.create_index("ix_signal_sources_region", "signal_sources", ["region"], unique=False)
    op.create_index("ix_signal_sources_source_type", "signal_sources", ["source_type"], unique=False)

    op.create_table(
        "signal_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("signal_type", sa.String(length=40), nullable=False),
        sa.Column("signal_date", sa.Date(), nullable=False),
        sa.Column("jurisdiction", sa.String(length=120), nullable=True),
        sa.Column("agency_name", sa.String(length=255), nullable=True),
        sa.Column("program_name", sa.String(length=255), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("confidence_level", sa.String(length=20), nullable=False),
        sa.Column("source_url", sa.String(length=255), nullable=True),
        sa.Column("source_reference", sa.String(length=255), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["signal_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_signal_events_agency_name", "signal_events", ["agency_name"], unique=False)
    op.create_index("ix_signal_events_confidence_level", "signal_events", ["confidence_level"], unique=False)
    op.create_index("ix_signal_events_jurisdiction", "signal_events", ["jurisdiction"], unique=False)
    op.create_index("ix_signal_events_signal_date", "signal_events", ["signal_date"], unique=False)
    op.create_index("ix_signal_events_signal_type", "signal_events", ["signal_type"], unique=False)
    op.create_index("ix_signal_events_source_id", "signal_events", ["source_id"], unique=False)
    op.create_index("ix_signal_events_title", "signal_events", ["title"], unique=False)

    op.create_table(
        "opportunity_hypotheses",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("sector", sa.String(length=120), nullable=True),
        sa.Column("geography", sa.String(length=120), nullable=True),
        sa.Column("buying_organization", sa.String(length=255), nullable=True),
        sa.Column("service_line", sa.String(length=120), nullable=True),
        sa.Column("stage", sa.String(length=40), nullable=False),
        sa.Column("confidence_level", sa.String(length=20), nullable=False),
        sa.Column("expected_release_start", sa.Date(), nullable=True),
        sa.Column("expected_release_end", sa.Date(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("primary_signal_event_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["primary_signal_event_id"], ["signal_events.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("title", "buying_organization", name="uq_hypothesis_title_buying_org"),
    )
    op.create_index("ix_opportunity_hypotheses_buying_organization", "opportunity_hypotheses", ["buying_organization"], unique=False)
    op.create_index("ix_opportunity_hypotheses_confidence_level", "opportunity_hypotheses", ["confidence_level"], unique=False)
    op.create_index("ix_opportunity_hypotheses_expected_release_end", "opportunity_hypotheses", ["expected_release_end"], unique=False)
    op.create_index("ix_opportunity_hypotheses_expected_release_start", "opportunity_hypotheses", ["expected_release_start"], unique=False)
    op.create_index("ix_opportunity_hypotheses_geography", "opportunity_hypotheses", ["geography"], unique=False)
    op.create_index("ix_opportunity_hypotheses_primary_signal_event_id", "opportunity_hypotheses", ["primary_signal_event_id"], unique=False)
    op.create_index("ix_opportunity_hypotheses_sector", "opportunity_hypotheses", ["sector"], unique=False)
    op.create_index("ix_opportunity_hypotheses_service_line", "opportunity_hypotheses", ["service_line"], unique=False)
    op.create_index("ix_opportunity_hypotheses_stage", "opportunity_hypotheses", ["stage"], unique=False)
    op.create_index("ix_opportunity_hypotheses_title", "opportunity_hypotheses", ["title"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_opportunity_hypotheses_title", table_name="opportunity_hypotheses")
    op.drop_index("ix_opportunity_hypotheses_stage", table_name="opportunity_hypotheses")
    op.drop_index("ix_opportunity_hypotheses_service_line", table_name="opportunity_hypotheses")
    op.drop_index("ix_opportunity_hypotheses_sector", table_name="opportunity_hypotheses")
    op.drop_index("ix_opportunity_hypotheses_primary_signal_event_id", table_name="opportunity_hypotheses")
    op.drop_index("ix_opportunity_hypotheses_geography", table_name="opportunity_hypotheses")
    op.drop_index("ix_opportunity_hypotheses_expected_release_start", table_name="opportunity_hypotheses")
    op.drop_index("ix_opportunity_hypotheses_expected_release_end", table_name="opportunity_hypotheses")
    op.drop_index("ix_opportunity_hypotheses_confidence_level", table_name="opportunity_hypotheses")
    op.drop_index("ix_opportunity_hypotheses_buying_organization", table_name="opportunity_hypotheses")
    op.drop_table("opportunity_hypotheses")

    op.drop_index("ix_signal_events_title", table_name="signal_events")
    op.drop_index("ix_signal_events_source_id", table_name="signal_events")
    op.drop_index("ix_signal_events_signal_type", table_name="signal_events")
    op.drop_index("ix_signal_events_signal_date", table_name="signal_events")
    op.drop_index("ix_signal_events_jurisdiction", table_name="signal_events")
    op.drop_index("ix_signal_events_confidence_level", table_name="signal_events")
    op.drop_index("ix_signal_events_agency_name", table_name="signal_events")
    op.drop_table("signal_events")

    op.drop_index("ix_signal_sources_source_type", table_name="signal_sources")
    op.drop_index("ix_signal_sources_region", table_name="signal_sources")
    op.drop_index("ix_signal_sources_owner_scope", table_name="signal_sources")
    op.drop_index("ix_signal_sources_name", table_name="signal_sources")
    op.drop_table("signal_sources")
