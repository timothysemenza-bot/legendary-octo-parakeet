"""proposal package engine backbone

Revision ID: 0035_proposal_package_engine
Revises: 0034_proposal_builder_demo_ready
Create Date: 2026-03-19
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0035_proposal_package_engine"
down_revision: str | Sequence[str] | None = "0034_proposal_builder_demo_ready"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_names() -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return set(inspector.get_table_names())


def upgrade() -> None:
    existing_tables = _table_names()

    if "proposal_package_runs" not in existing_tables:
        op.create_table(
            "proposal_package_runs",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("opportunity_id", sa.String(length=36), nullable=False),
            sa.Column("source_solicitation_id", sa.String(length=36), nullable=False),
            sa.Column("proposal_builder_run_id", sa.String(length=36), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=40), nullable=False),
            sa.Column("current_stage", sa.String(length=60), nullable=True),
            sa.Column("generation_mode", sa.String(length=30), nullable=False),
            sa.Column("generation_reason", sa.String(length=80), nullable=True),
            sa.Column("requested_by", sa.String(length=120), nullable=False),
            sa.Column("requested_at", sa.DateTime(), nullable=False),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("approved_pricing_by", sa.String(length=120), nullable=True),
            sa.Column("approved_pricing_at", sa.DateTime(), nullable=True),
            sa.Column("approved_export_by", sa.String(length=120), nullable=True),
            sa.Column("approved_export_at", sa.DateTime(), nullable=True),
            sa.Column("customer_strategy_json", sa.Text(), nullable=True),
            sa.Column("content_plan_json", sa.Text(), nullable=True),
            sa.Column("pricing_package_json", sa.Text(), nullable=True),
            sa.Column("form_package_json", sa.Text(), nullable=True),
            sa.Column("review_findings_json", sa.Text(), nullable=True),
            sa.Column("package_export_manifest_json", sa.Text(), nullable=True),
            sa.Column("package_artifacts_json", sa.Text(), nullable=True),
            sa.Column("blocking_issues_json", sa.Text(), nullable=True),
            sa.Column("warnings_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
            sa.ForeignKeyConstraint(["proposal_builder_run_id"], ["proposal_builder_runs.id"]),
            sa.ForeignKeyConstraint(["source_solicitation_id"], ["solicitations.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_proposal_package_runs_opportunity_id",
            "proposal_package_runs",
            ["opportunity_id"],
            unique=False,
        )
        op.create_index(
            "ix_proposal_package_runs_source_solicitation_id",
            "proposal_package_runs",
            ["source_solicitation_id"],
            unique=False,
        )
        op.create_index("ix_proposal_package_runs_status", "proposal_package_runs", ["status"], unique=False)
        op.create_index(
            "ix_proposal_package_runs_current_stage",
            "proposal_package_runs",
            ["current_stage"],
            unique=False,
        )

    if "proposal_package_stage_runs" not in existing_tables:
        op.create_table(
            "proposal_package_stage_runs",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("proposal_package_run_id", sa.String(length=36), nullable=False),
            sa.Column("stage_name", sa.String(length=60), nullable=False),
            sa.Column("stage_sequence", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("attempt_count", sa.Integer(), nullable=False),
            sa.Column("model_name", sa.String(length=80), nullable=True),
            sa.Column("reasoning_profile", sa.String(length=40), nullable=True),
            sa.Column("runtime_seconds", sa.Integer(), nullable=True),
            sa.Column("openai_response_id", sa.String(length=120), nullable=True),
            sa.Column("token_usage_json", sa.Text(), nullable=True),
            sa.Column("input_sources_json", sa.Text(), nullable=True),
            sa.Column("artifact_json", sa.Text(), nullable=True),
            sa.Column("blocking_issues_json", sa.Text(), nullable=True),
            sa.Column("warnings_json", sa.Text(), nullable=True),
            sa.Column("failure_reason", sa.Text(), nullable=True),
            sa.Column("approval_required", sa.String(length=40), nullable=True),
            sa.Column("approval_status", sa.String(length=30), nullable=True),
            sa.Column("approved_by", sa.String(length=120), nullable=True),
            sa.Column("approved_at", sa.DateTime(), nullable=True),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["proposal_package_run_id"], ["proposal_package_runs.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_proposal_package_stage_runs_proposal_package_run_id",
            "proposal_package_stage_runs",
            ["proposal_package_run_id"],
            unique=False,
        )
        op.create_index(
            "ix_proposal_package_stage_runs_stage_name",
            "proposal_package_stage_runs",
            ["stage_name"],
            unique=False,
        )
        op.create_index(
            "ix_proposal_package_stage_runs_status",
            "proposal_package_stage_runs",
            ["status"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_index("ix_proposal_package_stage_runs_status", table_name="proposal_package_stage_runs")
    op.drop_index("ix_proposal_package_stage_runs_stage_name", table_name="proposal_package_stage_runs")
    op.drop_index(
        "ix_proposal_package_stage_runs_proposal_package_run_id",
        table_name="proposal_package_stage_runs",
    )
    op.drop_table("proposal_package_stage_runs")

    op.drop_index("ix_proposal_package_runs_current_stage", table_name="proposal_package_runs")
    op.drop_index("ix_proposal_package_runs_status", table_name="proposal_package_runs")
    op.drop_index("ix_proposal_package_runs_source_solicitation_id", table_name="proposal_package_runs")
    op.drop_index("ix_proposal_package_runs_opportunity_id", table_name="proposal_package_runs")
    op.drop_table("proposal_package_runs")
