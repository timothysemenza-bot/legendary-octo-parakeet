from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.compliance_matrix.schemas import ComplianceMatrixRowResponse
from app.modules.proposal_outline.schemas import ProposalOutlineResponse
from app.modules.rfp_parser.schemas import RequirementRecord, RfpStructuredFields
from app.modules.rfp_parser.schemas import RfpSourceDocumentRecord, SolicitationVersionRecord
from app.modules.submission_checklist.schemas import SubmissionReadinessResponse


class OpportunitySummaryArtifact(BaseModel):
    client_name: str | None = None
    opportunity_name: str | None = None
    solicitation_number: str | None = None
    issue_date: str | None = None
    questions_due_date: str | None = None
    proposal_due_date: str | None = None
    proposal_due_time: str | None = None
    contract_term: str | None = None
    site_geography: list[str] = Field(default_factory=list)
    scope_summary: str | None = None
    submission_method: str | None = None
    strategic_fit: str
    geographic_fit: str
    operational_fit: str
    revenue_scale_signal: str
    complexity_level: str
    risk_level: str
    recommended_next_action: str
    missing_information: list[str] = Field(default_factory=list)
    uncertainty_notes: list[str] = Field(default_factory=list)


class EvaluationCriterionArtifact(BaseModel):
    criterion: str
    description: str
    weight: str | None = None
    source_snippet: str | None = None


class SubmissionInstructionsArtifact(BaseModel):
    instruction_type: str
    instruction: str
    source_snippet: str | None = None


class ContentBlockArtifact(BaseModel):
    block_id: str
    title: str
    category: str
    tags: list[str] = Field(default_factory=list)


class ClientProfileOption(BaseModel):
    id: str
    display_name: str
    status: str


class ClientPricingModelOption(BaseModel):
    id: str
    name: str
    status: str
    onboarding_mode: str
    source_format: str | None = None


class ClientProposalTemplateOption(BaseModel):
    id: str
    name: str
    status: str
    source_filename: str
    valid: bool = False


class OpportunityProposalConfigArtifact(BaseModel):
    client_profile_id: str | None = None
    client_profile_name: str | None = None
    active_onboarding_pack_id: str | None = None
    active_onboarding_pack_name: str | None = None
    active_playbook_version: int | None = None
    client_environment_status: str | None = None
    pricing_model_id: str | None = None
    pricing_model_name: str | None = None
    proposal_template_id: str | None = None
    proposal_template_name: str | None = None
    client_profile_selection_source: str = "missing"
    pricing_model_selection_source: str = "missing"
    proposal_template_selection_source: str = "missing"
    setup_gaps: list[str] = Field(default_factory=list)
    validation_warnings: list[str] = Field(default_factory=list)
    validation_errors: list[str] = Field(default_factory=list)


class PricingModelLaborCategoryArtifact(BaseModel):
    code: str
    label: str
    hourly_rate: float
    burden_factor: float
    markup_factor: float
    default_hours_per_week: float = 0
    apply_site_multiplier: bool = True
    apply_continuous_coverage_multiplier: bool = True


class ClientPricingModelCanonicalArtifact(BaseModel):
    labor_categories: list[PricingModelLaborCategoryArtifact] = Field(default_factory=list)
    staffing_rules: dict[str, float | int | str | bool] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)
    workbook_mapping: dict[str, object] = Field(default_factory=dict)
    service_tags: list[str] = Field(default_factory=list)
    region_tags: list[str] = Field(default_factory=list)


class ValidationReportArtifact(BaseModel):
    status: str
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    details: dict[str, object] = Field(default_factory=dict)


class ClientPricingModelResponse(BaseModel):
    id: str
    client_profile_id: str
    name: str
    status: str
    onboarding_mode: str
    source_format: str | None = None
    source_filename: str | None = None
    source_file_path: str | None = None
    workbook_template_filename: str | None = None
    workbook_template_path: str | None = None
    canonical_model: ClientPricingModelCanonicalArtifact | None = None
    validation_report: ValidationReportArtifact | None = None
    created_at: datetime
    updated_at: datetime


class ClientProposalTemplateResponse(BaseModel):
    id: str
    client_profile_id: str
    name: str
    status: str
    source_filename: str
    storage_path: str
    anchor_map: dict[str, object] = Field(default_factory=dict)
    validation_report: ValidationReportArtifact | None = None
    created_at: datetime
    updated_at: datetime


