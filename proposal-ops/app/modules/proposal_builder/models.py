import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ClientProfile(Base):
    __tablename__ = "client_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    display_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    aliases_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_content_tags_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    region_tags_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    service_tags_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", index=True)
    default_pricing_model_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("client_pricing_models.id"), nullable=True)
    default_proposal_template_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("client_proposal_templates.id"), nullable=True
    )
    active_onboarding_pack_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("client_onboarding_packs.id"), nullable=True, index=True
    )
    active_playbook_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("client_playbooks.id"), nullable=True, index=True
    )
    client_environment_status: Mapped[str] = mapped_column(String(30), nullable=False, default="SETUP_REQUIRED")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class ClientOnboardingPack(Base):
    __tablename__ = "client_onboarding_packs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("client_profiles.id"), nullable=False, index=True)
    pack_name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT", index=True)
    source_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="ZIP")
    source_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    storage_dir: Mapped[str] = mapped_column(Text, nullable=False)
    manifest_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    classification_report_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_report_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    setup_gaps_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class ClientOnboardingAsset(Base):
    __tablename__ = "client_onboarding_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    onboarding_pack_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("client_onboarding_packs.id"), nullable=False, index=True
    )
    asset_role: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    asset_status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT", index=True)
    classification_source: Mapped[str] = mapped_column(String(20), nullable=False, default="heuristic")
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    source_path: Mapped[str] = mapped_column(Text, nullable=False)
    media_type: Mapped[str] = mapped_column(String(120), nullable=False, default="application/octet-stream")
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_report_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class ClientPlaybook(Base):
    __tablename__ = "client_playbooks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    onboarding_pack_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("client_onboarding_packs.id"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT", index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    narrative_guidance_md: Mapped[str] = mapped_column(Text, nullable=False)
    structured_rules_json: Mapped[str] = mapped_column(Text, nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class ClientBehaviorProfile(Base):
    __tablename__ = "client_behavior_profiles"
    __table_args__ = (UniqueConstraint("onboarding_pack_id", name="uq_client_behavior_profiles_onboarding_pack_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    onboarding_pack_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("client_onboarding_packs.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT", index=True)
    behavior_profile_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class ClientPricingModel(Base):
    __tablename__ = "client_pricing_models"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("client_profiles.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT", index=True)
    onboarding_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="IMPORT")
    source_format: Mapped[str | None] = mapped_column(String(20), nullable=True)
    source_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    workbook_template_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    workbook_template_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    canonical_model_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_report_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class ClientProposalTemplate(Base):
    __tablename__ = "client_proposal_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("client_profiles.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT", index=True)
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    anchor_map_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_report_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class OpportunityProposalConfig(Base):
    __tablename__ = "opportunity_proposal_configs"
    __table_args__ = (UniqueConstraint("opportunity_id", name="uq_opportunity_proposal_configs_opportunity_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id: Mapped[str] = mapped_column(String(36), ForeignKey("opportunities.id"), nullable=False, index=True)
    client_profile_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("client_profiles.id"), nullable=True, index=True)
    pricing_model_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("client_pricing_models.id"), nullable=True, index=True)
    proposal_template_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("client_proposal_templates.id"), nullable=True, index=True
    )
    client_profile_selection_source: Mapped[str] = mapped_column(String(20), nullable=False, default="missing")
    pricing_model_selection_source: Mapped[str] = mapped_column(String(20), nullable=False, default="missing")
    proposal_template_selection_source: Mapped[str] = mapped_column(String(20), nullable=False, default="missing")
    validation_warnings_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_errors_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class ProposalBuilderRun(Base):
    __tablename__ = "proposal_builder_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("opportunities.id"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source_solicitation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("solicitations.id"), nullable=False, index=True
    )
    generation_mode: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING")
    model_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="INTAKE_COMPLETE")
    client_profile_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    onboarding_pack_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    playbook_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    playbook_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pricing_model_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    proposal_template_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    selection_source_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    opportunity_summary_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluation_criteria_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    submission_instructions_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    win_themes_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    section_drafting_plan_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    draft_package_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    export_manifest_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    warnings_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class ProposalPackageRun(Base):
    __tablename__ = "proposal_package_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("opportunities.id"), nullable=False, index=True
    )
    source_solicitation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("solicitations.id"), nullable=False, index=True
    )
    proposal_builder_run_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("proposal_builder_runs.id"), nullable=True, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="QUEUED", index=True)
    current_stage: Mapped[str | None] = mapped_column(String(60), nullable=True, index=True)
    generation_mode: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING")
    generation_reason: Mapped[str | None] = mapped_column(String(80), nullable=True)
    client_profile_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    onboarding_pack_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    playbook_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    playbook_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pricing_model_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    proposal_template_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    selection_source_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_by: Mapped[str] = mapped_column(String(120), nullable=False, default="operator")
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approved_pricing_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    approved_pricing_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approved_export_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    approved_export_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    customer_strategy_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_plan_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    pricing_package_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    form_package_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_findings_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    package_export_manifest_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    package_artifacts_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    blocking_issues_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    warnings_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class ProposalPackageStageRun(Base):
    __tablename__ = "proposal_package_stage_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    proposal_package_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("proposal_package_runs.id"), nullable=False, index=True
    )
    stage_name: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    stage_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING", index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    model_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    reasoning_profile: Mapped[str | None] = mapped_column(String(40), nullable=True)
    runtime_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    openai_response_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    token_usage_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_sources_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    artifact_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    blocking_issues_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    warnings_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    approval_required: Mapped[str | None] = mapped_column(String(40), nullable=True)
    approval_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
