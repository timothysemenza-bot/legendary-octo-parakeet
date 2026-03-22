"""client onboarding packs and playbooks

Revision ID: 0037_client_onboarding_packs
Revises: 0036_client_profiles_pricing_templates
Create Date: 2026-03-19
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0037_client_onboarding_packs"
down_revision: str | Sequence[str] | None = "0036_client_profiles_pricing_templates"
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

    if "client_onboarding_packs" not in existing_tables:
        op.create_table(
            "client_onboarding_packs",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("client_profile_id", sa.String(length=36), nullable=False),
            sa.Column("pack_name", sa.String(length=255), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("source_mode", sa.String(length=20), nullable=False),
            sa.Column("source_filename", sa.String(length=255), nullable=True),
            sa.Column("storage_dir", sa.Text(), nullable=False),
            sa.Column("manifest_json", sa.Text(), nullable=True),
            sa.Column("classification_report_json", sa.Text(), nullable=True),
            sa.Column("validation_report_json", sa.Text(), nullable=True),
            sa.Column("setup_gaps_json", sa.Text(), nullable=True),
            sa.Column("approved_at", sa.DateTime(), nullable=True),
            sa.Column("activated_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["client_profile_id"], ["client_profiles.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_client_onboarding_packs_client_profile_id", "client_onboarding_packs", ["client_profile_id"], unique=False)
        op.create_index("ix_client_onboarding_packs_status", "client_onboarding_packs", ["status"], unique=False)

    if "client_playbooks" not in existing_tables:
        op.create_table(
            "client_playbooks",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("onboarding_pack_id", sa.String(length=36), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("narrative_guidance_md", sa.Text(), nullable=False),
            sa.Column("structured_rules_json", sa.Text(), nullable=False),
            sa.Column("approved_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["onboarding_pack_id"], ["client_onboarding_packs.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_client_playbooks_onboarding_pack_id", "client_playbooks", ["onboarding_pack_id"], unique=False)
        op.create_index("ix_client_playbooks_status", "client_playbooks", ["status"], unique=False)

    if "client_behavior_profiles" not in existing_tables:
        op.create_table(
            "client_behavior_profiles",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("onboarding_pack_id", sa.String(length=36), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("behavior_profile_json", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["onboarding_pack_id"], ["client_onboarding_packs.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("onboarding_pack_id", name="uq_client_behavior_profiles_onboarding_pack_id"),
        )
        op.create_index("ix_client_behavior_profiles_onboarding_pack_id", "client_behavior_profiles", ["onboarding_pack_id"], unique=False)
        op.create_index("ix_client_behavior_profiles_status", "client_behavior_profiles", ["status"], unique=False)

    if "client_onboarding_assets" not in existing_tables:
        op.create_table(
            "client_onboarding_assets",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("onboarding_pack_id", sa.String(length=36), nullable=False),
            sa.Column("asset_role", sa.String(length=40), nullable=False),
            sa.Column("asset_status", sa.String(length=20), nullable=False),
            sa.Column("classification_source", sa.String(length=20), nullable=False),
            sa.Column("source_filename", sa.String(length=255), nullable=False),
            sa.Column("source_path", sa.Text(), nullable=False),
            sa.Column("media_type", sa.String(length=120), nullable=False),
            sa.Column("extracted_text", sa.Text(), nullable=True),
            sa.Column("normalized_metadata_json", sa.Text(), nullable=True),
            sa.Column("validation_report_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["onboarding_pack_id"], ["client_onboarding_packs.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_client_onboarding_assets_onboarding_pack_id", "client_onboarding_assets", ["onboarding_pack_id"], unique=False)
        op.create_index("ix_client_onboarding_assets_asset_role", "client_onboarding_assets", ["asset_role"], unique=False)
        op.create_index("ix_client_onboarding_assets_asset_status", "client_onboarding_assets", ["asset_status"], unique=False)

    if "client_profiles" in _table_names():
        _add_column_if_missing("client_profiles", sa.Column("active_onboarding_pack_id", sa.String(length=36), nullable=True))
        _add_column_if_missing("client_profiles", sa.Column("active_playbook_id", sa.String(length=36), nullable=True))
        _add_column_if_missing("client_profiles", sa.Column("client_environment_status", sa.String(length=30), nullable=False, server_default="SETUP_REQUIRED"))
        _create_index_if_missing("ix_client_profiles_active_onboarding_pack_id", "client_profiles", ["active_onboarding_pack_id"])
        _create_index_if_missing("ix_client_profiles_active_playbook_id", "client_profiles", ["active_playbook_id"])

    if "proposal_builder_runs" in _table_names():
        _add_column_if_missing("proposal_builder_runs", sa.Column("onboarding_pack_id", sa.String(length=36), nullable=True))
        _add_column_if_missing("proposal_builder_runs", sa.Column("playbook_id", sa.String(length=36), nullable=True))
        _add_column_if_missing("proposal_builder_runs", sa.Column("playbook_version", sa.Integer(), nullable=True))
        _create_index_if_missing("ix_proposal_builder_runs_onboarding_pack_id", "proposal_builder_runs", ["onboarding_pack_id"])
        _create_index_if_missing("ix_proposal_builder_runs_playbook_id", "proposal_builder_runs", ["playbook_id"])

    if "proposal_package_runs" in _table_names():
        _add_column_if_missing("proposal_package_runs", sa.Column("onboarding_pack_id", sa.String(length=36), nullable=True))
        _add_column_if_missing("proposal_package_runs", sa.Column("playbook_id", sa.String(length=36), nullable=True))
        _add_column_if_missing("proposal_package_runs", sa.Column("playbook_version", sa.Integer(), nullable=True))
        _create_index_if_missing("ix_proposal_package_runs_onboarding_pack_id", "proposal_package_runs", ["onboarding_pack_id"])
        _create_index_if_missing("ix_proposal_package_runs_playbook_id", "proposal_package_runs", ["playbook_id"])


def downgrade() -> None:
    if "proposal_package_runs" in _table_names():
        for index_name in (
            "ix_proposal_package_runs_playbook_id",
            "ix_proposal_package_runs_onboarding_pack_id",
        ):
            if index_name in _index_names("proposal_package_runs"):
                op.drop_index(index_name, table_name="proposal_package_runs")
        for column_name in ("playbook_version", "playbook_id", "onboarding_pack_id"):
            if column_name in _column_names("proposal_package_runs"):
                op.drop_column("proposal_package_runs", column_name)

    if "proposal_builder_runs" in _table_names():
        for index_name in (
            "ix_proposal_builder_runs_playbook_id",
            "ix_proposal_builder_runs_onboarding_pack_id",
        ):
            if index_name in _index_names("proposal_builder_runs"):
                op.drop_index(index_name, table_name="proposal_builder_runs")
        for column_name in ("playbook_version", "playbook_id", "onboarding_pack_id"):
            if column_name in _column_names("proposal_builder_runs"):
                op.drop_column("proposal_builder_runs", column_name)

    if "client_profiles" in _table_names():
        for index_name in (
            "ix_client_profiles_active_playbook_id",
            "ix_client_profiles_active_onboarding_pack_id",
        ):
            if index_name in _index_names("client_profiles"):
                op.drop_index(index_name, table_name="client_profiles")
        for column_name in ("client_environment_status", "active_playbook_id", "active_onboarding_pack_id"):
            if column_name in _column_names("client_profiles"):
                op.drop_column("client_profiles", column_name)

    if "client_onboarding_assets" in _table_names():
        for index_name in (
            "ix_client_onboarding_assets_asset_status",
            "ix_client_onboarding_assets_asset_role",
            "ix_client_onboarding_assets_onboarding_pack_id",
        ):
            if index_name in _index_names("client_onboarding_assets"):
                op.drop_index(index_name, table_name="client_onboarding_assets")
        op.drop_table("client_onboarding_assets")

    if "client_behavior_profiles" in _table_names():
        for index_name in (
            "ix_client_behavior_profiles_status",
            "ix_client_behavior_profiles_onboarding_pack_id",
        ):
            if index_name in _index_names("client_behavior_profiles"):
                op.drop_index(index_name, table_name="client_behavior_profiles")
        op.drop_table("client_behavior_profiles")

    if "client_playbooks" in _table_names():
        for index_name in ("ix_client_playbooks_status", "ix_client_playbooks_onboarding_pack_id"):
            if index_name in _index_names("client_playbooks"):
                op.drop_index(index_name, table_name="client_playbooks")
        op.drop_table("client_playbooks")

    if "client_onboarding_packs" in _table_names():
        for index_name in (
            "ix_client_onboarding_packs_status",
            "ix_client_onboarding_packs_client_profile_id",
        ):
            if index_name in _index_names("client_onboarding_packs"):
                op.drop_index(index_name, table_name="client_onboarding_packs")
        op.drop_table("client_onboarding_packs")