class ClientProfileResponse(BaseModel):
    id: str
    display_name: str
    aliases: list[str] = Field(default_factory=list)
    approved_content_tags: list[str] = Field(default_factory=list)
    region_tags: list[str] = Field(default_factory=list)
    service_tags: list[str] = Field(default_factory=list)
    status: str
    active_onboarding_pack_id: str | None = None
    active_playbook_version: int | None = None
    client_environment_status: str | None = None
    default_pricing_model_id: str | None = None
    default_proposal_template_id: str | None = None
    default_pricing_model_name: str | None = None
    default_proposal_template_name: str | None = None
    pricing_models: list[ClientPricingModelResponse] = Field(default_factory=list)
    proposal_templates: list[ClientProposalTemplateResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ClientProfileCreateRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=255)
    aliases: list[str] = Field(default_factory=list)
    approved_content_tags: list[str] = Field(default_factory=list)
    region_tags: list[str] = Field(default_factory=list)
    service_tags: list[str] = Field(default_factory=list)
    status: str = "ACTIVE"


class ClientPricingModelCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    assumptions: list[str] = Field(default_factory=list)
    service_tags: list[str] = Field(default_factory=list)
    region_tags: list[str] = Field(default_factory=list)
    site_multiplier: float = 1.0
    continuous_coverage_multiplier: float = 1.35
    labor_categories: list[PricingModelLaborCategoryArtifact] = Field(default_factory=list)


class ClientProfileDefaultsRequest(BaseModel):
    default_pricing_model_id: str | None = None
    default_proposal_template_id: str | None = None


class OpportunityProposalConfigSelectionRequest(BaseModel):
    actor: str = Field(default="operator", min_length=2, max_length=120)
    target_id: str | None = None


class OnboardingValidationReport(BaseModel):
    status: str
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    details: dict[str, object] = Field(default_factory=dict)


class ClientOnboardingAssetResponse(BaseModel):
    id: str
    onboarding_pack_id: str
    asset_role: str
    asset_status: str
    classification_source: str
    source_filename: str
    source_path: str
    media_type: str
    extracted_text: str | None = None
    normalized_metadata: dict[str, object] = Field(default_factory=dict)
    validation_report: OnboardingValidationReport | None = None
    created_at: datetime
    updated_at: datetime


class ClientBehaviorProfileArtifact(BaseModel):
    default_tone: str = "formal and buyer-focused"
    proposal_sections: list[str] = Field(default_factory=list)
    approval_requirements: list[str] = Field(default_factory=list)
    required_attachments: list[str] = Field(default_factory=list)
    evaluation_emphasis: list[str] = Field(default_factory=list)
    preferred_terminology: list[str] = Field(default_factory=list)
    avoid_terminology: list[str] = Field(default_factory=list)
    service_offering_boundaries: list[str] = Field(default_factory=list)
    pricing_defaults: dict[str, object] = Field(default_factory=dict)
    export_defaults: dict[str, object] = Field(default_factory=dict)


class ClientPlaybookResponse(BaseModel):
    id: str
    onboarding_pack_id: str
    version: int
    status: str
    title: str
    narrative_guidance_md: str
    structured_rules: ClientBehaviorProfileArtifact
    approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ClientOnboardingPackResponse(BaseModel):
    id: str
    client_profile_id: str
    client_profile_name: str
    pack_name: str
    version: int
    status: str
    source_mode: str
    source_filename: str | None = None
    storage_dir: str
    manifest: dict[str, object] = Field(default_factory=dict)
    classification_report: OnboardingValidationReport | None = None
    validation_report: OnboardingValidationReport | None = None
    setup_gaps: list[str] = Field(default_factory=list)
    assets: list[ClientOnboardingAssetResponse] = Field(default_factory=list)
    playbook: ClientPlaybookResponse | None = None
    behavior_profile: ClientBehaviorProfileArtifact | None = None
    approved_at: datetime | None = None
    activated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ClientOnboardingPackUploadResponse(BaseModel):
    pack: ClientOnboardingPackResponse
    created_profile: bool = False


class ClientOnboardingPackApproveRequest(BaseModel):
    actor: str = Field(default="admin", min_length=2, max_length=120)
    narrative_guidance_md: str | None = None


class ClientOnboardingPackCreateRequest(BaseModel):
    actor: str = Field(default="admin", min_length=2, max_length=120)
    pack_name: str | None = None
    client_display_name: str | None = None


