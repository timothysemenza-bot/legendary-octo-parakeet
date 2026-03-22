from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.core.config import (
    BASE_DIR,
    BOSSKEY_OPENAI_DRAFT_TIMEOUT_SECONDS,
    BOSSKEY_OPENAI_GLOBAL_MAX_ESTIMATED_INPUT_TOKENS,
    BOSSKEY_OPENAI_GLOBAL_MAX_OUTPUT_TOKENS,
    BOSSKEY_OPENAI_EXTRACT_TIMEOUT_SECONDS,
    BOSSKEY_OPENAI_MAX_TIMEOUT_SECONDS,
    BOSSKEY_OPENAI_SKELETON_TIMEOUT_SECONDS,
    BOSSKEY_PROPOSAL_BUILDER_ALLOW_CACHED_DEMO_FALLBACK,
    BOSSKEY_PROPOSAL_BUILDER_ALLOW_LIVE_STAGE_FALLBACK,
)
from app.modules.compliance_matrix.schemas import ComplianceMatrixRowResponse
from app.modules.compliance_matrix.service import ComplianceMatrixService
from app.modules.janitorial_os.models import ProposalWorkflowSummary
from app.modules.opportunity_intake.models import Opportunity
from app.modules.opportunity_intake.schemas import OpportunityIntakeDraftConfirmRequest, OpportunityIntakeDraftResponse
from app.modules.opportunity_intake.service import OpportunityIntakeService
from app.modules.proposal_builder.client_profiles import ClientProfileError, ClientProfileService
from app.modules.proposal_builder.content_library import content_block_inventory, select_candidate_blocks
from app.modules.proposal_builder.export import build_export_bundle
from app.modules.proposal_builder.models import ProposalBuilderRun, ProposalPackageRun
from app.modules.proposal_builder.openai_client import OpenAIStructuredOutputError, ProposalBuilderOpenAIClient
from app.modules.proposal_builder.schemas import (
    ComplianceRequirementNormalizationArtifact,
    DraftPackageArtifact,
    DraftSectionArtifact,
    DraftStageArtifactResponse,
    EvaluationCriterionArtifact,
    ExportManifestArtifact,
    ExtractStageArtifactResponse,
    FollowUpActionArtifact,
    OpportunitySummaryArtifact,
    ProposalBuilderRunResponse,
    ProposalBuilderStartResult,
    ProposalBuilderWorkspaceResponse,
    ProposalOutlineSectionArtifact,
    SectionDraftingPlanArtifact,
    SkeletonStageArtifactResponse,
    SubmissionInstructionsArtifact,
    WinThemeArtifact,
)
from app.modules.proposal_outline.schemas import (
    ProposalOutlineManualCreateRequest,
    ProposalOutlineManualSectionInput,
    ProposalOutlineResponse,
)
from app.modules.proposal_outline.service import ProposalOutlineService
from app.modules.rfp_parser.document_reader import extract_text_from_mixed_inputs
from app.modules.rfp_parser.models import ComplianceMatrixRow, Requirement, Solicitation
from app.modules.rfp_parser.schemas import RequirementRecord, RfpReparseRequest, RfpSourceDocumentInput, RfpStructuredFields
from app.modules.rfp_parser.service import RfpParserService
from app.modules.submission_checklist.service import SubmissionChecklistService


DEMO_SAMPLE_FILENAME = "bosskey-demo-airport-facilities-rfp.txt"
DEMO_SAMPLE_PATH = BASE_DIR / "demo-artifacts" / DEMO_SAMPLE_FILENAME
DEMO_CACHE_PATH = BASE_DIR / "demo-artifacts" / "proposal-builder-demo-cache.json"
OWNER_ROLE_ORDER = ("Proposal Lead", "Operations Lead", "Pricing/Finance", "SME")
GENERATION_REASON_PREFIX = "__generation_reason__:"
CLIENT_META_PHRASES = (
    "phase 1",
    "proposal team",
    "compliance matrix",
    "finish in word",
    "structured workflow",
    "proposal starter",
)
SECTION_BLUEPRINT = (
    ("Executive Summary", "Proposal Lead", "Open with buyer priorities, delivery confidence, and differentiators tied to the solicitation."),
    ("Technical Approach", "Operations Lead", "Describe the operating model, service controls, and issue-response approach."),
    ("Management and Staffing Plan", "Operations Lead", "Define supervisory structure, staffing coverage, and local leadership commitments."),
    ("Transition and Mobilization Plan", "Operations Lead", "Show how startup, onboarding, and early performance controls will be executed."),
    ("Past Performance", "SME", "Provide comparable contract experience and proof points tied to the buyer's priorities."),
    ("Pricing and Commercials", "Pricing/Finance", "Complete pricing assumptions, workbook inputs, and commercial framing."),
    ("Compliance and Attachments", "Proposal Lead", "Track forms, certifications, insurance, and addenda acknowledgements."),
)
SECTION_OWNER_MAP = {name: owner for name, owner, _purpose in SECTION_BLUEPRINT}
SECTION_PURPOSE_MAP = {name: purpose for name, _owner, purpose in SECTION_BLUEPRINT}
ALLOWED_REQUIREMENT_CATEGORIES = {"GENERAL", "TECHNICAL", "MANAGEMENT", "PRICING", "PAST_PERFORMANCE"}
ALLOWED_REQUIREMENT_TYPES = {"COMPLIANCE_REQUIRED", "EVALUATION_SIGNAL", "CONTEXT_ONLY"}
CURRENCY_PATTERN = re.compile(r"\$\s?\d[\d,]*(?:\.\d{2})?")
STAGE_INPUT_TOKEN_CAPS = {
    "extract": 10_000,
    "skeleton": 12_000,
    "draft": 16_000,
    "customer_strategy": 10_000,
    "content_plan": 12_000,
    "full_draft": 16_000,
    "pink_team_review": 12_000,
    "red_team_review": 12_000,
    "gold_team_production_review": 10_000,
}
STAGE_OUTPUT_TOKEN_CAPS = {
    "extract": 2_200,
    "skeleton": 2_600,
    "draft": 4_800,
    "customer_strategy": 2_000,
    "content_plan": 3_000,
    "full_draft": 5_500,
    "pink_team_review": 2_000,
    "red_team_review": 2_000,
    "gold_team_production_review": 1_800,
}


class ProposalBuilderError(RuntimeError):
    pass


