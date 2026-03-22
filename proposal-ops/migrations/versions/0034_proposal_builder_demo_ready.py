"""proposal builder demo ready

Revision ID: 0034_proposal_builder_demo_ready
Revises: 0033_company_os_wave1
Create Date: 2026-03-19
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0034_proposal_builder_demo_ready"
down_revision: str | Sequence[str] | None = "0033_company_os_wave1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _column_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    solicitation_columns = _column_names("solicitations")
    if "structured_fields_json" not in solicitation_columns:
        op.add_column("solicitations", sa.Column("structured_fields_json", sa.Text(), nullable=True))
    if "field_provenance_json" not in solicitation_columns:
        op.add_column("solicitations", sa.Column("field_provenance_json", sa.Text(), nullable=True))

    op.create_table(
        "proposal_builder_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("opportunity_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("source_solicitation_id", sa.String(length=36), nullable=False),
        sa.Column("generation_mode", sa.String(length=30), nullable=False),
        sa.Column("model_name", sa.String(length=80), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("opportunity_summary_json", sa.Text(), nullable=True),
        sa.Column("evaluation_criteria_json", sa.Text(), nullable=True),
        sa.Column("submission_instructions_json", sa.Text(), nullable=True),
        sa.Column("win_themes_json", sa.Text(), nullable=True),
        sa.Column("section_drafting_plan_json", sa.Text(), nullable=True),
        sa.Column("draft_package_json", sa.Text(), nullable=True),
        sa.Column("export_manifest_json", sa.Text(), nullable=True),
        sa.Column("warnings_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.ForeignKeyConstraint(["source_solicitation_id"], ["solicitations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_proposal_builder_runs_opportunity_id", "proposal_builder_runs", ["opportunity_id"], unique=False)
    op.create_index(
        "ix_proposal_builder_runs_source_solicitation_id",
        "proposal_builder_runs",
        ["source_solicitation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_proposal_builder_runs_source_solicitation_id", table_name="proposal_builder_runs")
    op.drop_index("ix_proposal_builder_runs_opportunity_id", table_name="proposal_builder_runs")
    op.drop_table("proposal_builder_runs")