class ClientOnboardingPackActionRequest(BaseModel):
    actor: str = Field(default="admin", min_length=2, max_length=120)


class ClientOnboardingAssetUpdateRequest(BaseModel):
    actor: str = Field(default="admin", min_length=2, max_length=120)
    asset_role: str = Field(min_length=2, max_length=60)
    asset_status: str = Field(default="CANDIDATE", min_length=2, max_length=30)


class ClientPlaybookUpdateRequest(BaseModel):
    actor: str = Field(default="admin", min_length=2, max_length=120)
    title: str | None = None
    narrative_guidance_md: str = Field(min_length=10)


class FollowUpActionArtifact(BaseModel):
    title: str
    description: str
    action_label: str
    material_kind: str
    input_mode: str = "either"
    suggested_filename: str | None = None
    placeholder_text: str | None = None


class ProposalOutlineSectionArtifact(BaseModel):
    sequence: int = Field(ge=1)
    proposal_section: str
    owner_role: str
    section_purpose: str
    requirement_codes: list[str] = Field(default_factory=list)


class WinThemeArtifact(BaseModel):
    title: str
    rationale: str
    supporting_requirement_codes: list[str] = Field(default_factory=list)
    supporting_evaluation_criteria: list[str] = Field(default_factory=list)


class SectionDraftingPlanArtifact(BaseModel):
    proposal_section: str
    owner_role: str
    objective: str
    source_requirement_codes: list[str] = Field(default_factory=list)
    candidate_content_block_ids: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class DraftSectionArtifact(BaseModel):
    section_title: str
    body_markdown: str
    used_content_block_ids: list[str] = Field(default_factory=list)
    cited_requirement_codes: list[str] = Field(default_factory=list)


class DraftPackageArtifact(BaseModel):
    sections: list[DraftSectionArtifact] = Field(default_factory=list)
    client_sections: list[DraftSectionArtifact] = Field(default_factory=list)
    internal_notes: list[str] = Field(default_factory=list)
    unresolved_items: list[str] = Field(default_factory=list)
    editor_notes: str
    used_content_block_ids: list[str] = Field(default_factory=list)
    cited_requirement_codes: list[str] = Field(default_factory=list)


class ValuePropositionArtifact(BaseModel):
    title: str
    buyer_outcome: str
    differentiators: list[str] = Field(default_factory=list)
    supporting_requirement_codes: list[str] = Field(default_factory=list)
    supporting_asset_ids: list[str] = Field(default_factory=list)


class ProofPointArtifact(BaseModel):
    title: str
    statement: str
    supporting_asset_ids: list[str] = Field(default_factory=list)
    supporting_requirement_codes: list[str] = Field(default_factory=list)


class ReviewFindingArtifact(BaseModel):
    review_stage: str
    title: str
    severity: str
    disposition: str
    recommendation: str
    apmp_topic_id: str | None = None
    section_title: str | None = None
    source_refs: list[str] = Field(default_factory=list)


class ComplianceRequirementNormalizationArtifact(BaseModel):
    requirement_code: str
    normalized_requirement_text: str
    category: str
    requirement_type: str
    proposal_section: str
    source_excerpt: str | None = None
    confidence: str | None = None


class CustomerStrategyArtifact(BaseModel):
    buyer_priorities: list[str] = Field(default_factory=list)
    strategic_positioning: str
    bid_recommendation: str
    value_propositions: list[ValuePropositionArtifact] = Field(default_factory=list)
    proof_points: list[ProofPointArtifact] = Field(default_factory=list)
    win_theme_titles: list[str] = Field(default_factory=list)
    apmp_findings: list[ReviewFindingArtifact] = Field(default_factory=list)


class SectionBriefArtifact(BaseModel):
    section_title: str
    objective: str
    evaluator_priorities: list[str] = Field(default_factory=list)
    win_themes: list[str] = Field(default_factory=list)
    value_propositions: list[str] = Field(default_factory=list)
    proof_points: list[str] = Field(default_factory=list)
    cited_requirement_codes: list[str] = Field(default_factory=list)
    approved_asset_ids: list[str] = Field(default_factory=list)
    required_graphics_or_actions: list[str] = Field(default_factory=list)
    drafting_instructions: list[str] = Field(default_factory=list)


class ContentPlanArtifact(BaseModel):
    section_briefs: list[SectionBriefArtifact] = Field(default_factory=list)
    missing_asset_inputs: list[str] = Field(default_factory=list)
    apmp_findings: list[ReviewFindingArtifact] = Field(default_factory=list)