def _parse_json(raw: str | None, default: Any) -> Any:
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def _normalize_space(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _split_lines(value: str | None) -> list[str]:
    if not value:
        return []
    return [_normalize_space(line) for line in value.splitlines() if _normalize_space(line)]


def _short_label(value: str, *, words: int = 6) -> str:
    tokens = value.split()
    short = " ".join(tokens[:words]).rstrip(" ,;:.")
    return short if short else value


def _parse_date(raw: str | None) -> date | None:
    if not raw:
        return None
    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _currency_signal(value: float) -> str:
    if value >= 1_000_000:
        return f"Estimated intake value is ${value:,.0f}, which suggests a material pursuit worth formal review."
    if value >= 250_000:
        return f"Estimated intake value is ${value:,.0f}, which supports a structured response workflow."
    return f"Estimated intake value is ${value:,.0f}; confirm final scope and pricing assumptions before full drafting."


def _fit_label(score: int) -> str:
    if score >= 5:
        return "Very strong fit based on the intake assumptions currently on file."
    if score >= 4:
        return "Good fit for a disciplined facilities proposal workflow."
    if score >= 3:
        return "Possible fit, but it should be validated with operations and local leadership."
    return "Fit is uncertain and needs explicit bid/no-bid review."


def _ensure_list(values: list[str], *extra: str) -> list[str]:
    ordered: list[str] = []
    for value in list(values) + list(extra):
        cleaned = _normalize_space(value)
        if cleaned and cleaned not in ordered:
            ordered.append(cleaned)
    return ordered


def _coerce_draft_stage_artifact(parsed: Any) -> DraftStageArtifactResponse:
    if isinstance(parsed, DraftStageArtifactResponse):
        return parsed
    if isinstance(parsed, dict):
        if "draft_package" in parsed:
            return DraftStageArtifactResponse.model_validate(parsed)
        if "section_title" in parsed and "body_markdown" in parsed:
            return DraftStageArtifactResponse(
                draft_package=DraftPackageArtifact(
                    sections=[DraftSectionArtifact.model_validate(parsed)],
                    client_sections=[DraftSectionArtifact.model_validate(parsed)],
                    internal_notes=[],
                    unresolved_items=[],
                    editor_notes="Recovered a draft section from a loosely structured model response.",
                    used_content_block_ids=list(parsed.get("used_content_block_ids") or []),
                    cited_requirement_codes=list(parsed.get("cited_requirement_codes") or []),
                ),
                warnings=["Recovered draft content from a loosely structured model response."],
            )
        if any(key in parsed for key in ("sections", "client_sections", "editor_notes", "internal_notes", "unresolved_items")):
            return DraftStageArtifactResponse(
                draft_package=DraftPackageArtifact.model_validate(parsed),
                warnings=list(parsed.get("warnings") or []),
            )
    if isinstance(parsed, list) and parsed and all(isinstance(item, dict) for item in parsed):
        sections = [DraftSectionArtifact.model_validate(item) for item in parsed]
        return DraftStageArtifactResponse(
            draft_package=DraftPackageArtifact(
                sections=sections,
                client_sections=list(sections),
                internal_notes=[],
                unresolved_items=[],
                editor_notes="Recovered draft sections from a list-shaped model response.",
                used_content_block_ids=_unique_strings(
                    [block_id for section in sections for block_id in section.used_content_block_ids]
                ),
                cited_requirement_codes=_unique_strings(
                    [code for section in sections for code in section.cited_requirement_codes]
                ),
            ),
            warnings=["Recovered draft content from a list-shaped model response."],
        )
    return DraftStageArtifactResponse.model_validate(parsed)


def _rank_risk(missing_information: list[str], structured_fields: RfpStructuredFields, requirement_count: int) -> str:
    major_gap_count = len(missing_information)
    if not structured_fields.proposal_due_date or not structured_fields.submission_method:
        return "High"
    if major_gap_count >= 4 or requirement_count >= 20:
        return "High"
    if major_gap_count >= 2 or requirement_count >= 10:
        return "Medium"
    return "Low to medium"


def _complexity_level(structured_fields: RfpStructuredFields, requirement_count: int) -> str:
    indicator_count = len(structured_fields.mandatory_forms) + len(structured_fields.mandatory_meetings)
    if requirement_count >= 18 or indicator_count >= 6:
        return "High"
    if requirement_count >= 8 or indicator_count >= 3:
        return "Moderate"
    return "Low to moderate"


def _workflow_stage_flags(workspace: ProposalBuilderWorkspaceResponse) -> list[dict[str, object]]:
    return [
        {"label": "Upload RFP", "complete": True, "description": "Create one opportunity record from the uploaded package."},
        {
            "label": "Review Requirements",
            "complete": workspace.opportunity_summary is not None,
            "description": "Inspect dates, requirements, evaluation criteria, and submission instructions.",
        },
        {
            "label": "Build Proposal Skeleton",
            "complete": workspace.proposal_outline is not None and bool(workspace.win_themes),
            "description": "Map requirements into sections, owners, and win themes.",
        },
        {
            "label": "Generate Draft",
            "complete": workspace.draft_package is not None,
            "description": "Generate buyer-facing draft sections for the executive, technical, staffing, and transition narrative.",
        },
        {
            "label": "Export Package",
            "complete": workspace.export_manifest is not None,
            "description": "Download a Word-ready package plus the support bundle.",
        },
    ]


def _unique_strings(values: list[str]) -> list[str]:
    unique: list[str] = []
    for value in values:
        cleaned = _normalize_space(value)
        if cleaned and cleaned not in unique:
            unique.append(cleaned)
    return unique


def _extract_warning_metadata(raw_items: list[Any]) -> tuple[list[str], str | None]:
    warnings: list[str] = []
    generation_reason = None
    for item in raw_items:
        text = _normalize_space(str(item))
        if not text:
            continue
        if text.startswith(GENERATION_REASON_PREFIX):
            generation_reason = text.split(":", 1)[1] or None
            continue
        warnings.append(text)
    return warnings, generation_reason


def _pack_warning_payload(existing_items: list[Any], warnings: list[str], generation_reason: str | None) -> str:
    existing_warnings, _existing_reason = _extract_warning_metadata(existing_items)
    payload = _unique_strings(existing_warnings + warnings)
    if generation_reason:
        payload.append(f"{GENERATION_REASON_PREFIX}{generation_reason}")
    return json.dumps(payload)


def _generation_reason_from_exception(exc: Exception | None) -> str:
    if exc is None:
        return "missing_api_key"
    lowered = str(exc).lower()
    if "openai_api_key" in lowered or "api key" in lowered:
        return "missing_api_key"
    if "usage safeguard blocked" in lowered or ("estimated input tokens" in lowered and "configured cap" in lowered):
        return "token_budget_exceeded"
    if "timeout" in lowered or "timed out" in lowered:
        return "timeout"
    if "invalid json" in lowered or "structured output" in lowered or "json root" in lowered or "model_validate" in lowered:
        return "structured_output_validation_failed"
    return "generation_error"


def _canonical_section_name(raw_name: str) -> str:
    cleaned = _normalize_space(raw_name)
    lowered = cleaned.lower()
    if cleaned in SECTION_OWNER_MAP:
        return cleaned
    alias_map = {
        "technical / management approach": "Technical Approach",
        "technical and management approach": "Technical Approach",
        "technical management approach": "Technical Approach",
        "pricing & commercials": "Pricing and Commercials",
        "compliance & attachments": "Compliance and Attachments",
        "management plan": "Management and Staffing Plan",
        "technical approach": "Technical Approach",
        "transition plan": "Transition and Mobilization Plan",
    }
    return alias_map.get(lowered, cleaned)


def _requirement_section_name(requirement: Requirement | RequirementRecord) -> str:
    lowered = requirement.requirement_text.lower()
    category = getattr(requirement, "category", "GENERAL")
    if any(marker in lowered for marker in ("reference", "references", "past performance", "comparable contract")) or category == "PAST_PERFORMANCE":
        return "Past Performance"
    if any(marker in lowered for marker in ("resume", "resumes", "staffing plan", "supervisory coverage", "staffing coverage", "contract manager", "supervisor")) or category == "MANAGEMENT":
        return "Management and Staffing Plan"
    if any(marker in lowered for marker in ("transition", "mobilization", "notice of intent to award", "startup")):
        return "Transition and Mobilization Plan"
    if any(marker in lowered for marker in ("insurance", "certificate", "attachment", "attachments", "certification", "forms", "form", "workbook", "addenda", "addendum")):
        return "Compliance and Attachments"
    if any(marker in lowered for marker in ("pricing", "price", "cost", "commercial")) or category == "PRICING":
        return "Pricing and Commercials"
    if any(marker in lowered for marker in ("quality assurance", "issue log", "incident-response", "incident response", "technical approach", "janitorial", "cleaning", "scope of work")) or category == "TECHNICAL":
        return "Technical Approach"
    return "Executive Summary"


def _owner_for_section(section_name: str) -> str:
    return SECTION_OWNER_MAP.get(section_name, "Proposal Lead")


def _purpose_for_section(section_name: str) -> str:
    return SECTION_PURPOSE_MAP.get(section_name, "Address the buyer's requirements in a clear, scorable format.")


def _buyer_facing_text(value: str) -> str:
    cleaned = value.strip()
    for phrase in CLIENT_META_PHRASES:
        cleaned = re.sub(re.escape(phrase), "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _contract_value_signal(content_text: str | None) -> str:
    if not content_text:
        return "Revenue scale is not stated in the RFP package; confirm the commercial size during pricing kickoff."
    for line in content_text.splitlines():
        lowered = line.lower()
        if not any(marker in lowered for marker in ("budget", "not to exceed", "estimated", "contract value", "annual value", "pricing")):
            continue
        match = CURRENCY_PATTERN.search(line)
        if match:
            return f"RFP budget signal: {match.group(0)}. Confirm the pricing basis and contract economics during kickoff."
    return "Revenue scale is not stated in the RFP package; confirm the commercial size during pricing kickoff."


def _source_document_gaps(
    *,
    solicitation: Solicitation | None,
    source_documents: list[Any],
) -> list[str]:
    if solicitation is None:
        return []
    content_text = solicitation.content_text.lower()
    filenames = [str(getattr(item, "source_filename", "")).lower() for item in source_documents]
    gaps: list[str] = []
    if "2026 rfp staffing-pricing-questions" in content_text and not any(
        any(marker in name for marker in ("staffing", "pricing", "worksheet", "workbook")) and name.endswith((".xlsx", ".xls", ".csv"))
        for name in filenames
    ):
        gaps.append(
            "The owner-issued staffing and pricing workbook referenced in the RFP was not included in the uploaded source package."
        )
    if "w-9 form" in content_text and not any("w-9" in name or "w9" in name for name in filenames):
        gaps.append("A completed W-9 was referenced in the RFP files but was not included in the uploaded source package.")
    if "service agreement" in content_text and not any("service agreement" in name for name in filenames):
        gaps.append("The referenced Highwoods service agreement file was not included in the uploaded source package.")
    return gaps


class ProposalBuilderService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _profile_service(self) -> ClientProfileService:
        return ClientProfileService(self.db)

    def demo_sample_text(self) -> str:
        if not DEMO_SAMPLE_PATH.exists():
            raise ProposalBuilderError("Demo sample fixture is missing.")
        return DEMO_SAMPLE_PATH.read_text(encoding="utf-8")

    def _stage_timeout_seconds(self, *, stage_name: str, source_text_length: int, requirement_count: int) -> int:
        if stage_name == "extract":
            base_timeout = BOSSKEY_OPENAI_EXTRACT_TIMEOUT_SECONDS
        elif stage_name == "skeleton":
            base_timeout = BOSSKEY_OPENAI_SKELETON_TIMEOUT_SECONDS
        elif stage_name == "draft":
            base_timeout = BOSSKEY_OPENAI_DRAFT_TIMEOUT_SECONDS
        else:
            base_timeout = BOSSKEY_OPENAI_DRAFT_TIMEOUT_SECONDS

        length_increment = max(source_text_length - 12_000, 0) // 8_000 * 30
        requirement_increment = max(requirement_count - 8, 0) // 6 * 20
        return min(base_timeout + length_increment + requirement_increment, BOSSKEY_OPENAI_MAX_TIMEOUT_SECONDS)

    def _openai_client(self, *, stage_name: str, source_text_length: int, requirement_count: int) -> ProposalBuilderOpenAIClient:
        return ProposalBuilderOpenAIClient(
            timeout_seconds=self._stage_timeout_seconds(
                stage_name=stage_name,
                source_text_length=source_text_length,
                requirement_count=requirement_count,
            )
        )

    def _stage_ai_guardrails(self, *, stage_name: str, source_text_length: int, requirement_count: int) -> dict[str, int]:
        base_input_cap = STAGE_INPUT_TOKEN_CAPS.get(stage_name, STAGE_INPUT_TOKEN_CAPS["draft"])
        base_output_cap = STAGE_OUTPUT_TOKEN_CAPS.get(stage_name, STAGE_OUTPUT_TOKEN_CAPS["draft"])
        length_increment = max(source_text_length - 12_000, 0) // 10_000 * 800
        requirement_increment = max(requirement_count - 8, 0) // 8 * 400
        input_cap = min(
            base_input_cap + length_increment + requirement_increment,
            BOSSKEY_OPENAI_GLOBAL_MAX_ESTIMATED_INPUT_TOKENS,
        )
        output_cap = min(
            base_output_cap + max(requirement_count - 10, 0) // 10 * 200,
            BOSSKEY_OPENAI_GLOBAL_MAX_OUTPUT_TOKENS,
        )
        return {
            "max_estimated_input_tokens": input_cap,
            "max_output_tokens": output_cap,
        }

    def _record_stage_failure(
        self,
        *,
        opportunity_id: str,
        solicitation_id: str,
        stage_name: str,
        actor: str,
        generation_reason: str,
        message: str,
        model_name: str | None,
    ) -> ProposalBuilderRun:
        run = self._ensure_run(opportunity_id, solicitation_id)
        run.generation_mode = "ERROR"
        run.model_name = model_name
        run.status = f"{stage_name.upper()}_FAILED"
        run.warnings_json = _pack_warning_payload(_parse_json(run.warnings_json, []), [message], generation_reason)
        self.db.flush()
        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=actor,
            action=f"proposal_builder_{stage_name}_failed",
            after_state_json=json.dumps(
                {
                    "generation_reason": generation_reason,
                    "message": message,
                    "model_name": model_name,
                }
            ),
        )
        self.db.commit()
        self.db.refresh(run)
        return run

    def _live_stage_error_message(self, *, stage_label: str, timeout_seconds: int, exc: Exception) -> str:
        reason = _generation_reason_from_exception(exc)
        if reason == "token_budget_exceeded":
            return (
                f"{stage_label} was stopped by the token-usage safeguard before the model call was sent. "
                "Add less context, upload supporting material in smaller batches, or continue iteratively instead of sending everything at once."
            )
        if reason == "timeout":
            return (
                f"{stage_label} exceeded the live-model wait window of {timeout_seconds} seconds. "
                "Increase the stage timeout or rerun the step; the app did not generate a deterministic fallback."
            )
        if reason == "missing_api_key":
            return f"{stage_label} could not start because OPENAI_API_KEY is not configured."
        return f"{stage_label} did not complete successfully: {exc}"

    def _is_demo_sample_solicitation(self, solicitation: Solicitation | None) -> bool:
        if solicitation is None:
            return False
        if solicitation.source_filename == DEMO_SAMPLE_FILENAME:
            return True
        content = solicitation.content_text.lower()
        return "metro regional airport authority" in content and "mr-aa-2026-041" in content

    def _latest_solicitation(self, opportunity_id: str) -> Solicitation | None:
        stmt = (
            select(Solicitation)
            .where(Solicitation.opportunity_id == opportunity_id)
            .order_by(Solicitation.version.desc(), Solicitation.created_at.desc())
        )
        return self.db.scalars(stmt).first()

    def _latest_run(self, opportunity_id: str) -> ProposalBuilderRun | None:
        stmt = (
            select(ProposalBuilderRun)
            .where(ProposalBuilderRun.opportunity_id == opportunity_id)
            .order_by(ProposalBuilderRun.version.desc(), ProposalBuilderRun.updated_at.desc())
        )
        return self.db.scalars(stmt).first()

    def _next_run_version(self, opportunity_id: str) -> int:
        latest = self._latest_run(opportunity_id)
        return 1 if latest is None else latest.version + 1

    def _ensure_run(self, opportunity_id: str, solicitation_id: str) -> ProposalBuilderRun:
        existing = self._latest_run(opportunity_id)
        if existing and existing.source_solicitation_id == solicitation_id:
            self._profile_service().apply_snapshot_to_run(opportunity_id, existing)
            return existing
        created = ProposalBuilderRun(
            opportunity_id=opportunity_id,
            version=self._next_run_version(opportunity_id),
            source_solicitation_id=solicitation_id,
            generation_mode="PENDING",
            status="INTAKE_COMPLETE",
            warnings_json="[]",
        )
        self.db.add(created)
        self.db.flush()
        self._profile_service().apply_snapshot_to_run(opportunity_id, created)
        return created

    def _latest_outline_response(self, opportunity_id: str) -> ProposalOutlineResponse | None:
        outline_service = ProposalOutlineService(self.db)
        latest = outline_service.get_latest(opportunity_id)
        if not latest:
            return None
        sections = outline_service.parse_sections(latest)
        return ProposalOutlineResponse(
            id=latest.id,
            opportunity_id=latest.opportunity_id,
            version=latest.version,
            source=latest.source,
            sections=sections,
            created_at=latest.created_at,
        )

    def _latest_requirements(self, solicitation_id: str) -> list[Requirement]:
        stmt = select(Requirement).where(Requirement.solicitation_id == solicitation_id).order_by(Requirement.requirement_code.asc())
        return list(self.db.scalars(stmt))

    def _structured_fields(self, solicitation: Solicitation | None) -> RfpStructuredFields | None:
        if not solicitation or not solicitation.structured_fields_json:
            return None
        return RfpStructuredFields.model_validate(_parse_json(solicitation.structured_fields_json, {}))

    def _field_provenance(self, solicitation: Solicitation | None) -> dict[str, list[str]]:
        if not solicitation or not solicitation.field_provenance_json:
            return {}
        raw = _parse_json(solicitation.field_provenance_json, {})
        if not isinstance(raw, dict):
            return {}
        cleaned: dict[str, list[str]] = {}
        for key, value in raw.items():
            if isinstance(value, list):
                cleaned[str(key)] = [item for item in (_normalize_space(str(entry)) for entry in value) if item]
        return cleaned

    def _repair_structured_fields_from_extract(
        self,
        *,
        solicitation: Solicitation,
        structured_fields: RfpStructuredFields,
        artifact: ExtractStageArtifactResponse,
    ) -> RfpStructuredFields:
        provenance = self._field_provenance(solicitation)
        changed = False

        def set_if_missing(field_name: str, value: str | None, source_label: str) -> None:
            nonlocal changed
            cleaned = _normalize_space(value)
            current = getattr(structured_fields, field_name)
            if not cleaned or current:
                return
            setattr(structured_fields, field_name, cleaned)
            provenance[field_name] = _unique_strings(provenance.get(field_name, []) + [f"AI extract repair: {source_label}"])
            changed = True

        summary = artifact.opportunity_summary
        set_if_missing("client_name", summary.client_name, "client_name")
        set_if_missing("opportunity_name", summary.opportunity_name, "opportunity_name")
        set_if_missing("solicitation_number", summary.solicitation_number, "solicitation_number")
        set_if_missing("issue_date", summary.issue_date, "issue_date")
        set_if_missing("questions_due_date", summary.questions_due_date, "questions_due_date")
        set_if_missing("proposal_due_date", summary.proposal_due_date, "proposal_due_date")
        set_if_missing("proposal_due_time", summary.proposal_due_time, "proposal_due_time")
        set_if_missing("contract_term", summary.contract_term, "contract_term")
        set_if_missing("scope_summary", summary.scope_summary, "scope_summary")
        set_if_missing("submission_method", summary.submission_method, "submission_method")

        if summary.site_geography and not structured_fields.geography:
            structured_fields.geography = _unique_strings(summary.site_geography)
            provenance["geography"] = _unique_strings(provenance.get("geography", []) + ["AI extract repair: site_geography"])
            changed = True

        if changed:
            solicitation.structured_fields_json = json.dumps(structured_fields.model_dump())
            solicitation.field_provenance_json = json.dumps(provenance)
            if structured_fields.proposal_due_date:
                solicitation.extracted_deadline = structured_fields.proposal_due_date
        return structured_fields

    def _cached_demo_artifact(self, stage_name: str, model: type[Any]) -> Any | None:
        if not DEMO_CACHE_PATH.exists():
            return None
        try:
            payload = _parse_json(DEMO_CACHE_PATH.read_text(encoding="utf-8"), {})
        except OSError:
            return None
        stage_payload = payload.get(stage_name)
        if not isinstance(stage_payload, dict):
            return None
        try:
            return model.model_validate(stage_payload)
        except Exception:
            return None

    def _document_gaps(self, structured_fields: RfpStructuredFields | None, requirements: list[Requirement | RequirementRecord]) -> list[str]:
        if structured_fields is None:
            return ["RFP details have not been fully parsed yet; confirm the due date, submission method, and required attachments."]

        requirement_text = " ".join(row.requirement_text.lower() for row in requirements)
        gaps: list[str] = []
        if not structured_fields.proposal_due_date:
            gaps.append("Confirm the proposal due date from the solicitation package.")
        if not structured_fields.proposal_due_time:
            gaps.append("Confirm the exact proposal due time before final production.")
        if not structured_fields.submission_method:
            gaps.append("Confirm the final submission portal or delivery method.")
        if not structured_fields.questions_due_date:
            gaps.append("Confirm the deadline for clarification questions.")
        if structured_fields.insurance_requirements:
            gaps.append("Prepare current certificates of insurance that match the stated coverage requirements.")
        if structured_fields.mandatory_forms or "addenda" in requirement_text or "attachment" in requirement_text or "workbook" in requirement_text:
            gaps.append("Complete required attachments, certification forms, pricing workbooks, and addenda acknowledgements.")
        if "reference" in requirement_text:
            gaps.append("Collect comparable contract references and confirm who will serve as reference contacts.")
        if "resume" in requirement_text or "staffing plan" in requirement_text:
            gaps.append("Assemble the staffing plan inputs, key resumes, and supervisory coverage details needed for the final package.")
        return _unique_strings(gaps)

    def _assumption_flags(
        self,
        *,
        opportunity: Opportunity,
        solicitation: Solicitation | None,
        structured_fields: RfpStructuredFields | None,
        requirements: list[Requirement | RequirementRecord],
    ) -> list[str]:
        flags: list[str] = []
        requirement_text = " ".join(row.requirement_text.lower() for row in requirements)
        content_text = solicitation.content_text if solicitation else ""
        if not CURRENCY_PATTERN.search(content_text or ""):
            flags.append("The RFP does not state contract value, so the client-facing draft intentionally avoids revenue claims or budget language.")
        if not structured_fields or not structured_fields.incumbent_hints:
            flags.append("Incumbent provider information is not stated in the parsed package.")
        if "staffing plan" in requirement_text:
            flags.append("The solicitation requires a staffing plan, but staffing quantities still need operations and pricing input.")
        if "local office" not in content_text.lower():
            flags.append("Local office address, leadership names, and escalation contacts must be inserted from approved company content.")
        if opportunity.estimated_contract_value == 250000 and not CURRENCY_PATTERN.search(content_text or ""):
            flags.append("A default intake value exists in the operator record, but it is treated as an internal placeholder and omitted from the exported draft.")
        return _unique_strings(flags)

    def _rank_risk(
        self,
        *,
        document_gaps: list[str],
        assumption_flags: list[str],
        structured_fields: RfpStructuredFields,
        requirement_count: int,
    ) -> str:
        if not structured_fields.proposal_due_date or not structured_fields.submission_method:
            return "High"
        if len(document_gaps) >= 5 or requirement_count >= 12:
            return "High"
        if len(document_gaps) >= 3 or len(assumption_flags) >= 3 or requirement_count >= 8:
            return "Medium"
        return "Low to medium"

    def _recommended_next_action(self, structured_fields: RfpStructuredFields, document_gaps: list[str]) -> str:
        if not structured_fields.proposal_due_date or not structured_fields.submission_method:
            return "Confirm the due date, due time, and submission path before moving into buyer-facing drafting."
        if document_gaps:
            return "Proceed with the proposal skeleton, assign section owners, and close the remaining document and staffing gaps in parallel."
        return "Proceed into drafting and tailor the narrative around the evaluation criteria and mandatory requirements."

    def _recommended_materials(
        self,
        *,
        structured_fields: RfpStructuredFields | None,
        requirements: list[Requirement | RequirementRecord],
    ) -> list[str]:
        requirement_text = " ".join(row.requirement_text.lower() for row in requirements)
        recommendations = [
            "Any addenda or amendments released after the original RFP.",
            "Buyer discovery notes, capture notes, and meeting transcripts that explain priorities or evaluator concerns.",
            "Pricing assumptions, staffing plans, and site-specific operating notes from sales or operations.",
            "Approved resumes, references, certifications, and insurance documents that will strengthen the final package.",
        ]
        if structured_fields and structured_fields.questions_due_date:
            recommendations.append("Answers to bidder questions or any clarification responses issued by the buyer.")
        if "reference" in requirement_text or "past performance" in requirement_text:
            recommendations.append("Comparable past-performance references and updated customer contact details.")
        if "resume" in requirement_text or "staffing plan" in requirement_text:
            recommendations.append("Named key personnel, staffing matrices, and supervisory coverage details.")
        if "pricing" in requirement_text or "workbook" in requirement_text:
            recommendations.append("Pricing workbooks, labor assumptions, rate cards, and any site-specific cost drivers.")
        return _unique_strings(recommendations)

    def _latest_package_run_model(self, opportunity_id: str) -> ProposalPackageRun | None:
        stmt = (
            select(ProposalPackageRun)
            .where(ProposalPackageRun.opportunity_id == opportunity_id)
            .order_by(ProposalPackageRun.version.desc(), ProposalPackageRun.created_at.desc())
        )
        return self.db.execute(stmt).scalars().first()

    def _follow_up_actions(
        self,
        *,
        package_run: ProposalPackageRun | None,
        document_gaps: list[str],
        recommended_materials: list[str],
    ) -> list[FollowUpActionArtifact]:
        actions: list[FollowUpActionArtifact] = []
        seen_titles: set[str] = set()

        def add_action(
            title: str,
            description: str,
            action_label: str,
            material_kind: str,
            *,
            input_mode: str,
            suggested_filename: str,
            placeholder_text: str,
        ) -> None:
            if title in seen_titles:
                return
            seen_titles.add(title)
            actions.append(
                FollowUpActionArtifact(
                    title=title,
                    description=description,
                    action_label=action_label,
                    material_kind=material_kind,
                    input_mode=input_mode,
                    suggested_filename=suggested_filename,
                    placeholder_text=placeholder_text,
                )
            )

        raw_items = list(document_gaps[:4]) + list(recommended_materials[:4])
        if package_run is not None:
            raw_items = _ensure_list(_parse_json(package_run.blocking_issues_json, []), *raw_items)

        for item in raw_items:
            lowered = item.lower()
            if any(term in lowered for term in ("addenda", "addendum", "amendment")):
                add_action(
                    "Upload the latest addenda",
                    "Use this when the buyer issues an amendment or addendum so the response refreshes against the newest requirements.",
                    "Add Addendum Files",
                    "addendum",
                    input_mode="files",
                    suggested_filename="latest-addendum.pdf",
                    placeholder_text="Summarize the addendum here only if you do not have the file yet.",
                )
            elif any(term in lowered for term in ("buyer discovery", "capture", "clarification", "buyer note")):
                add_action(
                    "Add buyer or capture notes",
                    "Paste discovery notes, call notes, or clarifications so the proposal can adjust its positioning and emphasis.",
                    "Paste Buyer Notes",
                    "buyer discovery notes",
                    input_mode="text",
                    suggested_filename="buyer-discovery-notes.txt",
                    placeholder_text="Example: Buyer emphasized response time, reporting visibility, and stronger local supervision after the walkthrough.",
                )
            elif any(term in lowered for term in ("transcript", "walkthrough", "meeting")):
                add_action(
                    "Add meeting notes or transcript",
                    "Paste a walkthrough transcript or meeting summary to update requirements, risks, and messaging.",
                    "Paste Transcript",
                    "meeting transcript",
                    input_mode="text",
                    suggested_filename="meeting-transcript.txt",
                    placeholder_text="Paste the meeting notes or transcript here.",
                )
            elif any(term in lowered for term in ("staffing", "shift", "coverage", "pricing input", "pricing assumption", "workbook")):
                add_action(
                    "Add staffing or pricing assumptions",
                    "Provide staffing counts, shifts, coverage windows, or pricing assumptions so the package can improve the management and pricing sections.",
                    "Add Staffing Inputs",
                    "pricing input",
                    input_mode="text",
                    suggested_filename="staffing-and-pricing-inputs.txt",
                    placeholder_text="Example: Main terminal 3 FTE day porters, baggage claim 1 swing porter, day-shift supervisor on site 6am-4pm.",
                )
            elif any(term in lowered for term in ("resume", "reference", "insurance", "certificate", "attachment", "form")):
                add_action(
                    "Upload supporting documents",
                    "Add resumes, references, insurance documents, forms, or other submission attachments for the next package pass.",
                    "Upload Supporting Files",
                    "other supporting material",
                    input_mode="files",
                    suggested_filename="supporting-material.pdf",
                    placeholder_text="Describe what you are adding if the file is not ready yet.",
                )

        if not actions:
            add_action(
                "Upload more source material",
                "Add any new addenda, attachments, or supporting documents that should shape the next package pass.",
                "Upload Files",
                "other supporting material",
                input_mode="files",
                suggested_filename="supporting-material.pdf",
                placeholder_text="Describe the missing document if you only have notes right now.",
            )
            add_action(
                "Paste buyer notes or clarifications",
                "Use notes from calls, discovery, or site visits to keep the response aligned with what you are learning.",
                "Paste Notes",
                "buyer discovery notes",
                input_mode="text",
                suggested_filename="buyer-discovery-notes.txt",
                placeholder_text="Paste buyer notes, capture information, or clarifications here.",
            )

        return actions[:4]

    def _material_filename(self, material_kind: str, raw_text_filename: str | None) -> str:
        preferred = _normalize_space(raw_text_filename)
        if preferred:
            return preferred
        slug = re.sub(r"[^a-z0-9]+", "-", material_kind.lower()).strip("-")
        slug = slug or "supporting-material"
        return f"{slug}.txt"

    def _serialize_run(
        self,
        run: ProposalBuilderRun | None,
        *,
        opportunity: Opportunity | None = None,
        solicitation: Solicitation | None = None,
        requirements: list[Requirement | RequirementRecord] | None = None,
    ) -> ProposalBuilderRunResponse | None:
        if not run:
            return None
        raw_warning_items = _parse_json(run.warnings_json, [])
        warnings, generation_reason = _extract_warning_metadata(raw_warning_items)
        draft_package = DraftPackageArtifact.model_validate(_parse_json(run.draft_package_json, {})) if run.draft_package_json else None
        client_sections = draft_package.client_sections or draft_package.sections if draft_package else []
        internal_notes = draft_package.internal_notes if draft_package else []
        structured_fields = self._structured_fields(solicitation) if solicitation else None
        try:
            proposal_config = self._profile_service().opportunity_config(run.opportunity_id)
        except ClientProfileError:
            proposal_config = None
        document_gaps = self._document_gaps(structured_fields, requirements or []) if structured_fields else []
        assumption_flags = (
            self._assumption_flags(
                opportunity=opportunity,
                solicitation=solicitation,
                structured_fields=structured_fields,
                requirements=requirements or [],
            )
            if opportunity and solicitation
            else []
        )
        return ProposalBuilderRunResponse(
            id=run.id,
            opportunity_id=run.opportunity_id,
            version=run.version,
            source_solicitation_id=run.source_solicitation_id,
            generation_mode=run.generation_mode,
            generation_reason=generation_reason,
            model_name=run.model_name,
            status=run.status,
            proposal_config=proposal_config,
            opportunity_summary=OpportunitySummaryArtifact.model_validate(_parse_json(run.opportunity_summary_json, {})) if run.opportunity_summary_json else None,
            document_gaps=document_gaps,
            assumption_flags=assumption_flags,
            evaluation_criteria=[EvaluationCriterionArtifact.model_validate(item) for item in _parse_json(run.evaluation_criteria_json, [])],
            submission_instructions=[SubmissionInstructionsArtifact.model_validate(item) for item in _parse_json(run.submission_instructions_json, [])],
            win_themes=[WinThemeArtifact.model_validate(item) for item in _parse_json(run.win_themes_json, [])],
            section_drafting_plan=[SectionDraftingPlanArtifact.model_validate(item) for item in _parse_json(run.section_drafting_plan_json, [])],
            draft_package=draft_package,
            client_sections=client_sections,
            internal_notes=internal_notes,
            export_manifest=ExportManifestArtifact.model_validate(_parse_json(run.export_manifest_json, {})) if run.export_manifest_json else None,
            warnings=warnings,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )

    def _build_extract_fallback(
        self,
        *,
        opportunity: Opportunity,
        solicitation: Solicitation,
        structured_fields: RfpStructuredFields,
        requirements: list[Requirement],
    ) -> ExtractStageArtifactResponse:
        evaluation_lines = structured_fields.evaluation_criteria or _split_lines(solicitation.extracted_evaluation_criteria)
        evaluation_criteria = [
            EvaluationCriterionArtifact(criterion=_short_label(line), description=line, source_snippet=line)
            for line in evaluation_lines[:6]
        ]
        instruction_lines = _split_lines(solicitation.extracted_submission_instructions)
        if structured_fields.submission_method:
            instruction_lines = [structured_fields.submission_method] + [line for line in instruction_lines if line != structured_fields.submission_method]
        submission_instructions = [
            SubmissionInstructionsArtifact(
                instruction_type="Submission method" if any(marker in line.lower() for marker in ("portal", "email", "copy", "upload")) else "Submission instruction",
                instruction=line,
                source_snippet=line,
            )
            for line in instruction_lines[:6]
        ]
        document_gaps = self._document_gaps(structured_fields, requirements)
        assumption_flags = self._assumption_flags(
            opportunity=opportunity,
            solicitation=solicitation,
            structured_fields=structured_fields,
            requirements=requirements,
        )
        uncertainty_notes = _ensure_list(assumption_flags)
        geography_text = ", ".join(structured_fields.geography[:3]) if structured_fields.geography else None
        operational_count = len(structured_fields.operational_requirements)
        summary = OpportunitySummaryArtifact(
            client_name=structured_fields.client_name or opportunity.client,
            opportunity_name=structured_fields.opportunity_name or opportunity.name,
            solicitation_number=structured_fields.solicitation_number,
            issue_date=structured_fields.issue_date,
            questions_due_date=structured_fields.questions_due_date,
            proposal_due_date=structured_fields.proposal_due_date,
            proposal_due_time=structured_fields.proposal_due_time,
            contract_term=structured_fields.contract_term,
            site_geography=structured_fields.geography,
            scope_summary=structured_fields.scope_summary,
            submission_method=structured_fields.submission_method,
            strategic_fit=_fit_label(opportunity.strategic_alignment),
            geographic_fit=f"Geography is identified as {geography_text}." if geography_text else "Geography is not explicit yet; confirm site coverage and local leadership assumptions.",
            operational_fit=f"{operational_count} operational requirements were detected, which is enough to start a structured delivery approach." if operational_count else "Operational expectations are still light in the parsed output; validate service assumptions with operations.",
            revenue_scale_signal=_contract_value_signal(solicitation.content_text),
            complexity_level=_complexity_level(structured_fields, len(requirements)),
            risk_level=self._rank_risk(document_gaps=document_gaps, assumption_flags=assumption_flags, structured_fields=structured_fields, requirement_count=len(requirements)),
            recommended_next_action=self._recommended_next_action(structured_fields, document_gaps),
            missing_information=document_gaps,
            uncertainty_notes=uncertainty_notes,
            )
        return ExtractStageArtifactResponse(
            opportunity_summary=summary,
            evaluation_criteria=evaluation_criteria,
            submission_instructions=submission_instructions,
            normalized_requirements=self._fallback_requirement_normalizations(requirements=requirements),
            warnings=[],
        )

    def _fallback_requirement_normalizations(
        self,
        *,
        requirements: list[Requirement],
    ) -> list[ComplianceRequirementNormalizationArtifact]:
        return [
            ComplianceRequirementNormalizationArtifact(
                requirement_code=row.requirement_code,
                normalized_requirement_text=row.requirement_text,
                category=row.category,
                requirement_type=row.requirement_type,
                proposal_section=_requirement_section_name(row),
                source_excerpt=row.requirement_text,
                confidence="baseline",
            )
            for row in requirements
        ]

    def _normalized_requirement_artifacts(
        self,
        *,
        requirements: list[Requirement],
        normalized_items: list[ComplianceRequirementNormalizationArtifact],
    ) -> list[ComplianceRequirementNormalizationArtifact]:
        fallback_by_code = {
            item.requirement_code: item for item in self._fallback_requirement_normalizations(requirements=requirements)
        }
        merged_by_code = dict(fallback_by_code)

        for item in normalized_items:
            code = _normalize_space(item.requirement_code).upper()
            fallback = fallback_by_code.get(code)
            if fallback is None:
                continue
            normalized_text = _normalize_space(item.normalized_requirement_text) or fallback.normalized_requirement_text
            category = _normalize_space(item.category).upper() or fallback.category
            if category not in ALLOWED_REQUIREMENT_CATEGORIES:
                category = fallback.category
            requirement_type = _normalize_space(item.requirement_type).upper() or fallback.requirement_type
            if requirement_type not in ALLOWED_REQUIREMENT_TYPES:
                requirement_type = fallback.requirement_type
            proposal_section = _canonical_section_name(item.proposal_section)
            if proposal_section not in SECTION_OWNER_MAP:
                proposal_section = _canonical_section_name(fallback.proposal_section)
            if proposal_section not in SECTION_OWNER_MAP:
                requirement_row = next((row for row in requirements if row.requirement_code == code), None)
                proposal_section = _requirement_section_name(requirement_row) if requirement_row else fallback.proposal_section
            merged_by_code[code] = ComplianceRequirementNormalizationArtifact(
                requirement_code=code,
                normalized_requirement_text=normalized_text,
                category=category,
                requirement_type=requirement_type,
                proposal_section=proposal_section,
                source_excerpt=_normalize_space(item.source_excerpt) or fallback.source_excerpt,
                confidence=_normalize_space(item.confidence) or fallback.confidence,
            )

        return [merged_by_code[row.requirement_code] for row in requirements if row.requirement_code in merged_by_code]

    def _apply_requirement_normalizations(
        self,
        *,
        opportunity_id: str,
        requirements: list[Requirement],
        normalized_requirements: list[ComplianceRequirementNormalizationArtifact],
        actor: str,
    ) -> None:
        requirements_by_code = {row.requirement_code: row for row in requirements}
        matrix_rows = (
            self.db.query(ComplianceMatrixRow)
            .filter(ComplianceMatrixRow.opportunity_id == opportunity_id)
            .all()
        )
        rows_by_requirement_id = {row.requirement_id: row for row in matrix_rows}
        updated_codes: list[str] = []

        for item in normalized_requirements:
            requirement = requirements_by_code.get(item.requirement_code)
            if requirement is None:
                continue
            requirement.requirement_text = item.normalized_requirement_text
            requirement.category = item.category
            requirement.requirement_type = item.requirement_type

            row = rows_by_requirement_id.get(requirement.id)
            if item.requirement_type == "CONTEXT_ONLY":
                if row is not None:
                    self.db.delete(row)
                    rows_by_requirement_id.pop(requirement.id, None)
                updated_codes.append(item.requirement_code)
                continue

            if row is None:
                row = ComplianceMatrixRow(
                    opportunity_id=opportunity_id,
                    requirement_id=requirement.id,
                    proposal_section=item.proposal_section,
                    owner="UNASSIGNED",
                    status="UNMAPPED",
                )
                self.db.add(row)
                self.db.flush()
                rows_by_requirement_id[requirement.id] = row
            else:
                if row.status == "UNMAPPED" or row.owner == "UNASSIGNED":
                    row.proposal_section = item.proposal_section
                if not row.owner:
                    row.owner = "UNASSIGNED"
            updated_codes.append(item.requirement_code)

        self.db.flush()
        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=actor,
            action="proposal_builder_compliance_normalized",
            after_state_json=json.dumps(
                {
                    "updated_requirement_count": len(updated_codes),
                    "context_only_codes": [
                        item.requirement_code
                        for item in normalized_requirements
                        if item.requirement_type == "CONTEXT_ONLY"
                    ],
                }
            ),
        )

    def _extract_prompt_payload(
        self,
        *,
        opportunity: Opportunity,
        solicitation: Solicitation,
        structured_fields: RfpStructuredFields,
        requirements: list[Requirement],
        baseline: ExtractStageArtifactResponse,
    ) -> dict[str, Any]:
        return {
            "workflow_goal": "Produce a grounded opportunity summary, evaluation criteria list, and submission instructions list.",
            "rules": [
                "Only use facts that are present in the RFP payload or the baseline deterministic extraction.",
                "Do not invent dates, weights, incumbent facts, or contract values.",
                "If something is uncertain, say so in uncertainty_notes or warnings.",
                "For normalized_requirements, only use requirement_code values from the provided list.",
                "Keep each normalized requirement atomic and buyer-responsive. Reclassify to CONTEXT_ONLY only when the line is not truly actionable.",
            ],
            "opportunity": {
                "name": opportunity.name,
                "client": opportunity.client,
                "lead_time_days": opportunity.lead_time_days,
                "strategic_alignment": opportunity.strategic_alignment,
                "estimated_probability_win": opportunity.estimated_probability_win,
            },
            "allowed_requirement_categories": sorted(ALLOWED_REQUIREMENT_CATEGORIES),
            "allowed_requirement_types": sorted(ALLOWED_REQUIREMENT_TYPES),
            "allowed_proposal_sections": list(SECTION_OWNER_MAP.keys()),
            "structured_fields": structured_fields.model_dump(),
            "baseline": baseline.model_dump(),
            "requirements": [
                {
                    "requirement_code": row.requirement_code,
                    "category": row.category,
                    "requirement_type": row.requirement_type,
                    "mandatory": row.mandatory,
                    "requirement_text": row.requirement_text,
                    "deterministic_proposal_section": _requirement_section_name(row),
                }
                for row in requirements[:30]
            ],
            "source_excerpt": solicitation.content_text[:18000],
        }

    def _extract_prompt(self) -> str:
        return (
            "You are preparing a staged proposal-building workflow for a facilities-management and janitorial sales team. "
            "Return only the requested JSON schema. Use only facts grounded in the provided RFP payload. "
            "Opportunity summary fields should be concise, business-readable, and explicit about uncertainty. "
            "If the source excerpt states key dates or submission details and the baseline extraction is blank, repair those missing fields in the opportunity summary. "
            "Also normalize the provided deterministic requirement list into cleaner, proposal-ready compliance rows. "
            "Do not invent new requirement codes, and do not add requirements that are not grounded in the source excerpt."
        )

    def run_extract_stage(self, opportunity_id: str, *, actor: str = "operator") -> ProposalBuilderRunResponse:
        opportunity = self.db.get(Opportunity, opportunity_id)
        solicitation = self._latest_solicitation(opportunity_id)
        if not opportunity or not solicitation:
            raise ProposalBuilderError("An opportunity and parsed solicitation are required before extraction.")
        structured_fields = self._structured_fields(solicitation) or RfpStructuredFields()
        requirements = self._latest_requirements(solicitation.id)
        baseline = self._build_extract_fallback(
            opportunity=opportunity,
            solicitation=solicitation,
            structured_fields=structured_fields,
            requirements=requirements,
        )

        generation_mode = "PENDING"
        generation_reason = None
        model_name = None
        warnings = list(baseline.warnings)
        artifact = baseline
        is_demo_sample = self._is_demo_sample_solicitation(solicitation)
        client = self._openai_client(
            stage_name="extract",
            source_text_length=len(solicitation.content_text),
            requirement_count=len(requirements),
        )
        cached_demo = (
            self._cached_demo_artifact("extract", ExtractStageArtifactResponse)
            if is_demo_sample and BOSSKEY_PROPOSAL_BUILDER_ALLOW_CACHED_DEMO_FALLBACK
            else None
        )
        if not client.available:
            if cached_demo is not None:
                artifact = cached_demo
                generation_mode = "FALLBACK_SAMPLE"
                generation_reason = "missing_api_key"
                warnings.append("Using the cached demo extraction because a live OpenAI key is not configured.")
            else:
                message = self._live_stage_error_message(
                    stage_label="Requirements extraction",
                    timeout_seconds=client.timeout_seconds,
                    exc=OpenAIStructuredOutputError("OPENAI_API_KEY is not configured."),
                )
                self._record_stage_failure(
                    opportunity_id=opportunity_id,
                    solicitation_id=solicitation.id,
                    stage_name="extract",
                    actor=actor,
                    generation_reason="missing_api_key",
                    message=message,
                    model_name=None,
                )
                raise ProposalBuilderError(message)
        else:
            try:
                guardrails = self._stage_ai_guardrails(
                    stage_name="extract",
                    source_text_length=len(solicitation.content_text),
                    requirement_count=len(requirements),
                )
                parsed = client.generate_json(
                    system_prompt=self._extract_prompt(),
                    user_payload=self._extract_prompt_payload(
                        opportunity=opportunity,
                        solicitation=solicitation,
                        structured_fields=structured_fields,
                        requirements=requirements,
                        baseline=baseline,
                    ),
                    schema_name="proposal_builder_extract_stage",
                    schema=ExtractStageArtifactResponse.model_json_schema(),
                    max_output_tokens=guardrails["max_output_tokens"],
                    max_estimated_input_tokens=guardrails["max_estimated_input_tokens"],
                    guardrail_label="extract",
                )
                artifact = ExtractStageArtifactResponse.model_validate(parsed)
                generation_mode = "LIVE"
                generation_reason = "live_model"
                model_name = client.model
            except (OpenAIStructuredOutputError, ValueError) as exc:
                generation_reason = _generation_reason_from_exception(exc)
                if cached_demo is not None and BOSSKEY_PROPOSAL_BUILDER_ALLOW_LIVE_STAGE_FALLBACK:
                    artifact = cached_demo
                    generation_mode = "FALLBACK_SAMPLE"
                    warnings.append("Loaded the cached demo extraction artifact after the live extraction step failed.")
                else:
                    artifact = baseline.model_copy(deep=True)
                    generation_mode = "FALLBACK_BASELINE"
                    warnings.append(
                        "The live extraction refinement step did not return usable structured output, "
                        "so the app kept the deterministic RFP extraction and continued."
                    )

        normalized_requirements = self._normalized_requirement_artifacts(
            requirements=requirements,
            normalized_items=artifact.normalized_requirements,
        )
        artifact.normalized_requirements = normalized_requirements
        self._apply_requirement_normalizations(
            opportunity_id=opportunity_id,
            requirements=requirements,
            normalized_requirements=normalized_requirements,
            actor=actor,
        )
        structured_fields = self._repair_structured_fields_from_extract(
            solicitation=solicitation,
            structured_fields=structured_fields,
            artifact=artifact,
        )
        self.db.flush()
        requirements = self._latest_requirements(solicitation.id)

        document_gaps = self._document_gaps(structured_fields, requirements)
        assumption_flags = self._assumption_flags(
            opportunity=opportunity,
            solicitation=solicitation,
            structured_fields=structured_fields,
            requirements=requirements,
        )
        artifact.opportunity_summary.revenue_scale_signal = _contract_value_signal(solicitation.content_text)
        artifact.opportunity_summary.missing_information = document_gaps
        artifact.opportunity_summary.uncertainty_notes = _ensure_list(
            artifact.opportunity_summary.uncertainty_notes,
            *assumption_flags,
        )
        artifact.opportunity_summary.risk_level = self._rank_risk(
            document_gaps=document_gaps,
            assumption_flags=assumption_flags,
            structured_fields=structured_fields,
            requirement_count=len(requirements),
        )
        artifact.opportunity_summary.recommended_next_action = self._recommended_next_action(structured_fields, document_gaps)

        run = self._ensure_run(opportunity_id, solicitation.id)
        run.generation_mode = generation_mode
        run.model_name = model_name
        run.status = "REQUIREMENTS_READY"
        run.opportunity_summary_json = json.dumps(artifact.opportunity_summary.model_dump())
        run.evaluation_criteria_json = json.dumps([item.model_dump() for item in artifact.evaluation_criteria])
        run.submission_instructions_json = json.dumps([item.model_dump() for item in artifact.submission_instructions])
        run.warnings_json = _pack_warning_payload(_parse_json(run.warnings_json, []), warnings, generation_reason)
        self.db.flush()

        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=actor,
            action="proposal_builder_extract_completed",
            after_state_json=json.dumps(
                {
                    "generation_mode": generation_mode,
                    "model_name": model_name,
                    "normalized_requirement_count": len(normalized_requirements),
                    "evaluation_criteria_count": len(artifact.evaluation_criteria),
                    "submission_instruction_count": len(artifact.submission_instructions),
                }
            ),
        )
        self.db.commit()
        self.db.refresh(run)
        return self._serialize_run(run, opportunity=opportunity, solicitation=solicitation, requirements=requirements)

    def _build_drafting_plan(
        self,
        *,
        sections: list[ProposalOutlineSectionArtifact],
        requirements_by_code: dict[str, Requirement],
    ) -> list[SectionDraftingPlanArtifact]:
        drafting_plan: list[SectionDraftingPlanArtifact] = []
        for section in sections:
            requirement_texts = [
                requirements_by_code[code].requirement_text
                for code in section.requirement_codes
                if code in requirements_by_code
            ]
            candidate_blocks = select_candidate_blocks(section_name=section.proposal_section, requirement_texts=requirement_texts)
            drafting_plan.append(
                SectionDraftingPlanArtifact(
                    proposal_section=section.proposal_section,
                    owner_role=section.owner_role,
                    objective=section.section_purpose,
                    source_requirement_codes=section.requirement_codes,
                    candidate_content_block_ids=[block.id for block in candidate_blocks],
                    notes=[
                        "Tie narrative claims directly to the solicitation requirements and evaluation criteria.",
                        "Use approved content blocks where they strengthen the section without overstating unsupported facts.",
                    ],
                )
            )
        return drafting_plan

    def _fallback_outline_artifacts(self, *, requirements: list[Requirement]) -> SkeletonStageArtifactResponse:
        requirements_by_section: dict[str, list[Requirement]] = {name: [] for name, _owner, _purpose in SECTION_BLUEPRINT}
        for row in requirements:
            section_name = _requirement_section_name(row)
            requirements_by_section.setdefault(section_name, []).append(row)

        sections = [
            ProposalOutlineSectionArtifact(
                sequence=index,
                proposal_section=name,
                owner_role=owner_role,
                section_purpose=purpose,
                requirement_codes=[row.requirement_code for row in requirements_by_section.get(name, [])],
            )
            for index, (name, owner_role, purpose) in enumerate(SECTION_BLUEPRINT, start=1)
        ]

        technical_codes = [row.requirement_code for row in requirements_by_section.get("Technical Approach", [])[:3]]
        staffing_codes = [row.requirement_code for row in requirements_by_section.get("Management and Staffing Plan", [])[:3]]
        transition_codes = [row.requirement_code for row in requirements_by_section.get("Transition and Mobilization Plan", [])[:3]]
        compliance_codes = [row.requirement_code for row in requirements_by_section.get("Compliance and Attachments", [])[:3]]
        past_performance_codes = [row.requirement_code for row in requirements_by_section.get("Past Performance", [])[:3]]
        win_themes = [
            WinThemeArtifact(
                title="Reliable Service Continuity",
                rationale="Lead with disciplined operations, visible supervision, and consistent site-level service controls.",
                supporting_requirement_codes=_unique_strings(technical_codes + staffing_codes[:1]),
            ),
            WinThemeArtifact(
                title="Low-Risk Mobilization",
                rationale="Show a controlled startup plan, quick-turn onboarding steps, and early performance checkpoints.",
                supporting_requirement_codes=_unique_strings(transition_codes + technical_codes[:1]),
            ),
            WinThemeArtifact(
                title="Scorable Compliance Package",
                rationale="Make the submission easy to evaluate by clearly tying forms, insurance, and required attachments back to the solicitation.",
                supporting_requirement_codes=_unique_strings(compliance_codes),
            ),
            WinThemeArtifact(
                title="Relevant Multi-Site Experience",
                rationale="Use comparable facilities or transportation experience to reinforce execution confidence and buyer fit.",
                supporting_requirement_codes=_unique_strings(past_performance_codes),
            ),
        ]
        drafting_plan = self._build_drafting_plan(
            sections=sections,
            requirements_by_code={row.requirement_code: row for row in requirements},
        )
        return SkeletonStageArtifactResponse(proposal_outline=sections, win_themes=win_themes, section_drafting_plan=drafting_plan, warnings=[])

    def _skeleton_prompt(self) -> str:
        return (
            "You are building a staged proposal skeleton for a facilities-management and janitorial proposal team. "
            "Return only JSON that defines the proposal outline, win themes, and section drafting plan. "
            "Use only requirement codes that appear in the provided requirements list. "
            "Use owner roles from this set only: Proposal Lead, Operations Lead, Pricing/Finance, SME. "
            "Prefer this section taxonomy: Executive Summary, Technical Approach, Management and Staffing Plan, Transition and Mobilization Plan, Past Performance, Pricing and Commercials, Compliance and Attachments."
        )

    def _skeleton_prompt_payload(
        self,
        *,
        opportunity: Opportunity,
        solicitation: Solicitation,
        structured_fields: RfpStructuredFields,
        requirements: list[Requirement],
        compliance_rows: list[dict[str, Any]],
        current_run: ProposalBuilderRunResponse,
    ) -> dict[str, Any]:
        serialized_compliance_rows = [
            {
                "requirement_code": row["requirement_code"] if isinstance(row, dict) else row.requirement_code,
                "requirement_text": row["requirement_text"] if isinstance(row, dict) else row.requirement_text,
                "requirement_type": row["requirement_type"] if isinstance(row, dict) else row.requirement_type,
                "proposal_section": row["proposal_section"] if isinstance(row, dict) else row.proposal_section,
                "owner": row["owner"] if isinstance(row, dict) else row.owner,
                "status": row["status"] if isinstance(row, dict) else row.status,
            }
            for row in compliance_rows
        ]
        return {
            "workflow_goal": "Create a proposal skeleton grounded in the current RFP.",
            "opportunity": {"name": opportunity.name, "client": opportunity.client},
            "structured_fields": structured_fields.model_dump(),
            "opportunity_summary": current_run.opportunity_summary.model_dump() if current_run.opportunity_summary else {},
            "evaluation_criteria": [item.model_dump() for item in current_run.evaluation_criteria],
            "preferred_section_taxonomy": [name for name, _owner, _purpose in SECTION_BLUEPRINT],
            "requirements": [
                {
                    "requirement_code": row.requirement_code,
                    "category": row.category,
                    "requirement_type": row.requirement_type,
                    "requirement_text": row.requirement_text,
                }
                for row in requirements[:40]
            ],
            "current_compliance_matrix": serialized_compliance_rows,
            "content_block_inventory": content_block_inventory()[:30],
            "source_excerpt": solicitation.content_text[:12000],
        }

    def _normalize_skeleton_artifact(
        self,
        *,
        artifact: SkeletonStageArtifactResponse,
        fallback: SkeletonStageArtifactResponse,
        requirements_by_code: dict[str, Requirement],
    ) -> SkeletonStageArtifactResponse:
        def valid_outline_codes(codes: list[str]) -> list[str]:
            return _unique_strings(
                [
                    code
                    for code in codes
                    if code in requirements_by_code
                    and requirements_by_code[code].requirement_type != "CONTEXT_ONLY"
                ]
            )

        normalized_sections: list[ProposalOutlineSectionArtifact] = []
        seen_sections: set[str] = set()
        for section in artifact.proposal_outline:
            canonical_name = _canonical_section_name(section.proposal_section)
            if canonical_name in seen_sections:
                continue
            valid_codes = valid_outline_codes(section.requirement_codes)
            normalized_sections.append(
                ProposalOutlineSectionArtifact(
                    sequence=len(normalized_sections) + 1,
                    proposal_section=canonical_name,
                    owner_role=section.owner_role if section.owner_role in OWNER_ROLE_ORDER else _owner_for_section(canonical_name),
                    section_purpose=section.section_purpose or _purpose_for_section(canonical_name),
                    requirement_codes=valid_codes,
                )
            )
            seen_sections.add(canonical_name)

        fallback_by_name = {section.proposal_section: section for section in fallback.proposal_outline}
        for section_name, owner_role, purpose in SECTION_BLUEPRINT:
            if section_name in seen_sections:
                continue
            fallback_section = fallback_by_name[section_name]
            normalized_sections.append(
                ProposalOutlineSectionArtifact(
                    sequence=len(normalized_sections) + 1,
                    proposal_section=section_name,
                    owner_role=owner_role,
                    section_purpose=purpose,
                    requirement_codes=valid_outline_codes(fallback_section.requirement_codes),
                )
            )

        drafting_plan = self._build_drafting_plan(sections=normalized_sections, requirements_by_code=requirements_by_code)
        win_themes = artifact.win_themes or fallback.win_themes
        return SkeletonStageArtifactResponse(
            proposal_outline=normalized_sections,
            win_themes=win_themes,
            section_drafting_plan=drafting_plan,
            warnings=_unique_strings(artifact.warnings + fallback.warnings),
        )

    def _apply_outline_mapping(
        self,
        *,
        opportunity_id: str,
        sections: list[ProposalOutlineSectionArtifact],
        requirements_by_code: dict[str, Requirement],
        actor: str,
    ) -> None:
        mapped_codes: set[str] = set()
        for section in sections:
            for code in section.requirement_codes:
                requirement = requirements_by_code.get(code)
                if not requirement:
                    continue
                mapped_codes.add(code)
                row = (
                    self.db.query(ComplianceMatrixRow)
                    .filter(ComplianceMatrixRow.opportunity_id == opportunity_id)
                    .filter(ComplianceMatrixRow.requirement_id == requirement.id)
                    .first()
                )
                if not row:
                    continue
                row.proposal_section = section.proposal_section
                row.owner = section.owner_role
                if row.status == "UNMAPPED":
                    row.status = "IN_PROGRESS"

        for code, requirement in requirements_by_code.items():
            row = (
                self.db.query(ComplianceMatrixRow)
                .filter(ComplianceMatrixRow.opportunity_id == opportunity_id)
                .filter(ComplianceMatrixRow.requirement_id == requirement.id)
                .first()
            )
            if not row:
                continue
            if row.status != "UNMAPPED" and row.owner != "UNASSIGNED":
                continue
            section_name = _requirement_section_name(requirement)
            row.proposal_section = section_name
            row.owner = _owner_for_section(section_name)
            if row.status == "UNMAPPED":
                row.status = "IN_PROGRESS"
            mapped_codes.add(code)

        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=actor,
            action="proposal_builder_compliance_mapping_applied",
            after_state_json=json.dumps(
                {
                    "mapped_requirement_count": len(mapped_codes),
                    "proposal_sections": [section.proposal_section for section in sections],
                }
            ),
        )

    def _update_workflow_summary(
        self,
        opportunity_id: str,
        *,
        compliance_status: str | None = None,
        pricing_status: str | None = None,
        review_gate_status: str | None = None,
        submission_milestone: str | None = None,
        section_owners: list[ProposalOutlineSectionArtifact] | None = None,
    ) -> ProposalWorkflowSummary:
        summary = self.db.query(ProposalWorkflowSummary).filter(ProposalWorkflowSummary.opportunity_id == opportunity_id).first()
        if summary is None:
            summary = ProposalWorkflowSummary(opportunity_id=opportunity_id)
            self.db.add(summary)
            self.db.flush()
        if compliance_status:
            summary.compliance_status = compliance_status
        if pricing_status:
            summary.pricing_status = pricing_status
        if review_gate_status:
            summary.review_gate_status = review_gate_status
        if submission_milestone:
            summary.submission_milestone = submission_milestone
        if section_owners is not None:
            summary.sme_assignments_json = json.dumps(
                [
                    {"role": section.owner_role, "owner_name": "", "proposal_section": section.proposal_section}
                    for section in section_owners
                ]
            )
        self.db.flush()
        return summary

    def run_skeleton_stage(self, opportunity_id: str, *, actor: str = "operator") -> ProposalBuilderRunResponse:
        opportunity = self.db.get(Opportunity, opportunity_id)
        solicitation = self._latest_solicitation(opportunity_id)
        if not opportunity or not solicitation:
            raise ProposalBuilderError("An opportunity and parsed solicitation are required before skeleton generation.")
        current_run = self._latest_run(opportunity_id)
        if current_run is None or not current_run.opportunity_summary_json:
            self.run_extract_stage(opportunity_id, actor=actor)
        requirements = self._latest_requirements(solicitation.id)
        current_run_response = self._serialize_run(
            self._latest_run(opportunity_id),
            opportunity=opportunity,
            solicitation=solicitation,
            requirements=requirements,
        )
        assert current_run_response is not None
        requirements_by_code = {row.requirement_code: row for row in requirements}
        structured_fields = self._structured_fields(solicitation) or RfpStructuredFields()
        compliance_rows = ComplianceMatrixService(self.db).list_rows(opportunity_id, include_context=True)
        fallback = self._fallback_outline_artifacts(requirements=requirements)
        warnings = list(fallback.warnings)
        artifact = fallback
        generation_mode = "PENDING"
        generation_reason = None
        model_name = None

        is_demo_sample = self._is_demo_sample_solicitation(solicitation)
        client = self._openai_client(
            stage_name="skeleton",
            source_text_length=len(solicitation.content_text),
            requirement_count=len(requirements),
        )
        cached_demo = (
            self._cached_demo_artifact("skeleton", SkeletonStageArtifactResponse)
            if is_demo_sample and BOSSKEY_PROPOSAL_BUILDER_ALLOW_CACHED_DEMO_FALLBACK
            else None
        )
        if not client.available:
            if cached_demo is not None:
                artifact = cached_demo
                generation_mode = "FALLBACK_SAMPLE"
                generation_reason = "missing_api_key"
                warnings.append("Using the cached demo proposal skeleton because a live OpenAI key is not configured.")
            else:
                message = self._live_stage_error_message(
                    stage_label="Proposal skeleton generation",
                    timeout_seconds=client.timeout_seconds,
                    exc=OpenAIStructuredOutputError("OPENAI_API_KEY is not configured."),
                )
                self._record_stage_failure(
                    opportunity_id=opportunity_id,
                    solicitation_id=solicitation.id,
                    stage_name="skeleton",
                    actor=actor,
                    generation_reason="missing_api_key",
                    message=message,
                    model_name=None,
                )
                raise ProposalBuilderError(message)
        else:
            try:
                guardrails = self._stage_ai_guardrails(
                    stage_name="skeleton",
                    source_text_length=len(solicitation.content_text),
                    requirement_count=len(requirements),
                )
                parsed = client.generate_json(
                    system_prompt=self._skeleton_prompt(),
                    user_payload=self._skeleton_prompt_payload(
                        opportunity=opportunity,
                        solicitation=solicitation,
                        structured_fields=structured_fields,
                        requirements=requirements,
                        compliance_rows=compliance_rows,
                        current_run=current_run_response,
                    ),
                    schema_name="proposal_builder_skeleton_stage",
                    schema=SkeletonStageArtifactResponse.model_json_schema(),
                    max_output_tokens=guardrails["max_output_tokens"],
                    max_estimated_input_tokens=guardrails["max_estimated_input_tokens"],
                    guardrail_label="skeleton",
                )
                artifact = SkeletonStageArtifactResponse.model_validate(parsed)
                generation_mode = "LIVE"
                generation_reason = "live_model"
                model_name = client.model
            except (OpenAIStructuredOutputError, ValueError) as exc:
                generation_reason = _generation_reason_from_exception(exc)
                if cached_demo is not None and BOSSKEY_PROPOSAL_BUILDER_ALLOW_LIVE_STAGE_FALLBACK:
                    artifact = cached_demo
                    generation_mode = "FALLBACK_SAMPLE"
                    warnings.append("Loaded the cached demo proposal skeleton artifact after the live stage failed.")
                else:
                    message = self._live_stage_error_message(
                        stage_label="Proposal skeleton generation",
                        timeout_seconds=client.timeout_seconds,
                        exc=exc,
                    )
                    self._record_stage_failure(
                        opportunity_id=opportunity_id,
                        solicitation_id=solicitation.id,
                        stage_name="skeleton",
                        actor=actor,
                        generation_reason=generation_reason,
                        message=message,
                        model_name=client.model,
                    )
                    raise ProposalBuilderError(message)

        artifact = self._normalize_skeleton_artifact(
            artifact=artifact,
            fallback=fallback,
            requirements_by_code=requirements_by_code,
        )
        artifact = SkeletonStageArtifactResponse(
            proposal_outline=artifact.proposal_outline,
            win_themes=artifact.win_themes,
            section_drafting_plan=artifact.section_drafting_plan,
            warnings=_unique_strings(artifact.warnings + warnings),
        )

        outline_service = ProposalOutlineService(self.db)
        outline = outline_service.create_manual_version(
            opportunity_id,
            ProposalOutlineManualCreateRequest(
                actor=actor,
                sections=[
                    ProposalOutlineManualSectionInput(
                        sequence=section.sequence,
                        proposal_section=section.proposal_section,
                        owner=section.owner_role,
                        requirement_ids=[requirements_by_code[code].id for code in section.requirement_codes if code in requirements_by_code],
                    )
                    for section in artifact.proposal_outline
                ],
            ),
        )
        self._apply_outline_mapping(opportunity_id=opportunity_id, sections=artifact.proposal_outline, requirements_by_code=requirements_by_code, actor=actor)

        run = self._ensure_run(opportunity_id, solicitation.id)
        run.generation_mode = generation_mode
        run.model_name = model_name
        run.status = "SKELETON_READY"
        run.win_themes_json = json.dumps([item.model_dump() for item in artifact.win_themes])
        run.section_drafting_plan_json = json.dumps([item.model_dump() for item in artifact.section_drafting_plan])
        run.warnings_json = _pack_warning_payload(_parse_json(run.warnings_json, []), artifact.warnings, generation_reason)
        self._update_workflow_summary(
            opportunity_id,
            compliance_status="IN_PROGRESS",
            pricing_status="NOT_STARTED",
            review_gate_status="NOT_STARTED",
            submission_milestone="Proposal skeleton and compliance mapping ready",
            section_owners=artifact.proposal_outline,
        )
        self.db.flush()
        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=actor,
            action="proposal_builder_skeleton_completed",
            after_state_json=json.dumps(
                {
                    "generation_mode": generation_mode,
                    "model_name": model_name,
                    "outline_id": outline.id,
                    "outline_version": outline.version,
                    "win_theme_count": len(artifact.win_themes),
                }
            ),
        )
        self.db.commit()
        self.db.refresh(run)
        return self._serialize_run(run, opportunity=opportunity, solicitation=solicitation, requirements=requirements)

    def _fallback_draft_package(self, *, workspace: ProposalBuilderWorkspaceResponse) -> DraftStageArtifactResponse:
        summary = workspace.opportunity_summary
        if summary is None:
            raise ProposalBuilderError("Opportunity summary is required before drafting.")
        section_requirements: dict[str, list[RequirementRecord]] = {name: [] for name, _owner, _purpose in SECTION_BLUEPRINT}
        for requirement in workspace.requirements_list:
            section_requirements.setdefault(_requirement_section_name(requirement), []).append(requirement)

        theme_titles = [theme.title for theme in workspace.win_themes[:3]]
        criteria_titles = [criterion.criterion for criterion in workspace.evaluation_criteria[:4]]
        geography_text = ", ".join(summary.site_geography[:3]) if summary.site_geography else "the identified service locations"
        scope_text = summary.scope_summary or "routine janitorial services, day porter coverage, incident-response support, and day-to-day facility presentation work."
        provider_name = (
            workspace.proposal_config.client_profile_name
            if workspace.proposal_config and workspace.proposal_config.client_profile_name
            else "the contractor"
        )
        buyer_name = summary.client_name or workspace.client_name
        due_label = " ".join(
            part
            for part in [summary.proposal_due_date or workspace.extracted_deadline or "", summary.proposal_due_time or ""]
            if part
        ).strip() or "the stated due date"
        commercial_gaps = [
            gap
            for gap in workspace.document_gaps
            if any(term in gap.lower() for term in ("pricing", "workbook", "attachment", "insurance", "resume", "reference"))
        ]

        def build_section(section_title: str, body_markdown: str) -> DraftSectionArtifact:
            requirement_rows = section_requirements.get(section_title, [])
            blocks = select_candidate_blocks(
                section_name=section_title,
                requirement_texts=[row.requirement_text for row in requirement_rows][:8],
                limit=3,
            )
            return DraftSectionArtifact(
                section_title=section_title,
                body_markdown=_buyer_facing_text(body_markdown),
                used_content_block_ids=[block.id for block in blocks],
                cited_requirement_codes=[row.requirement_code for row in requirement_rows[:8]],
            )

        transmittal_text = (
            f"{provider_name} respectfully submits this proposal for {workspace.opportunity_name} on behalf of {buyer_name}. "
            "This response is structured around the stated scope, the site-specific operational requirements for PPG Place and 625 Liberty Avenue, and the submission instructions provided through the RFP package and bidder questions.\n\n"
            f"The proposal is prepared for electronic submission through Prism by {due_label}. "
            "It is intended to demonstrate a disciplined operating approach, readiness to mobilize within the required window, and a clear path to finalizing pricing, forms, and attachments once the remaining bid files are supplied."
        )
        executive_text = (
            f"{buyer_name} is seeking a dependable security partner for {workspace.opportunity_name}. "
            f"{provider_name} is positioned around disciplined 24/7/365 service execution across {geography_text}, with emphasis on access control, visible patrol presence, incident reporting, building-system awareness, and responsive tenant-facing service.\n\n"
            f"The response is aligned to {', '.join(criteria_titles) if criteria_titles else 'the stated evaluation criteria and mandatory requirements'}, "
            f"while reinforcing differentiators such as {', '.join(theme_titles) if theme_titles else 'reliable service continuity, low-risk mobilization, and clear compliance discipline'}. "
            "The narrative is intentionally buyer-facing and executive-readable so it can move quickly into final pricing, attachments, and portal-ready packaging."
        )
        technical_text = (
            "### Service Delivery Model\n"
            f"{provider_name} will structure service delivery around the RFP scope, including access control, visitor management, roving patrols, dispatch and incident response, building-system awareness, reporting, and post-order execution across the PPG Place and 625 Liberty portfolios. {scope_text}\n\n"
            "### Site-Specific Operations\n"
            "- Maintain controlled access, visitor processing, and non-business-hours security discipline in line with building rules and tenant expectations.\n"
            "- Perform interior and exterior patrols, checkpoint coverage, daily reporting, and issue escalation with direct coordination to Property Management.\n"
            "- Support PPG Place shuttle operations, property tours, alarm and life-safety coordination, and other duties described in the scope.\n\n"
            "### Reporting and Control\n"
            "- Provide daily reports, incident documentation, inspection support, and other requested management reporting.\n"
            "- Implement tour tracking, communications equipment, and field supervision sufficient to maintain accountability across both properties."
        )
        management_text = (
            "### Management Structure\n"
            f"- {provider_name} will assign accountable management leadership, site supervision, and field oversight for both separately contracted properties under a unified operating approach.\n"
            "- The management structure will provide clear property-management interfaces, escalation paths, and supervisory coverage for all shifts.\n\n"
            "### Staffing Plan Approach\n"
            "- The final staffing submission will be built against the current staffing levels required for comparative evaluation and will address relief, holiday, vacation, and call-off coverage.\n"
            "- Manager and supervisor costs will be reflected in the commercial response consistent with the bidder questions and pricing instructions.\n\n"
            "### Personnel Inputs Still Needed\n"
            "- Final named transition personnel, resumes, and any site-specific organizational chart details should be inserted before submission."
        )
        transition_text = (
            "### Mobilization Priorities\n"
            "- Use a controlled transition sequence that confirms scope, property-specific protocols, post orders, reporting expectations, and startup responsibilities.\n"
            "- Commence service within the required 30-day window and provide the formal transition plan with tasks, time frames, and assigned transition personnel.\n\n"
            "### Early Performance Controls\n"
            "- Within 14 days of award, assess tour points for each property and implement the approved checkpoint approach.\n"
            "- Within 30 days of award, deliver procedures manuals with post orders and emergency procedures for each property.\n"
            "- Launch with clear inspection routines, issue escalation paths, and service accountability from day one."
        )
        past_performance_text = (
            "### Relevant Experience Positioning\n"
            f"{provider_name} will present comparable commercial security experience and role-relevant leadership credentials in the final submission package. "
            "For this first draft, the section is intentionally framed around the buyer's evaluation priorities without inventing unsupported customer names or contract statistics.\n\n"
            "### Planned Final Inserts\n"
            "- Comparable references for downtown commercial office, mixed-use, or similarly complex security environments.\n"
            "- Resume or biography inserts for key contract leadership and transition personnel.\n"
            "- Proof points tied to service continuity, reporting discipline, tenant-facing professionalism, and emergency-response readiness."
        )
        pricing_text = (
            "### Pricing Basis\n"
            "The commercial response will be built on the current union economics and current staffing levels required for comparative evaluation, consistent with the RFP and the consolidated bidder questions. "
            "Holiday premium and overtime assumptions will be addressed in burden or other approved pricing structures as instructed by the owner team.\n\n"
            "### Current Gap Affecting Numeric Pricing\n"
            "- The referenced staffing and pricing workbook was not included in the source package provided for this draft, so final numeric pricing and staffing schedules remain pending source-file completion.\n"
            "- Non-union supervisor and manager wage details were noted as forthcoming in the bidder questions and should be reconciled before final pricing submission.\n\n"
            "### Commercial Submission Intent\n"
            "- The final commercial package should include the required workbook, any approved alternate staffing scenario, and any additional-expense explanations required by the forms."
        )
        compliance_text = (
            "### Required Attachments and Compliance Items\n"
            "- Confirm acceptance of the Highwoods standard service agreement, including the non-negotiable insurance and indemnification sections.\n"
            "- Provide vendor qualification information, W-9, certificates of insurance, and any other required administrative forms.\n"
            "- Acknowledge Exhibit C rules and regulations and align operating procedures accordingly.\n\n"
            "### Items Pending Completion\n"
            + "\n".join(f"- {item}" for item in (commercial_gaps or [
                "Complete the pricing workbook and supporting staffing schedules once the owner-issued spreadsheet is available.",
                "Populate vendor qualification, W-9, insurance certificate, and any other required submission forms.",
                "Insert approved references, resumes, and named transition contacts before final submission.",
            ]))
        )
        client_sections = [
            build_section("Transmittal Letter", transmittal_text),
            build_section("Executive Summary", executive_text),
            build_section("Technical Approach", technical_text),
            build_section("Management and Staffing Plan", management_text),
            build_section("Transition and Mobilization Plan", transition_text),
            build_section("Past Performance", past_performance_text),
            build_section("Pricing and Commercials", pricing_text),
            build_section("Compliance and Attachments", compliance_text),
        ]
        unresolved_items = _ensure_list(
            workspace.document_gaps,
            "Complete pricing inputs and confirm final commercial assumptions.",
            "Finalize the owner-issued staffing and pricing workbook before submission.",
        )
        internal_notes = _ensure_list(
            workspace.assumption_flags,
            "Insert approved St. Moritz local office details, leadership names, and escalation contacts from approved source material.",
            "Populate references, resumes, insurance certificates, vendor qualification content, W-9 details, and completed attachments before final submission.",
        )
        used_content_block_ids = _unique_strings([block_id for section in client_sections for block_id in section.used_content_block_ids])
        cited_requirement_codes = _unique_strings([code for section in client_sections for code in section.cited_requirement_codes])
        return DraftStageArtifactResponse(
            draft_package=DraftPackageArtifact(
                sections=client_sections,
                client_sections=client_sections,
                internal_notes=internal_notes,
                unresolved_items=unresolved_items,
                editor_notes="Use the support bundle and HTML preview to finish pricing, references, resumes, forms, and final St. Moritz-specific formatting before submission.",
                used_content_block_ids=used_content_block_ids,
                cited_requirement_codes=cited_requirement_codes,
            ),
            warnings=[],
        )

    def _draft_prompt(self) -> str:
        return (
            "You are generating a first-pass proposal draft for a commercial security-services proposal team. "
            "Return only JSON. Draft these client-facing sections: Transmittal Letter, Executive Summary, Technical Approach, Management and Staffing Plan, Transition and Mobilization Plan, Past Performance, Pricing and Commercials, and Compliance and Attachments. "
            "Use the RFP facts, bidder clarifications, win themes, compliance matrix, and approved content blocks. "
            "Do not invent customer names, references, resumes, pricing numbers, contract values, or proprietary St. Moritz facts that are not provided. "
            "If the source package is missing company-specific references, resumes, or pricing workbooks, say so directly in a professional way and use explicit placeholders or gap notes instead of making up content. "
            "Do not mention internal workflow concepts such as Phase 1, proposal team operations, compliance matrix, or finishing in Word in the client-facing section text."
        )

    def _draft_prompt_payload(self, workspace: ProposalBuilderWorkspaceResponse) -> dict[str, Any]:
        blocks: list[dict[str, Any]] = []
        for plan in workspace.section_drafting_plan:
            requirement_texts = [row.requirement_text for row in workspace.requirements_list if row.requirement_code in set(plan.source_requirement_codes)]
            candidates = select_candidate_blocks(section_name=plan.proposal_section, requirement_texts=requirement_texts, limit=3)
            for block in candidates:
                blocks.append({"block_id": block.id, "title": block.title, "category": block.category, "tags": list(block.tags), "body": block.body[:1200]})
        return {
            "workflow_goal": "Generate a comprehensive first-pass proposal draft that is strong enough for HTML preview review and Word export.",
            "service_provider_name": (
                workspace.proposal_config.client_profile_name
                if workspace.proposal_config and workspace.proposal_config.client_profile_name
                else None
            ),
            "opportunity_summary": workspace.opportunity_summary.model_dump() if workspace.opportunity_summary else {},
            "document_gaps": workspace.document_gaps,
            "assumption_flags": workspace.assumption_flags,
            "evaluation_criteria": [item.model_dump() for item in workspace.evaluation_criteria],
            "submission_instructions": [item.model_dump() for item in workspace.submission_instructions],
            "win_themes": [item.model_dump() for item in workspace.win_themes],
            "proposal_outline": {
                "source": workspace.proposal_outline.source,
                "sections": [
                    {
                        "sequence": section.sequence,
                        "proposal_section": section.proposal_section,
                        "owner": section.owner,
                        "requirement_count": section.requirement_count,
                    }
                    for section in workspace.proposal_outline.sections
                ],
            } if workspace.proposal_outline else {},
            "section_drafting_plan": [item.model_dump() for item in workspace.section_drafting_plan],
            "requirements": [{"requirement_code": row.requirement_code, "category": row.category, "requirement_type": row.requirement_type, "requirement_text": row.requirement_text} for row in workspace.requirements_list[:40]],
            "content_blocks": blocks[:12],
        }

    def _ensure_required_draft_sections(self, draft_response: DraftStageArtifactResponse, fallback: DraftStageArtifactResponse) -> DraftStageArtifactResponse:
        existing_client_sections = draft_response.draft_package.client_sections or draft_response.draft_package.sections
        fallback_client_sections = fallback.draft_package.client_sections or fallback.draft_package.sections
        existing_titles = {section.section_title.lower() for section in existing_client_sections}
        sections = list(existing_client_sections)
        for section in fallback_client_sections:
            if section.section_title.lower() not in existing_titles:
                sections.append(section)
        sanitized_sections = [
            DraftSectionArtifact(
                section_title=section.section_title,
                body_markdown=_buyer_facing_text(section.body_markdown),
                used_content_block_ids=section.used_content_block_ids,
                cited_requirement_codes=section.cited_requirement_codes,
            )
            for section in sections
        ]
        unresolved_items = _unique_strings(draft_response.draft_package.unresolved_items + fallback.draft_package.unresolved_items)
        internal_notes = _unique_strings(draft_response.draft_package.internal_notes + fallback.draft_package.internal_notes)
        used_content_block_ids = _unique_strings(draft_response.draft_package.used_content_block_ids + fallback.draft_package.used_content_block_ids)
        cited_requirement_codes = _unique_strings(draft_response.draft_package.cited_requirement_codes + fallback.draft_package.cited_requirement_codes)
        return DraftStageArtifactResponse(
            draft_package=DraftPackageArtifact(
                sections=sanitized_sections,
                client_sections=sanitized_sections,
                internal_notes=internal_notes,
                unresolved_items=unresolved_items,
                editor_notes=draft_response.draft_package.editor_notes or fallback.draft_package.editor_notes,
                used_content_block_ids=used_content_block_ids,
                cited_requirement_codes=cited_requirement_codes,
            ),
            warnings=_unique_strings(draft_response.warnings + fallback.warnings),
        )

    def run_draft_stage(self, opportunity_id: str, *, actor: str = "operator") -> ProposalBuilderRunResponse:
        current_run = self._latest_run(opportunity_id)
        if current_run is None or not current_run.section_drafting_plan_json:
            self.run_skeleton_stage(opportunity_id, actor=actor)
        workspace = self.get_workspace(opportunity_id)
        fallback = self._fallback_draft_package(workspace=workspace)
        warnings = list(fallback.warnings)
        artifact = fallback
        model_name = None
        solicitation = self._latest_solicitation(opportunity_id)
        if solicitation is None:
            raise ProposalBuilderError("No solicitation is available for drafting.")
        generation_mode = "PENDING"
        generation_reason = None
        is_demo_sample = self._is_demo_sample_solicitation(solicitation)
        client = self._openai_client(
            stage_name="draft",
            source_text_length=len(solicitation.content_text),
            requirement_count=len(workspace.requirements_list),
        )
        cached_demo = (
            self._cached_demo_artifact("draft", DraftStageArtifactResponse)
            if is_demo_sample and BOSSKEY_PROPOSAL_BUILDER_ALLOW_CACHED_DEMO_FALLBACK
            else None
        )
        if not client.available:
            if cached_demo is not None:
                artifact = self._ensure_required_draft_sections(cached_demo, fallback)
                generation_mode = "FALLBACK_SAMPLE"
                generation_reason = "missing_api_key"
                warnings.append("Using the cached demo draft because a live OpenAI key is not configured.")
            else:
                message = self._live_stage_error_message(
                    stage_label="Draft generation",
                    timeout_seconds=client.timeout_seconds,
                    exc=OpenAIStructuredOutputError("OPENAI_API_KEY is not configured."),
                )
                self._record_stage_failure(
                    opportunity_id=opportunity_id,
                    solicitation_id=solicitation.id,
                    stage_name="draft",
                    actor=actor,
                    generation_reason="missing_api_key",
                    message=message,
                    model_name=None,
                )
                raise ProposalBuilderError(message)
        else:
            try:
                guardrails = self._stage_ai_guardrails(
                    stage_name="draft",
                    source_text_length=len(solicitation.content_text),
                    requirement_count=len(workspace.requirements_list),
                )
                parsed = client.generate_json(
                    system_prompt=self._draft_prompt(),
                    user_payload=self._draft_prompt_payload(workspace),
                    schema_name="proposal_builder_draft_stage",
                    schema=DraftStageArtifactResponse.model_json_schema(),
                    max_output_tokens=guardrails["max_output_tokens"],
                    max_estimated_input_tokens=guardrails["max_estimated_input_tokens"],
                    guardrail_label="draft",
                )
                artifact = _coerce_draft_stage_artifact(parsed)
                warnings.extend(artifact.warnings)
                artifact = self._ensure_required_draft_sections(artifact, fallback)
                generation_mode = "LIVE"
                generation_reason = "live_model"
                model_name = client.model
            except (OpenAIStructuredOutputError, ValueError) as exc:
                generation_reason = _generation_reason_from_exception(exc)
                if cached_demo is not None and BOSSKEY_PROPOSAL_BUILDER_ALLOW_LIVE_STAGE_FALLBACK:
                    artifact = self._ensure_required_draft_sections(cached_demo, fallback)
                    generation_mode = "FALLBACK_SAMPLE"
                    warnings.append("Loaded the cached demo draft artifact after the live stage failed.")
                elif generation_reason == "structured_output_validation_failed":
                    artifact = fallback
                    generation_mode = "FALLBACK_BASELINE"
                    warnings.append(
                        "The live draft step did not return usable structured output, "
                        "so the app kept a baseline Word-ready draft built from the current outline and inputs."
                    )
                else:
                    message = self._live_stage_error_message(
                        stage_label="Draft generation",
                        timeout_seconds=client.timeout_seconds,
                        exc=exc,
                    )
                    self._record_stage_failure(
                        opportunity_id=opportunity_id,
                        solicitation_id=solicitation.id,
                        stage_name="draft",
                        actor=actor,
                        generation_reason=generation_reason,
                        message=message,
                        model_name=client.model,
                    )
                    raise ProposalBuilderError(message)

        run = self._ensure_run(opportunity_id, solicitation.id)
        run.generation_mode = generation_mode
        run.model_name = model_name
        run.status = "DRAFT_READY"
        run.draft_package_json = json.dumps(artifact.draft_package.model_dump())
        run.warnings_json = _pack_warning_payload(_parse_json(run.warnings_json, []), warnings, generation_reason)
        self._update_workflow_summary(opportunity_id, compliance_status="IN_PROGRESS", pricing_status="IN_PROGRESS", review_gate_status="IN_PROGRESS", submission_milestone="First draft ready for Word finishing")
        self.db.flush()
        log_audit_event(self.db, opportunity_id=opportunity_id, actor=actor, action="proposal_builder_draft_completed", after_state_json=json.dumps({"generation_mode": generation_mode, "model_name": model_name, "draft_section_count": len(artifact.draft_package.sections)}))
        self.db.commit()
        self.db.refresh(run)
        opportunity = self.db.get(Opportunity, opportunity_id)
        requirements = self._latest_requirements(solicitation.id)
        return self._serialize_run(run, opportunity=opportunity, solicitation=solicitation, requirements=requirements)

    def run_export_stage(self, opportunity_id: str, *, actor: str = "operator") -> ProposalBuilderRunResponse:
        current_run = self._latest_run(opportunity_id)
        if current_run is None or not current_run.draft_package_json:
            self.run_draft_stage(opportunity_id, actor=actor)
        solicitation = self._latest_solicitation(opportunity_id)
        if solicitation is None:
            raise ProposalBuilderError("No solicitation is available for export.")
        run = self._ensure_run(opportunity_id, solicitation.id)
        existing_warnings = _parse_json(run.warnings_json, [])
        warnings, generation_reason = _extract_warning_metadata(existing_warnings)
        warnings = [
            warning
            for warning in warnings
            if warning != "Word draft export is outdated because draft sections were edited in the HTML preview."
        ]
        run.warnings_json = _pack_warning_payload([], warnings, generation_reason)
        workspace = self.get_workspace(opportunity_id)
        if workspace.proposal_config and workspace.proposal_config.client_profile_id:
            if not workspace.proposal_config.proposal_template_id:
                raise ProposalBuilderError("Select an approved client proposal template before running client-facing export.")
            if any("template" in item.lower() for item in workspace.proposal_config.validation_errors):
                raise ProposalBuilderError("The selected client proposal template is not approved for export.")
        selected_template = self._profile_service().selected_proposal_template(opportunity_id)
        manifest = build_export_bundle(
            workspace.model_dump(mode="json"),
            proposal_template=selected_template.model_dump(mode="json") if selected_template else None,
        )
        run = self._ensure_run(opportunity_id, solicitation.id)
        self._profile_service().apply_snapshot_to_run(opportunity_id, run)
        run.status = "EXPORTED"
        run.export_manifest_json = json.dumps(manifest, default=str)
        self._update_workflow_summary(opportunity_id, compliance_status="IN_PROGRESS", pricing_status="IN_PROGRESS", review_gate_status="IN_PROGRESS", submission_milestone="Export package generated and ready for Word finish")
        self.db.flush()
        log_audit_event(self.db, opportunity_id=opportunity_id, actor=actor, action="proposal_builder_export_completed", after_state_json=json.dumps({"docx_path": manifest["client_docx_path"], "zip_path": manifest["support_bundle_zip_path"]}))
        self.db.commit()
        self.db.refresh(run)
        opportunity = self.db.get(Opportunity, opportunity_id)
        requirements = self._latest_requirements(solicitation.id)
        return self._serialize_run(run, opportunity=opportunity, solicitation=solicitation, requirements=requirements)

    def build_presentable_artifact(self, opportunity_id: str, *, actor: str = "operator") -> ProposalBuilderRunResponse:
        solicitation = self._latest_solicitation(opportunity_id)
        if solicitation is None:
            raise ProposalBuilderError("Upload an initial RFP before building the Word draft.")

        current_run = self._latest_run(opportunity_id)
        if (
            current_run is None
            or current_run.source_solicitation_id != solicitation.id
            or not current_run.opportunity_summary_json
        ):
            self.run_extract_stage(opportunity_id, actor=actor)

        self.run_skeleton_stage(opportunity_id, actor=actor)
        self.run_draft_stage(opportunity_id, actor=actor)
        return self.run_export_stage(opportunity_id, actor=actor)

    def update_draft_section(
        self,
        opportunity_id: str,
        *,
        actor: str = "operator",
        section_index: int,
        body_markdown: str,
    ) -> ProposalBuilderRunResponse:
        run = self._latest_run(opportunity_id)
        solicitation = self._latest_solicitation(opportunity_id)
        if run is None or solicitation is None or not run.draft_package_json:
            raise ProposalBuilderError("Create the proposal draft before editing sections.")

        draft_package = DraftPackageArtifact.model_validate(_parse_json(run.draft_package_json, {}))
        updated_body = body_markdown.strip()
        if not updated_body:
            raise ProposalBuilderError("Section edits cannot be blank.")

        def _update_sections(sections: list[DraftSectionArtifact]) -> bool:
            if section_index < 0 or section_index >= len(sections):
                return False
            section = sections[section_index]
            sections[section_index] = section.model_copy(update={"body_markdown": updated_body})
            return True

        client_sections = list(draft_package.client_sections or draft_package.sections)
        sections = list(draft_package.sections or draft_package.client_sections)
        updated = _update_sections(client_sections)
        updated = _update_sections(sections) or updated
        if not updated:
            raise ProposalBuilderError("The selected draft section could not be found.")

        draft_package = draft_package.model_copy(
            update={
                "client_sections": client_sections,
                "sections": sections,
            }
        )

        run.draft_package_json = json.dumps(draft_package.model_dump())
        run.export_manifest_json = None
        run.status = "DRAFT_READY"
        existing_warnings = _parse_json(run.warnings_json, [])
        warnings, generation_reason = _extract_warning_metadata(existing_warnings)
        warnings = _unique_strings(
            [
                warning
                for warning in warnings
                if warning != "Word draft export is outdated because draft sections were edited in the HTML preview."
            ]
            + ["Word draft export is outdated because draft sections were edited in the HTML preview."]
        )
        run.warnings_json = _pack_warning_payload([], warnings, generation_reason)

        self.db.flush()
        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=actor,
            action="proposal_builder_draft_section_updated",
            after_state_json=json.dumps(
                {
                    "section_index": section_index,
                    "section_title": client_sections[section_index].section_title,
                    "body_length": len(updated_body),
                }
            ),
        )
        self.db.commit()
        self.db.refresh(run)
        opportunity = self.db.get(Opportunity, opportunity_id)
        requirements = self._latest_requirements(solicitation.id)
        return self._serialize_run(run, opportunity=opportunity, solicitation=solicitation, requirements=requirements)

    def get_export_download_path(self, opportunity_id: str, kind: str) -> tuple[Path, str] | None:
        opportunity = self.db.get(Opportunity, opportunity_id)
        solicitation = self._latest_solicitation(opportunity_id)
        requirements = self._latest_requirements(solicitation.id) if solicitation else []
        run = self._serialize_run(self._latest_run(opportunity_id), opportunity=opportunity, solicitation=solicitation, requirements=requirements)
        if not run or not run.export_manifest:
            return None
        manifest = run.export_manifest
        if kind == "docx":
            return Path(manifest.client_docx_path), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if kind == "bundle":
            return Path(manifest.support_bundle_zip_path), "application/zip"
        if kind == "markdown":
            return Path(manifest.markdown_path), "text/markdown"
        if kind == "html" and manifest.html_preview_path:
            return Path(manifest.html_preview_path), "text/html"
        if kind == "checklist" and manifest.missing_input_checklist_path:
            return Path(manifest.missing_input_checklist_path), "text/markdown"
        if kind == "json":
            return Path(manifest.json_path), "application/json"
        return None

    def add_supporting_materials(
        self,
        opportunity_id: str,
        *,
        actor: str,
        material_kind: str,
        files: list[tuple[str, bytes]] | None = None,
        raw_text: str | None = None,
        raw_text_filename: str | None = None,
    ) -> ProposalBuilderWorkspaceResponse:
        parser_service = RfpParserService(self.db)
        source = parser_service.get_latest_solicitation(opportunity_id)
        if not source:
            raise ProposalBuilderError("Upload an initial RFP before adding more material.")

        text_entries: list[tuple[str, str]] = []
        if raw_text and raw_text.strip():
            text_entries.append((self._material_filename(material_kind, raw_text_filename), raw_text.strip()))

        batch = extract_text_from_mixed_inputs(files or [], text_entries=text_entries)
        parsed_new_documents = [item for item in batch.documents if item.parse_status == "PARSED" and item.content_text]
        if not parsed_new_documents:
            warnings = "; ".join(batch.warnings) if batch.warnings else "No readable supporting material was found."
            raise ProposalBuilderError(warnings)

        existing_rows = parser_service.list_source_documents_for_solicitation(source.id)
        effective_source_documents = parser_service._resolved_source_document_inputs(solicitation=source, rows=existing_rows)
        next_upload_order = len(effective_source_documents) + 1
        for offset, item in enumerate(batch.documents, start=next_upload_order):
            effective_source_documents.append(
                RfpSourceDocumentInput(
                    source_filename=item.source_filename,
                    content_type=item.content_type,
                    parse_status=item.parse_status,
                    skip_reason=item.skip_reason,
                    upload_order=offset,
                    source_size_bytes=item.source_size_bytes,
                    extracted_text_length=item.extracted_text_length,
                    content_text=item.content_text,
                    source_payload=item.source_payload,
                )
            )

        parser_service.reparse_solicitation(
            opportunity_id,
            RfpReparseRequest(
                actor=actor,
                source_solicitation_id=source.id,
                source_documents=effective_source_documents,
            ),
        )
        try:
            self.run_extract_stage(opportunity_id, actor=actor)
        except ProposalBuilderError:
            pass

        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=actor,
            action="proposal_builder_supporting_materials_added",
            after_state_json=json.dumps(
                {
                    "material_kind": material_kind,
                    "added_document_count": len(parsed_new_documents),
                    "added_filenames": [item.source_filename for item in parsed_new_documents],
                }
            ),
        )
        self.db.commit()
        return self.get_workspace(opportunity_id)

    def get_workspace(self, opportunity_id: str) -> ProposalBuilderWorkspaceResponse:
        opportunity = self.db.get(Opportunity, opportunity_id)
        if not opportunity:
            raise ProposalBuilderError("Opportunity not found.")
        solicitation = self._latest_solicitation(opportunity_id)
        parser_service = RfpParserService(self.db)
        source_documents = parser_service.list_source_documents_for_solicitation(solicitation.id) if solicitation else []
        version_history = parser_service.list_versions(opportunity_id)
        latest_package_run = self._latest_package_run_model(opportunity_id)
        requirements = (
            [RequirementRecord.model_validate(row, from_attributes=True) for row in self._latest_requirements(solicitation.id)]
            if solicitation
            else []
        )
        run = self._serialize_run(
            self._latest_run(opportunity_id),
            opportunity=opportunity,
            solicitation=solicitation,
            requirements=requirements,
        )
        resolved_config = self._profile_service().resolve_opportunity_config(opportunity_id)
        compliance_rows = [
            ComplianceMatrixRowResponse.model_validate(row)
            for row in ComplianceMatrixService(self.db).list_rows(opportunity_id, include_context=False)
        ]
        workflow_summary = self.db.query(ProposalWorkflowSummary).filter(ProposalWorkflowSummary.opportunity_id == opportunity_id).first()
        summary_payload = (
            {
                "pricing_status": workflow_summary.pricing_status,
                "compliance_status": workflow_summary.compliance_status,
                "review_gate_status": workflow_summary.review_gate_status,
                "submission_milestone": workflow_summary.submission_milestone,
                "sme_assignments": _parse_json(workflow_summary.sme_assignments_json, []),
            }
            if workflow_summary
            else {}
        )
        source_text_length = len(solicitation.content_text) if solicitation else 0
        summary_payload["stage_runtime_guidance"] = {
            "extract_seconds": self._stage_timeout_seconds(
                stage_name="extract",
                source_text_length=source_text_length,
                requirement_count=len(requirements),
            ),
            "skeleton_seconds": self._stage_timeout_seconds(
                stage_name="skeleton",
                source_text_length=source_text_length,
                requirement_count=len(requirements),
            ),
            "draft_seconds": self._stage_timeout_seconds(
                stage_name="draft",
                source_text_length=source_text_length,
                requirement_count=len(requirements),
            ),
        }
        summary_payload["stage_token_guardrails"] = {
            "extract": self._stage_ai_guardrails(
                stage_name="extract",
                source_text_length=source_text_length,
                requirement_count=len(requirements),
            ),
            "skeleton": self._stage_ai_guardrails(
                stage_name="skeleton",
                source_text_length=source_text_length,
                requirement_count=len(requirements),
            ),
            "draft": self._stage_ai_guardrails(
                stage_name="draft",
                source_text_length=source_text_length,
                requirement_count=len(requirements),
            ),
        }
        structured_fields = self._structured_fields(solicitation)
        source_based_gaps = _source_document_gaps(solicitation=solicitation, source_documents=source_documents)
        document_gaps = _ensure_list(run.document_gaps if run else [], *source_based_gaps)
        recommended_materials = self._recommended_materials(
            structured_fields=structured_fields,
            requirements=requirements,
        )
        workspace = ProposalBuilderWorkspaceResponse(
            opportunity_id=opportunity.id,
            opportunity_name=opportunity.name,
            client_name=opportunity.client,
            solicitation_id=solicitation.id if solicitation else None,
            solicitation_version=solicitation.version if solicitation else None,
            source_documents=source_documents,
            solicitation_versions=version_history,
            extracted_deadline=solicitation.extracted_deadline if solicitation else None,
            generation_mode=run.generation_mode if run else None,
            generation_reason=run.generation_reason if run else None,
            model_name=run.model_name if run else None,
            proposal_config=resolved_config.config,
            active_onboarding_pack_id=resolved_config.config.active_onboarding_pack_id,
            active_playbook_version=resolved_config.config.active_playbook_version,
            client_environment_status=resolved_config.config.client_environment_status,
            setup_gaps=resolved_config.config.setup_gaps,
            available_client_profiles=resolved_config.available_profiles,
            available_pricing_models=resolved_config.available_pricing_models,
            available_proposal_templates=resolved_config.available_proposal_templates,
            structured_fields=structured_fields,
            opportunity_summary=run.opportunity_summary if run else None,
            document_gaps=document_gaps,
            assumption_flags=run.assumption_flags if run else [],
            requirements_list=requirements,
            evaluation_criteria=run.evaluation_criteria if run else [],
            submission_instructions=run.submission_instructions if run else [],
            compliance_matrix=compliance_rows,
            proposal_outline=self._latest_outline_response(opportunity_id),
            win_themes=run.win_themes if run else [],
            section_drafting_plan=run.section_drafting_plan if run else [],
            draft_package=run.draft_package if run else None,
            client_sections=run.client_sections if run else [],
            internal_notes=run.internal_notes if run else [],
            export_manifest=run.export_manifest if run else None,
            submission_readiness=SubmissionChecklistService(self.db).readiness(opportunity_id),
            recommended_materials=recommended_materials,
            follow_up_actions=self._follow_up_actions(
                package_run=latest_package_run,
                document_gaps=document_gaps,
                recommended_materials=recommended_materials,
            ),
            workflow_summary=summary_payload,
            warnings=run.warnings if run else [],
            detail_links={
                "rfp_upload": f"/opportunities/{opportunity_id}/rfp-upload",
                "compliance_matrix": f"/opportunities/{opportunity_id}/compliance-matrix",
                "proposal_outline": f"/opportunities/{opportunity_id}/proposal-outline",
                "capture_plan": f"/opportunities/{opportunity_id}/capture-plan",
                "submission": f"/opportunities/{opportunity_id}/submission",
            },
        )
        workspace.workflow_summary["client_environment_status"] = resolved_config.config.client_environment_status
        workspace.workflow_summary["active_onboarding_pack_name"] = resolved_config.config.active_onboarding_pack_name
        workspace.workflow_summary["active_playbook_version"] = resolved_config.config.active_playbook_version
        workspace.workflow_summary["setup_gaps_count"] = len(resolved_config.config.setup_gaps)
        workspace.workflow_summary["stage_flags"] = _workflow_stage_flags(workspace)
        return workspace

    def _default_lead_time(self, extracted_deadline: str | None) -> int:
        parsed_deadline = _parse_date(extracted_deadline)
        if parsed_deadline is None:
            return 45
        return max((parsed_deadline - date.today()).days, 14)

    def _auto_confirm_payload(self, draft: OpportunityIntakeDraftResponse, *, actor: str) -> OpportunityIntakeDraftConfirmRequest | None:
        if not draft.suggested_fields.name or not draft.suggested_fields.client:
            return None
        return OpportunityIntakeDraftConfirmRequest(
            name=draft.suggested_fields.name,
            client=draft.suggested_fields.client,
            estimated_contract_value=draft.suggested_fields.estimated_contract_value or 250000,
            lead_time_days=draft.suggested_fields.lead_time_days or self._default_lead_time(draft.extracted_deadline),
            incumbent_status=draft.suggested_fields.incumbent_status,
            strategic_alignment=4,
            estimated_probability_win=60,
            actor=actor,
        )

    def start_from_inputs(
        self,
        *,
        actor: str,
        files: list[tuple[str, bytes]] | None = None,
        raw_text: str | None = None,
        raw_text_filename: str | None = None,
        use_demo_sample: bool = False,
    ) -> ProposalBuilderStartResult:
        text_entries: list[tuple[str, str]] = []
        if use_demo_sample:
            text_entries.append((DEMO_SAMPLE_FILENAME, self.demo_sample_text()))
        elif raw_text and raw_text.strip():
            text_entries.append((raw_text_filename or "pasted-rfp.txt", raw_text))

        batch = extract_text_from_mixed_inputs(files or [], text_entries=text_entries)
        intake_service = OpportunityIntakeService(self.db)
        draft = intake_service.create_intake_rfp_draft(actor, batch)
        auto_payload = self._auto_confirm_payload(draft, actor=actor)
        if auto_payload is None:
            return ProposalBuilderStartResult(
                opportunity_id=None,
                draft_id=draft.draft_id,
                intake_status="PENDING_CONFIRMATION",
                needs_confirmation=True,
                suggested_name=draft.suggested_fields.name,
                suggested_client=draft.suggested_fields.client,
                warnings=draft.warnings,
            )

        result = intake_service.confirm_intake_rfp_draft(draft.draft_id, auto_payload)
        warnings = list(draft.warnings)
        try:
            self.run_extract_stage(result.id, actor=actor)
        except ProposalBuilderError as exc:
            warnings.append(str(exc))
        return ProposalBuilderStartResult(
            opportunity_id=result.id,
            draft_id=draft.draft_id,
            intake_status="READY",
            warnings=warnings,
        )

    def confirm_start(self, *, draft_id: str, actor: str, name: str, client: str) -> ProposalBuilderStartResult:
        intake_service = OpportunityIntakeService(self.db)
        draft = intake_service.get_intake_rfp_draft(draft_id)
        if not draft:
            raise ProposalBuilderError("RFP intake draft not found.")
        payload = OpportunityIntakeDraftConfirmRequest(
            name=name,
            client=client,
            estimated_contract_value=draft.suggested_fields.estimated_contract_value or 250000,
            lead_time_days=draft.suggested_fields.lead_time_days or self._default_lead_time(draft.extracted_deadline),
            incumbent_status=draft.suggested_fields.incumbent_status,
            strategic_alignment=4,
            estimated_probability_win=60,
            actor=actor,
        )
        result = intake_service.confirm_intake_rfp_draft(draft_id, payload)
        warnings = list(draft.warnings)
        try:
            self.run_extract_stage(result.id, actor=actor)
        except ProposalBuilderError as exc:
            warnings.append(str(exc))
        return ProposalBuilderStartResult(
            opportunity_id=result.id,
            draft_id=draft_id,
            intake_status="READY",
            warnings=warnings,
        )
