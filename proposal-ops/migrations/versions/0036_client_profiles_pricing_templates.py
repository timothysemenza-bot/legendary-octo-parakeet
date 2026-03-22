"""client profiles, pricing models, and proposal templates

Revision ID: 0036_client_profiles_pricing_templates
Revises: 0035_proposal_package_engine
Create Date: 2026-03-19
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0036_client_profiles_pricing_templates"
down_revision: str | Sequence[str] | None = "0035_proposal_package_engine"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _inspector() -> sa.Inspector:
    return sa.inspect(op.get_bind())


def _table_names() -> set[str]:
    return set(_inspector().get_table_names())


def _column_names(table_name: str) -> set[str]:
    return {column["name"] for column in _inspector().get_columns(table_name)}


def _index_names(table_name: str) -> set[str]:
    return {index["name"] for index in _inspector().get_indexes(table_name)}


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if column.name not in _column_names(table_name):
        op.add_column(table_name, column)


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str]) -> None:
    if index_name not in _index_names(table_name):
        op.create_index(index_name, table_name, columns, unique=False)


def upgrade() -> None:
    existing_tables = _table_names()

    if "client_profiles" not in existing_tables:
        op.create_table(
            "client_profiles",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("display_name", sa.String(length=255), nullable=False),
            sa.Column("aliases_json", sa.Text(), nullable=True),
            sa.Column("approved_content_tags_json", sa.Text(), nullable=True),
            sa.Column("region_tags_json", sa.Text(), nullable=True),
            sa.Column("service_tags_json", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("default_pricing_model_id", sa.String(length=36), nullable=True),
            sa.Column("default_proposal_template_id", sa.String(length=36), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["default_pricing_model_id"], ["client_pricing_models.id"]),
            sa.ForeignKeyConstraint(["default_proposal_template_id"], ["client_proposal_templates.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_client_profiles_display_name", "client_profiles", ["display_name"], unique=True)
        op.create_index("ix_client_profiles_status", "client_profiles", ["status"], unique=False)

    if "client_pricing_models" not in existing_tables:
        op.create_table(
            "client_pricing_models",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("client_profile_id", sa.String(length=36), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("onboarding_mode", sa.String(length=20), nullable=False),
            sa.Column("source_format", sa.String(length=20), nullable=True),
            sa.Column("source_filename", sa.String(length=255), nullable=True),
            sa.Column("source_file_path", sa.Text(), nullable=True),
            sa.Column("workbook_template_filename", sa.String(length=255), nullable=True),
            sa.Column("workbook_template_path", sa.Text(), nullable=True),
            sa.Column("canonical_model_json", sa.Text(), nullable=True),
            sa.Column("validation_report_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["client_profile_id"], ["client_profiles.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_client_pricing_models_client_profile_id", "client_pricing_models", ["client_profile_id"], unique=False)
        op.create_index("ix_client_pricing_models_status", "client_pricing_models", ["status"], unique=False)

    if "client_proposal_templates" not in existing_tables:
        op.create_table(
            "client_proposal_templates",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("client_profile_id", sa.String(length=36), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("source_filename", sa.String(length=255), nullable=False),
            sa.Column("storage_path", sa.Text(), nullable=False),
            sa.Column("anchor_map_json", sa.Text(), nullable=True),
            sa.Column("validation_report_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["client_profile_id"], ["client_profiles.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_client_proposal_templates_client_profile_id",
            "client_proposal_templates",
            ["client_profile_id"],
            unique=False,
        )
        op.create_index("ix_client_proposal_templates_status", "client_proposal_templates", ["status"], unique=False)

    if "opportunity_proposal_configs" not in existing_tables:
        op.create_table(
            "opportunity_proposal_configs",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("opportunity_id", sa.String(length=36), nullable=False),
            sa.Column("client_profile_id", sa.String(length=36), nullable=True),
            sa.Column("pricing_model_id", sa.String(length=36), nullable=True),
            sa.Column("proposal_template_id", sa.String(length=36), nullable=True),
            sa.Column("client_profile_selection_source", sa.String(length=20), nullable=False),
            sa.Column("pricing_model_selection_source", sa.String(length=20), nullable=False),
            sa.Column("proposal_template_selection_source", sa.String(length=20), nullable=False),
            sa.Column("validation_warnings_json", sa.Text(), nullable=True),
            sa.Column("validation_errors_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
            sa.ForeignKeyConstraint(["client_profile_id"], ["client_profiles.id"]),
            sa.ForeignKeyConstraint(["pricing_model_id"], ["client_pricing_models.id"]),
            sa.ForeignKeyConstraint(["proposal_template_id"], ["client_proposal_templates.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("opportunity_id", name="uq_opportunity_proposal_configs_opportunity_id"),
        )
        op.create_index(
            "ix_opportunity_proposal_configs_opportunity_id",
            "opportunity_proposal_configs",
            ["opportunity_id"],
            unique=False,
        )
        op.create_index(
            "ix_opportunity_proposal_configs_client_profile_id",
            "opportunity_proposal_configs",
            ["client_profile_id"],
            unique=False,
        )
        op.create_index(
            "ix_opportunity_proposal_configs_pricing_model_id",
            "opportunity_proposal_configs",
            ["pricing_model_id"],
            unique=False,
        )
        op.create_index(
            "ix_opportunity_proposal_configs_proposal_template_id",
            "opportunity_proposal_configs",
            ["proposal_template_id"],
            unique=False,
        )

    if "proposal_builder_runs" in _table_names():
        _add_column_if_missing("proposal_builder_runs", sa.Column("client_profile_id", sa.String(length=36), nullable=True))
        _add_column_if_missing("proposal_builder_runs", sa.Column("pricing_model_id", sa.String(length=36), nullable=True))
        _add_column_if_missing("proposal_builder_runs", sa.Column("proposal_template_id", sa.String(length=36), nullable=True))
        _add_column_if_missing("proposal_builder_runs", sa.Column("selection_source_json", sa.Text(), nullable=True))
        _create_index_if_missing("ix_proposal_builder_runs_client_profile_id", "proposal_builder_runs", ["client_profile_id"])
        _create_index_if_missing("ix_proposal_builder_runs_pricing_model_id", "proposal_builder_runs", ["pricing_model_id"])
        _create_index_if_missing(
            "ix_proposal_builder_runs_proposal_template_id",
            "proposal_builder_runs",
            ["proposal_template_id"],
        )

    if "proposal_package_runs" in _table_names():
        _add_column_if_missing("proposal_package_runs", sa.Column("client_profile_id", sa.String(length=36), nullable=True))
        _add_column_if_missing("proposal_package_runs", sa.Column("pricing_model_id", sa.String(length=36), nullable=True))
        _add_column_if_missing("proposal_package_runs", sa.Column("proposal_template_id", sa.String(length=36), nullable=True))
        _add_column_if_missing("proposal_package_runs", sa.Column("selection_source_json", sa.Text(), nullable=True))
        _create_index_if_missing("ix_proposal_package_runs_client_profile_id", "proposal_package_runs", ["client_profile_id"])
        _create_index_if_missing("ix_proposal_package_runs_pricing_model_id", "proposal_package_runs", ["pricing_model_id"])
        _create_index_if_missing(
            "ix_proposal_package_runs_proposal_template_id",
            "proposal_package_runs",
            ["proposal_template_id"],
        )


def downgrade() -> None:
    if "proposal_package_runs" in _table_names():
        for index_name in (
            "ix_proposal_package_runs_proposal_template_id",
            "ix_proposal_package_runs_pricing_model_id",
            "ix_proposal_package_runs_client_profile_id",
        ):
            if index_name in _index_names("proposal_package_runs"):
                op.drop_index(index_name, table_name="proposal_package_runs")
        for column_name in ("selection_source_json", "proposal_template_id", "pricing_model_id", "client_profile_id"):
            if column_name in _column_names("proposal_package_runs"):
                op.drop_column("proposal_package_runs", column_name)

    if "proposal_builder_runs" in _table_names():
        for index_name in (
            "ix_proposal_builder_runs_proposal_template_id",
            "ix_proposal_builder_runs_pricing_model_id",
            "ix_proposal_builder_runs_client_profile_id",
        ):
            if index_name in _index_names("proposal_builder_runs"):
                op.drop_index(index_name, table_name="proposal_builder_runs")
        for column_name in ("selection_source_json", "proposal_template_id", "pricing_model_id", "client_profile_id"):
            if column_name in _column_names("proposal_builder_runs"):
                op.drop_column("proposal_builder_runs", column_name)

    if "opportunity_proposal_configs" in _table_names():
        for index_name in (
            "ix_opportunity_proposal_configs_proposal_template_id",
            "ix_opportunity_proposal_configs_pricing_model_id",
            "ix_opportunity_proposal_configs_client_profile_id",
            "ix_opportunity_proposal_configs_opportunity_id",
        ):
            if index_name in _index_names("opportunity_proposal_configs"):
                op.drop_index(index_name, table_name="opportunity_proposal_configs")
        op.drop_table("opportunity_proposal_configs")

    if "client_proposal_templates" in _table_names():
        for index_name in (
            "ix_client_proposal_templates_status",
            "ix_client_proposal_templates_client_profile_id",
        ):
            if index_name in _index_names("client_proposal_templates"):
                op.drop_index(index_name, table_name="client_proposal_templates")
        op.drop_table("client_proposal_templates")

    if "client_pricing_models" in _table_names():
        for index_name in (
            "ix_client_pricing_models_status",
            "ix_client_pricing_models_client_profile_id",
        ):
            if index_name in _index_names("client_pricing_models"):
                op.drop_index(index_name, table_name="client_pricing_models")
        op.drop_table("client_pricing_models")

    if "client_profiles" in _table_names():
        for index_name in ("ix_client_profiles_status", "ix_client_profiles_display_name"):
            if index_name in _index_names("client_profiles"):
                op.drop_index(index_name, table_name="client_profiles")
        op.drop_table("client_profiles")
