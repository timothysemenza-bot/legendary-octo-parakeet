"""janitorial capture os foundation

Revision ID: 0025_janitorial_capture_os_foundation
Revises: 0024_rfp_source_document_families
Create Date: 2026-03-07
"""

from collections.abc import Sequence
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision: str = "0025_janitorial_capture_os_foundation"
down_revision: str | Sequence[str] | None = "0024_rfp_source_document_families"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("organization_type", sa.String(length=50), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("state", sa.String(length=40), nullable=True),
        sa.Column("website_url", sa.String(length=255), nullable=True),
        sa.Column("procurement_url", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_organizations_name", "organizations", ["name"], unique=False)
    op.create_index("ix_organizations_organization_type", "organizations", ["organization_type"], unique=False)
    op.create_index("ix_organizations_state", "organizations", ["state"], unique=False)

    op.create_table(
        "facilities",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("parent_facility_id", sa.String(length=36), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("facility_kind", sa.String(length=20), nullable=False),
        sa.Column("facility_type", sa.String(length=60), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("state", sa.String(length=40), nullable=True),
        sa.Column("service_complexity", sa.String(length=20), nullable=False),
        sa.Column("square_footage", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["parent_facility_id"], ["facilities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_facilities_organization_id", "facilities", ["organization_id"], unique=False)
    op.create_index("ix_facilities_parent_facility_id", "facilities", ["parent_facility_id"], unique=False)
    op.create_index("ix_facilities_name", "facilities", ["name"], unique=False)
    op.create_index("ix_facilities_facility_kind", "facilities", ["facility_kind"], unique=False)
    op.create_index("ix_facilities_facility_type", "facilities", ["facility_type"], unique=False)
    op.create_index("ix_facilities_state", "facilities", ["state"], unique=False)

    op.create_table(
        "contract_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("incumbent_vendor", sa.String(length=255), nullable=True),
        sa.Column("estimated_annual_value", sa.Float(), nullable=True),
        sa.Column("estimated_total_value", sa.Float(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("expiration_date", sa.Date(), nullable=True),
        sa.Column("rebid_window_start", sa.Date(), nullable=True),
        sa.Column("rebid_window_end", sa.Date(), nullable=True),
        sa.Column("procurement_source_url", sa.String(length=255), nullable=True),
        sa.Column("source_type", sa.String(length=30), nullable=False),
        sa.Column("source_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_contract_records_organization_id", "contract_records", ["organization_id"], unique=False)
    op.create_index("ix_contract_records_title", "contract_records", ["title"], unique=False)
    op.create_index("ix_contract_records_incumbent_vendor", "contract_records", ["incumbent_vendor"], unique=False)
    op.create_index("ix_contract_records_expiration_date", "contract_records", ["expiration_date"], unique=False)
    op.create_index("ix_contract_records_rebid_window_start", "contract_records", ["rebid_window_start"], unique=False)
    op.create_index("ix_contract_records_rebid_window_end", "contract_records", ["rebid_window_end"], unique=False)
    op.create_index("ix_contract_records_source_type", "contract_records", ["source_type"], unique=False)

    op.create_table(
        "contract_facilities",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("contract_id", sa.String(length=36), nullable=False),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["contract_id"], ["contract_records.id"]),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("contract_id", "facility_id", name="uq_contract_facility_pair"),
    )
    op.create_index("ix_contract_facilities_contract_id", "contract_facilities", ["contract_id"], unique=False)
    op.create_index("ix_contract_facilities_facility_id", "contract_facilities", ["facility_id"], unique=False)

    op.create_table(
        "scoring_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("profile_type", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scoring_profiles_profile_type", "scoring_profiles", ["profile_type"], unique=False)

    op.create_table(
        "scoring_criteria",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("profile_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["scoring_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "code", name="uq_scoring_profile_code"),
    )
    op.create_index("ix_scoring_criteria_profile_id", "scoring_criteria", ["profile_id"], unique=False)

    op.create_table(
        "contractors",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("service_geographies", sa.Text(), nullable=True),
        sa.Column("headquarters_city", sa.String(length=120), nullable=True),
        sa.Column("headquarters_state", sa.String(length=40), nullable=True),
        sa.Column("vertical_experience", sa.Text(), nullable=True),
        sa.Column("labor_profile", sa.String(length=80), nullable=True),
        sa.Column("union_profile", sa.String(length=80), nullable=True),
        sa.Column("diversity_certs", sa.Text(), nullable=True),
        sa.Column("airport_experience", sa.Boolean(), nullable=False),
        sa.Column("healthcare_experience", sa.Boolean(), nullable=False),
        sa.Column("education_experience", sa.Boolean(), nullable=False),
        sa.Column("municipal_experience", sa.Boolean(), nullable=False),
        sa.Column("scale_band", sa.String(length=30), nullable=False),
        sa.Column("relationship_strength", sa.Integer(), nullable=False),
        sa.Column("relationship_notes", sa.Text(), nullable=True),
        sa.Column("strategic_fit_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_contractors_name", "contractors", ["name"], unique=False)
    op.create_index("ix_contractors_headquarters_state", "contractors", ["headquarters_state"], unique=False)

    op.create_table(
        "opportunity_matches",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("opportunity_id", sa.String(length=36), nullable=False),
        sa.Column("contractor_id", sa.String(length=36), nullable=False),
        sa.Column("match_score", sa.Float(), nullable=False),
        sa.Column("explanation_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.ForeignKeyConstraint(["contractor_id"], ["contractors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("opportunity_id", "contractor_id", name="uq_opportunity_match_pair"),
    )
    op.create_index("ix_opportunity_matches_opportunity_id", "opportunity_matches", ["opportunity_id"], unique=False)
    op.create_index("ix_opportunity_matches_contractor_id", "opportunity_matches", ["contractor_id"], unique=False)

    op.create_table(
        "contacts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=True),
        sa.Column("contractor_id", sa.String(length=36), nullable=True),
        sa.Column("opportunity_id", sa.String(length=36), nullable=True),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("role_title", sa.String(length=120), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=80), nullable=True),
        sa.Column("contact_side", sa.String(length=30), nullable=False),
        sa.Column("source_type", sa.String(length=30), nullable=False),
        sa.Column("confidence_level", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["contractor_id"], ["contractors.id"]),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_contacts_organization_id", "contacts", ["organization_id"], unique=False)
    op.create_index("ix_contacts_contractor_id", "contacts", ["contractor_id"], unique=False)
    op.create_index("ix_contacts_opportunity_id", "contacts", ["opportunity_id"], unique=False)

    op.create_table(
        "intelligence_notes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("opportunity_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("note_type", sa.String(length=40), nullable=False),
        sa.Column("note_text", sa.Text(), nullable=False),
        sa.Column("source_class", sa.String(length=30), nullable=False),
        sa.Column("provenance", sa.Text(), nullable=False),
        sa.Column("confidence_level", sa.String(length=20), nullable=False),
        sa.Column("ethics_guidance_text", sa.Text(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_intelligence_notes_opportunity_id", "intelligence_notes", ["opportunity_id"], unique=False)

    op.create_table(
        "evidence_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("opportunity_id", sa.String(length=36), nullable=False),
        sa.Column("intelligence_note_id", sa.String(length=36), nullable=True),
        sa.Column("contract_id", sa.String(length=36), nullable=True),
        sa.Column("source_class", sa.String(length=30), nullable=False),
        sa.Column("provenance", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(length=255), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("confidence_level", sa.String(length=20), nullable=False),
        sa.Column("ethics_guidance_text", sa.Text(), nullable=False),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.ForeignKeyConstraint(["intelligence_note_id"], ["intelligence_notes.id"]),
        sa.ForeignKeyConstraint(["contract_id"], ["contract_records.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evidence_records_opportunity_id", "evidence_records", ["opportunity_id"], unique=False)
    op.create_index("ix_evidence_records_intelligence_note_id", "evidence_records", ["intelligence_note_id"], unique=False)
    op.create_index("ix_evidence_records_contract_id", "evidence_records", ["contract_id"], unique=False)

    op.create_table(
        "capture_actions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("opportunity_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("action_type", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("owner", sa.String(length=120), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_capture_actions_opportunity_id", "capture_actions", ["opportunity_id"], unique=False)
    op.create_index("ix_capture_actions_status", "capture_actions", ["status"], unique=False)

    op.create_table(
        "commercial_engagements",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("opportunity_id", sa.String(length=36), nullable=False),
        sa.Column("contractor_id", sa.String(length=36), nullable=True),
        sa.Column("retainer_amount", sa.Float(), nullable=True),
        sa.Column("success_fee_type", sa.String(length=40), nullable=True),
        sa.Column("success_fee_value", sa.Float(), nullable=True),
        sa.Column("projected_payout_date", sa.Date(), nullable=True),
        sa.Column("projected_payout_amount", sa.Float(), nullable=True),
        sa.Column("weighted_expected_value", sa.Float(), nullable=True),
        sa.Column("realized_revenue", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.ForeignKeyConstraint(["contractor_id"], ["contractors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("opportunity_id", name="uq_commercials_opportunity"),
    )
    op.create_index("ix_commercial_engagements_opportunity_id", "commercial_engagements", ["opportunity_id"], unique=False)
    op.create_index("ix_commercial_engagements_contractor_id", "commercial_engagements", ["contractor_id"], unique=False)

    op.create_table(
        "proposal_workflow_summaries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("opportunity_id", sa.String(length=36), nullable=False),
        sa.Column("pricing_status", sa.String(length=30), nullable=False),
        sa.Column("compliance_status", sa.String(length=30), nullable=False),
        sa.Column("sme_assignments_json", sa.Text(), nullable=False),
        sa.Column("review_gate_status", sa.String(length=30), nullable=False),
        sa.Column("submission_milestone", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("opportunity_id", name="uq_proposal_summary_opportunity"),
    )
    op.create_index("ix_proposal_workflow_summaries_opportunity_id", "proposal_workflow_summaries", ["opportunity_id"], unique=False)

    op.add_column("opportunities", sa.Column("pursuit_stage", sa.String(length=30), nullable=False, server_default="INTELLIGENCE"))
    op.add_column("opportunities", sa.Column("proposal_stage", sa.String(length=30), nullable=False, server_default="INTAKE"))
    op.add_column("opportunities", sa.Column("buying_organization_id", sa.String(length=36), nullable=True))
    op.add_column("opportunities", sa.Column("primary_contract_id", sa.String(length=36), nullable=True))
    op.add_column("opportunities", sa.Column("primary_facility_id", sa.String(length=36), nullable=True))
    op.add_column("opportunities", sa.Column("confidence_level", sa.String(length=20), nullable=False, server_default="MEDIUM"))
    op.add_column("opportunities", sa.Column("expected_rfp_date", sa.Date(), nullable=True))
    op.add_column("opportunities", sa.Column("provenance_summary", sa.Text(), nullable=True))
    op.add_column("opportunities", sa.Column("provenance_last_verified_at", sa.DateTime(), nullable=True))
    op.add_column("opportunities", sa.Column("score_breakdown_json", sa.Text(), nullable=True))
    op.add_column("opportunities", sa.Column("bidder_fit_score", sa.Float(), nullable=True))
    op.add_column("opportunities", sa.Column("weighted_pipeline_value", sa.Float(), nullable=True))
    op.create_index("ix_opportunities_pursuit_stage", "opportunities", ["pursuit_stage"], unique=False)
    op.create_index("ix_opportunities_proposal_stage", "opportunities", ["proposal_stage"], unique=False)
    op.create_index("ix_opportunities_buying_organization_id", "opportunities", ["buying_organization_id"], unique=False)
    op.create_index("ix_opportunities_primary_contract_id", "opportunities", ["primary_contract_id"], unique=False)
    op.create_index("ix_opportunities_primary_facility_id", "opportunities", ["primary_facility_id"], unique=False)

    bind = op.get_bind()
    existing_clients = bind.execute(
        sa.text(
            """
            SELECT DISTINCT client
            FROM opportunities
            WHERE client IS NOT NULL AND TRIM(client) <> ''
            """
        )
    ).fetchall()
    org_lookup: dict[str, str] = {}
    for (client_name,) in existing_clients:
        organization_id = str(uuid4())
        org_lookup[str(client_name)] = organization_id
        bind.execute(
            sa.text(
                """
                INSERT INTO organizations (
                    id, name, organization_type, city, state, website_url, procurement_url, notes, created_at, updated_at
                )
                VALUES (:id, :name, 'OTHER', NULL, NULL, NULL, NULL, 'Backfilled from legacy opportunity client field.', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
            ),
            {"id": organization_id, "name": str(client_name)},
        )
    for client_name, organization_id in org_lookup.items():
        bind.execute(
            sa.text(
                """
                UPDATE opportunities
                SET buying_organization_id = :organization_id
                WHERE client = :client_name
                """
            ),
            {"organization_id": organization_id, "client_name": client_name},
        )

    bind.execute(
        sa.text(
            """
            UPDATE opportunities
            SET proposal_stage = stage,
                pursuit_stage = CASE
                    WHEN stage = 'INTAKE' THEN 'INTELLIGENCE'
                    WHEN stage = 'QUALIFICATION' THEN 'EARLY_QUALIFICATION'
                    WHEN stage = 'STRATEGY' THEN 'PRE_RFP_CAPTURE'
                    WHEN stage IN ('COMPLIANCE', 'CONTENT_PLANNING', 'DRAFTING', 'REVIEW', 'SUBMISSION') THEN 'ACTIVE_RFP'
                    WHEN stage = 'ARCHIVE' THEN 'SUBMITTED'
                    ELSE 'INTELLIGENCE'
                END,
                provenance_summary = COALESCE(provenance_summary, 'Backfilled from legacy opportunity intake workflow.'),
                weighted_pipeline_value = ROUND(estimated_contract_value * (qualification_score / 100.0), 2)
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_opportunities_primary_facility_id", table_name="opportunities")
    op.drop_index("ix_opportunities_primary_contract_id", table_name="opportunities")
    op.drop_index("ix_opportunities_buying_organization_id", table_name="opportunities")
    op.drop_index("ix_opportunities_proposal_stage", table_name="opportunities")
    op.drop_index("ix_opportunities_pursuit_stage", table_name="opportunities")
    op.drop_column("opportunities", "weighted_pipeline_value")
    op.drop_column("opportunities", "bidder_fit_score")
    op.drop_column("opportunities", "score_breakdown_json")
    op.drop_column("opportunities", "provenance_last_verified_at")
    op.drop_column("opportunities", "provenance_summary")
    op.drop_column("opportunities", "expected_rfp_date")
    op.drop_column("opportunities", "confidence_level")
    op.drop_column("opportunities", "primary_facility_id")
    op.drop_column("opportunities", "primary_contract_id")
    op.drop_column("opportunities", "buying_organization_id")
    op.drop_column("opportunities", "proposal_stage")
    op.drop_column("opportunities", "pursuit_stage")

    op.drop_index("ix_proposal_workflow_summaries_opportunity_id", table_name="proposal_workflow_summaries")
    op.drop_table("proposal_workflow_summaries")
    op.drop_index("ix_commercial_engagements_contractor_id", table_name="commercial_engagements")
    op.drop_index("ix_commercial_engagements_opportunity_id", table_name="commercial_engagements")
    op.drop_table("commercial_engagements")
    op.drop_index("ix_capture_actions_status", table_name="capture_actions")
    op.drop_index("ix_capture_actions_opportunity_id", table_name="capture_actions")
    op.drop_table("capture_actions")
    op.drop_index("ix_evidence_records_contract_id", table_name="evidence_records")
    op.drop_index("ix_evidence_records_intelligence_note_id", table_name="evidence_records")
    op.drop_index("ix_evidence_records_opportunity_id", table_name="evidence_records")
    op.drop_table("evidence_records")
    op.drop_index("ix_intelligence_notes_opportunity_id", table_name="intelligence_notes")
    op.drop_table("intelligence_notes")
    op.drop_index("ix_contacts_opportunity_id", table_name="contacts")
    op.drop_index("ix_contacts_contractor_id", table_name="contacts")
    op.drop_index("ix_contacts_organization_id", table_name="contacts")
    op.drop_table("contacts")
    op.drop_index("ix_opportunity_matches_contractor_id", table_name="opportunity_matches")
    op.drop_index("ix_opportunity_matches_opportunity_id", table_name="opportunity_matches")
    op.drop_table("opportunity_matches")
    op.drop_index("ix_contractors_headquarters_state", table_name="contractors")
    op.drop_index("ix_contractors_name", table_name="contractors")
    op.drop_table("contractors")
    op.drop_index("ix_scoring_criteria_profile_id", table_name="scoring_criteria")
    op.drop_table("scoring_criteria")
    op.drop_index("ix_scoring_profiles_profile_type", table_name="scoring_profiles")
    op.drop_table("scoring_profiles")
    op.drop_index("ix_contract_facilities_facility_id", table_name="contract_facilities")
    op.drop_index("ix_contract_facilities_contract_id", table_name="contract_facilities")
    op.drop_table("contract_facilities")
    op.drop_index("ix_contract_records_source_type", table_name="contract_records")
    op.drop_index("ix_contract_records_rebid_window_end", table_name="contract_records")
    op.drop_index("ix_contract_records_rebid_window_start", table_name="contract_records")
    op.drop_index("ix_contract_records_expiration_date", table_name="contract_records")
    op.drop_index("ix_contract_records_incumbent_vendor", table_name="contract_records")
    op.drop_index("ix_contract_records_title", table_name="contract_records")
    op.drop_index("ix_contract_records_organization_id", table_name="contract_records")
    op.drop_table("contract_records")
    op.drop_index("ix_facilities_state", table_name="facilities")
    op.drop_index("ix_facilities_facility_type", table_name="facilities")
    op.drop_index("ix_facilities_facility_kind", table_name="facilities")
    op.drop_index("ix_facilities_name", table_name="facilities")
    op.drop_index("ix_facilities_parent_facility_id", table_name="facilities")
    op.drop_index("ix_facilities_organization_id", table_name="facilities")
    op.drop_table("facilities")
    op.drop_index("ix_organizations_state", table_name="organizations")
    op.drop_index("ix_organizations_organization_type", table_name="organizations")
    op.drop_index("ix_organizations_name", table_name="organizations")
    op.drop_table("organizations")
