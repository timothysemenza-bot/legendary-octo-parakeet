"""growth relationship source of truth

Revision ID: 0032_growth_relationship_source_of_truth
Revises: 0031_pilot_hardening_release
Create Date: 2026-03-15
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0032_growth_relationship_source_of_truth"
down_revision: str | Sequence[str] | None = "0031_pilot_hardening_release"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "growth_relationship_profiles",
        sa.Column("relationship_id", sa.String(length=120), nullable=False),
        sa.Column("contractor_id", sa.String(length=36), nullable=False),
        sa.Column("current_opportunity_id", sa.String(length=36), nullable=True),
        sa.Column("created_date", sa.Date(), nullable=True),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("contact_name", sa.String(length=120), nullable=True),
        sa.Column("role", sa.String(length=120), nullable=True),
        sa.Column("linkedin_profile_url", sa.String(length=255), nullable=True),
        sa.Column("linkedin_company_url", sa.String(length=255), nullable=True),
        sa.Column("relationship_stage", sa.String(length=40), nullable=False, server_default="queued"),
        sa.Column("warm_signal", sa.String(length=80), nullable=True),
        sa.Column("fit_confirmed", sa.String(length=10), nullable=False, server_default="no"),
        sa.Column("pain_point", sa.Text(), nullable=True),
        sa.Column("desired_outcome", sa.Text(), nullable=True),
        sa.Column("offer_hypothesis", sa.String(length=255), nullable=True),
        sa.Column("urgency_level", sa.String(length=40), nullable=True),
        sa.Column("scope_breadth", sa.String(length=40), nullable=True),
        sa.Column("stakeholder_complexity", sa.String(length=40), nullable=True),
        sa.Column("research_load", sa.String(length=40), nullable=True),
        sa.Column("delivery_intensity", sa.String(length=40), nullable=True),
        sa.Column("last_touch_date", sa.Date(), nullable=True),
        sa.Column("last_interaction_summary", sa.Text(), nullable=True),
        sa.Column("next_best_touch_type", sa.String(length=60), nullable=True),
        sa.Column("next_best_touch_path", sa.String(length=255), nullable=True),
        sa.Column("meeting_needed", sa.String(length=10), nullable=False, server_default="no"),
        sa.Column("meeting_status", sa.String(length=60), nullable=True),
        sa.Column("proposal_status", sa.String(length=60), nullable=True),
        sa.Column("ptw_status", sa.String(length=60), nullable=True),
        sa.Column("ptw_stage", sa.String(length=60), nullable=True),
        sa.Column("ptw_recommendation", sa.String(length=60), nullable=True),
        sa.Column("ptw_record_id", sa.String(length=120), nullable=True),
        sa.Column("owner_decision", sa.String(length=20), nullable=False, server_default="hold"),
        sa.Column(
            "review_status",
            sa.String(length=40),
            nullable=False,
            server_default="pending-review",
        ),
        sa.Column(
            "ready_state",
            sa.String(length=60),
            nullable=False,
            server_default="draft-pending-review",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["contractor_id"], ["contractors.id"]),
        sa.ForeignKeyConstraint(["current_opportunity_id"], ["opportunities.id"]),
        sa.PrimaryKeyConstraint("relationship_id"),
        sa.UniqueConstraint("contractor_id", name="uq_growth_relationship_profiles_contractor_id"),
    )
    op.create_index(
        "ix_growth_relationship_profiles_company_name",
        "growth_relationship_profiles",
        ["company_name"],
        unique=False,
    )
    op.create_index(
        "ix_growth_relationship_profiles_contractor_id",
        "growth_relationship_profiles",
        ["contractor_id"],
        unique=False,
    )
    op.create_index(
        "ix_growth_relationship_profiles_current_opportunity_id",
        "growth_relationship_profiles",
        ["current_opportunity_id"],
        unique=False,
    )
    op.create_index(
        "ix_growth_relationship_profiles_last_touch_date",
        "growth_relationship_profiles",
        ["last_touch_date"],
        unique=False,
    )
    op.create_index(
        "ix_growth_relationship_profiles_relationship_stage",
        "growth_relationship_profiles",
        ["relationship_stage"],
        unique=False,
    )

    op.create_table(
        "growth_market_evidence",
        sa.Column("knowledge_id", sa.String(length=120), nullable=False),
        sa.Column("relationship_id", sa.String(length=120), nullable=True),
        sa.Column("contractor_id", sa.String(length=36), nullable=True),
        sa.Column("opportunity_id", sa.String(length=36), nullable=True),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("entity_type", sa.String(length=60), nullable=True),
        sa.Column("entity_name", sa.String(length=255), nullable=True),
        sa.Column("source_type", sa.String(length=80), nullable=True),
        sa.Column("source_reference", sa.Text(), nullable=True),
        sa.Column("source_date", sa.Date(), nullable=True),
        sa.Column("source_reliability", sa.String(length=40), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column("customer_objective", sa.Text(), nullable=True),
        sa.Column("customer_need", sa.Text(), nullable=True),
        sa.Column("customer_value_drivers", sa.Text(), nullable=True),
        sa.Column("buyer_priorities", sa.Text(), nullable=True),
        sa.Column("evaluation_priorities", sa.Text(), nullable=True),
        sa.Column("buying_behavior", sa.Text(), nullable=True),
        sa.Column("delivery_context", sa.Text(), nullable=True),
        sa.Column("timing_context", sa.Text(), nullable=True),
        sa.Column("budget_signal", sa.Text(), nullable=True),
        sa.Column("budget_band", sa.String(length=120), nullable=True),
        sa.Column("competitor_name", sa.Text(), nullable=True),
        sa.Column("incumbent_status", sa.String(length=60), nullable=True),
        sa.Column("alternative_option", sa.Text(), nullable=True),
        sa.Column("big4_technical", sa.Text(), nullable=True),
        sa.Column("big4_management", sa.Text(), nullable=True),
        sa.Column("big4_past_performance", sa.Text(), nullable=True),
        sa.Column("big4_cost_price", sa.Text(), nullable=True),
        sa.Column("differentiation_hypothesis", sa.Text(), nullable=True),
        sa.Column("evidence_summary", sa.Text(), nullable=True),
        sa.Column("assumptions", sa.Text(), nullable=True),
        sa.Column("ethical_use_check", sa.String(length=10), nullable=False, server_default="yes"),
        sa.Column("last_validated_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["relationship_id"], ["growth_relationship_profiles.relationship_id"]),
        sa.ForeignKeyConstraint(["contractor_id"], ["contractors.id"]),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.PrimaryKeyConstraint("knowledge_id"),
    )
    op.create_index(
        "ix_growth_market_evidence_company_name",
        "growth_market_evidence",
        ["company_name"],
        unique=False,
    )
    op.create_index(
        "ix_growth_market_evidence_contractor_id",
        "growth_market_evidence",
        ["contractor_id"],
        unique=False,
    )
    op.create_index(
        "ix_growth_market_evidence_entity_type",
        "growth_market_evidence",
        ["entity_type"],
        unique=False,
    )
    op.create_index(
        "ix_growth_market_evidence_opportunity_id",
        "growth_market_evidence",
        ["opportunity_id"],
        unique=False,
    )
    op.create_index(
        "ix_growth_market_evidence_relationship_id",
        "growth_market_evidence",
        ["relationship_id"],
        unique=False,
    )
    op.create_index(
        "ix_growth_market_evidence_source_date",
        "growth_market_evidence",
        ["source_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_growth_market_evidence_source_date", table_name="growth_market_evidence")
    op.drop_index("ix_growth_market_evidence_relationship_id", table_name="growth_market_evidence")
    op.drop_index("ix_growth_market_evidence_opportunity_id", table_name="growth_market_evidence")
    op.drop_index("ix_growth_market_evidence_entity_type", table_name="growth_market_evidence")
    op.drop_index("ix_growth_market_evidence_contractor_id", table_name="growth_market_evidence")
    op.drop_index("ix_growth_market_evidence_company_name", table_name="growth_market_evidence")
    op.drop_table("growth_market_evidence")

    op.drop_index(
        "ix_growth_relationship_profiles_relationship_stage",
        table_name="growth_relationship_profiles",
    )
    op.drop_index(
        "ix_growth_relationship_profiles_last_touch_date",
        table_name="growth_relationship_profiles",
    )
    op.drop_index(
        "ix_growth_relationship_profiles_current_opportunity_id",
        table_name="growth_relationship_profiles",
    )
    op.drop_index(
        "ix_growth_relationship_profiles_contractor_id",
        table_name="growth_relationship_profiles",
    )
    op.drop_index(
        "ix_growth_relationship_profiles_company_name",
        table_name="growth_relationship_profiles",
    )
    op.drop_table("growth_relationship_profiles")