class PricingLineItemArtifact(BaseModel):
    labor_category: str
    hours_per_week: float
    hourly_rate: float
    burden_factor: float
    markup_factor: float
    loaded_hourly_cost: float
    annual_sell_price: float


class PricingPackageArtifact(BaseModel):
    workbook_path: str | None = None
    pricing_model_id: str | None = None
    pricing_model_name: str | None = None
    workbook_template_path: str | None = None
    pricing_narrative: str
    staffing_assumptions: list[str] = Field(default_factory=list)
    line_items: list[PricingLineItemArtifact] = Field(default_factory=list)
    annual_total: float = 0
    monthly_total: float = 0
    assumptions_log: list[str] = Field(default_factory=list)
    validation_errors: list[str] = Field(default_factory=list)
    unresolved_pricing_blockers: list[str] = Field(default_factory=list)
    approval_required: bool = True


class GeneratedFileArtifact(BaseModel):
    label: str
    path: str
    media_type: str


class FormPackageArtifact(BaseModel):
    completed_forms: list[GeneratedFileArtifact] = Field(default_factory=list)
    attachment_checklist: list[str] = Field(default_factory=list)
    resumes_packet_paths: list[str] = Field(default_factory=list)
    references_packet_paths: list[str] = Field(default_factory=list)
    unresolved_field_map_gaps: list[str] = Field(default_factory=list)
    blocked_forms: list[str] = Field(default_factory=list)


class ExportManifestArtifact(BaseModel):
    export_directory: str
    client_docx_path: str
    support_bundle_zip_path: str
    proposal_template_id: str | None = None
    proposal_template_name: str | None = None
    docx_path: str
    markdown_path: str
    json_path: str
    compliance_csv_path: str
    html_preview_path: str | None = None
    missing_input_checklist_path: str | None = None
    zip_path: str
    pricing_workbook_path: str | None = None
    forms_bundle_path: str | None = None
    attachments_bundle_path: str | None = None
    review_report_path: str | None = None
    production_checklist_path: str | None = None
    generated_at: datetime


class ProposalBuilderRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    opportunity_id: str
    version: int
    source_solicitation_id: str
    generation_mode: str
    generation_reason: str | None = None
    model_name: str | None
    status: str
    proposal_config: OpportunityProposalConfigArtifact | None = None
    opportunity_summary: OpportunitySummaryArtifact | None = None
    document_gaps: list[str] = Field(default_factory=list)
    assumption_flags: list[str] = Field(default_factory=list)
    evaluation_criteria: list[EvaluationCriterionArtifact] = Field(default_factory=list)
    submission_instructions: list[SubmissionInstructionsArtifact] = Field(default_factory=list)
    win_themes: list[WinThemeArtifact] = Field(default_factory=list)
    section_drafting_plan: list[SectionDraftingPlanArtifact] = Field(default_factory=list)
    draft_package: DraftPackageArtifact | None = None
    client_sections: list[DraftSectionArtifact] = Field(default_factory=list)
    internal_notes: list[str] = Field(default_factory=list)
    export_manifest: ExportManifestArtifact | None = None
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ProposalPackageStageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    stage_name: str
    stage_sequence: int
    status: str
    attempt_count: int
    model_name: str | None = None
    reasoning_profile: str | None = None
    runtime_seconds: int | None = None
    openai_response_id: str | None = None
    approval_required: str | None = None
    approval_status: str | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    blocking_issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    failure_reason: str | None = None
    artifact: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class ProposalPackageRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    opportunity_id: str
    source_solicitation_id: str
    version: int
    status: str
    current_stage: str | None = None
    generation_mode: str
    generation_reason: str | None = None
    proposal_config: OpportunityProposalConfigArtifact | None = None
    active_onboarding_pack_id: str | None = None
    active_playbook_version: int | None = None
    client_environment_status: str | None = None
    setup_gaps: list[str] = Field(default_factory=list)
    requested_by: str
    requested_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    approved_pricing_by: str | None = None
    approved_pricing_at: datetime | None = None
    approved_export_by: str | None = None
    approved_export_at: datetime | None = None
    blocking_issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    customer_strategy: CustomerStrategyArtifact | None = None
    content_plan: ContentPlanArtifact | None = None
    pricing_package: PricingPackageArtifact | None = None
    form_package: FormPackageArtifact | None = None
    review_findings: list[ReviewFindingArtifact] = Field(default_factory=list)
    export_manifest: ExportManifestArtifact | None = None
    package_artifacts: dict[str, object] = Field(default_factory=dict)
    stages: list[ProposalPackageStageResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ProposalPackageRunCreateRequest(BaseModel):
    actor: str = Field(default="operator", min_length=2, max_length=120)
    demo_mode: bool = False


class ProposalPackageStageApprovalRequest(BaseModel):
    actor: str = Field(default="operator", min_length=2, max_length=120)
    stage_name: str = Field(min_length=2, max_length=80)
    demo_mode: bool | None = None


class ProposalBuilderStageRequest(BaseModel):
    actor: str = Field(default="operator", min_length=2, max_length=120)


class ProposalBuilderSectionUpdateRequest(BaseModel):
    actor: str = Field(default="operator", min_length=2, max_length=120)
    section_index: int = Field(ge=0)
    body_markdown: str = Field(min_length=1)


class ProposalBuilderStartResult(BaseModel):
    opportunity_id: str | None = None
    draft_id: str
    intake_status: str
    needs_confirmation: bool = False
    suggested_name: str | None = None
    suggested_client: str | None = None
    warnings: list[str] = Field(default_factory=list)


class ProposalBuilderWorkspaceResponse(BaseModel):
    opportunity_id: str
    opportunity_name: str
    client_name: str
    solicitation_id: str | None = None
    solicitation_version: int | None = None
    source_documents: list[RfpSourceDocumentRecord] = Field(default_factory=list)
    solicitation_versions: list[SolicitationVersionRecord] = Field(default_factory=list)
    extracted_deadline: str | None = None
    generation_mode: str | None = None
    generation_reason: str | None = None
    model_name: str | None = None
    proposal_config: OpportunityProposalConfigArtifact | None = None
    active_onboarding_pack_id: str | None = None
    active_playbook_version: int | None = None
    client_environment_status: str | None = None
    setup_gaps: list[str] = Field(default_factory=list)
    available_client_profiles: list[ClientProfileOption] = Field(default_factory=list)
    available_pricing_models: list[ClientPricingModelOption] = Field(default_factory=list)
    available_proposal_templates: list[ClientProposalTemplateOption] = Field(default_factory=list)
    structured_fields: RfpStructuredFields | None = None
    opportunity_summary: OpportunitySummaryArtifact | None = None
    document_gaps: list[str] = Field(default_factory=list)
    assumption_flags: list[str] = Field(default_factory=list)
    requirements_list: list[RequirementRecord] = Field(default_factory=list)
    evaluation_criteria: list[EvaluationCriterionArtifact] = Field(default_factory=list)
    submission_instructions: list[SubmissionInstructionsArtifact] = Field(default_factory=list)
    compliance_matrix: list[ComplianceMatrixRowResponse] = Field(default_factory=list)
    proposal_outline: ProposalOutlineResponse | None = None
    win_themes: list[WinThemeArtifact] = Field(default_factory=list)
    section_drafting_plan: list[SectionDraftingPlanArtifact] = Field(default_factory=list)
    draft_package: DraftPackageArtifact | None = None
    client_sections: list[DraftSectionArtifact] = Field(default_factory=list)
    internal_notes: list[str] = Field(default_factory=list)
    export_manifest: ExportManifestArtifact | None = None
    submission_readiness: SubmissionReadinessResponse | None = None
    recommended_materials: list[str] = Field(default_factory=list)
    follow_up_actions: list[FollowUpActionArtifact] = Field(default_factory=list)
    workflow_summary: dict[str, object] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    detail_links: dict[str, str] = Field(default_factory=dict)


class ExtractStageArtifactResponse(BaseModel):
    opportunity_summary: OpportunitySummaryArtifact
    evaluation_criteria: list[EvaluationCriterionArtifact] = Field(default_factory=list)
    submission_instructions: list[SubmissionInstructionsArtifact] = Field(default_factory=list)
    normalized_requirements: list[ComplianceRequirementNormalizationArtifact] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SkeletonStageArtifactResponse(BaseModel):
    proposal_outline: list[ProposalOutlineSectionArtifact] = Field(default_factory=list)
    win_themes: list[WinThemeArtifact] = Field(default_factory=list)
    section_drafting_plan: list[SectionDraftingPlanArtifact] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DraftStageArtifactResponse(BaseModel):
    draft_package: DraftPackageArtifact
    warnings: list[str] = Field(default_factory=list)
