from __future__ import annotations

import json
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.core.config import BOSSKEY_ENABLE_COLOR_TEAM_REVIEWS, EXPORTS_DIR
from app.core.db import SessionLocal
from app.modules.opportunity_intake.models import Opportunity
from app.modules.proposal_builder.apmp_playbook import apmp_findings_for_gaps, summarize_apmp_topics
from app.modules.proposal_builder.client_profiles import ClientProfileError, ClientProfileService
from app.modules.proposal_builder.content_authority import approved_assets_inventory, required_asset_blockers, select_assets
from app.modules.proposal_builder.export import build_proposal_package_export_bundle
from app.modules.proposal_builder.forms_engine import build_form_package
from app.modules.proposal_builder.models import ProposalBuilderRun, ProposalPackageRun, ProposalPackageStageRun
from app.modules.proposal_builder.onboarding import ClientOnboardingService
from app.modules.proposal_builder.openai_client import OpenAIStructuredOutputError
from app.modules.proposal_builder.pricing_engine import build_pricing_package
from app.modules.proposal_builder.schemas import (
    ContentPlanArtifact,
    CustomerStrategyArtifact,
    DraftPackageArtifact,
    DraftSectionArtifact,
    DraftStageArtifactResponse,
    ExportManifestArtifact,
    FormPackageArtifact,
    PricingPackageArtifact,
    ProposalPackageRunCreateRequest,
    ProposalPackageRunResponse,
    ProposalPackageStageApprovalRequest,
    ProposalPackageStageResponse,
    ReviewFindingArtifact,
)
from app.modules.proposal_builder.service import ProposalBuilderError, ProposalBuilderService
from app.modules.rfp_parser.models import Solicitation


_BASE_PACKAGE_STAGE_ORDER: list[tuple[str, str | None, str | None]] = [
    ("ingest", None, None),
    ("extract_and_classify", None, "medium"),
    ("compliance_and_submission_map", None, "medium"),
    ("customer_strategy", None, "high"),
    ("content_plan", None, "high"),
    ("full_draft", None, "high"),
    ("pricing", "pricing", None),
    ("forms_and_attachments", None, None),
    ("pink_team_review", None, "high"),
    ("red_team_review", None, "high"),
    ("gold_team_production_review", None, "medium"),
    ("export_package", "export", None),
]
if BOSSKEY_ENABLE_COLOR_TEAM_REVIEWS:
    PACKAGE_STAGE_ORDER = list(_BASE_PACKAGE_STAGE_ORDER)
else:
    PACKAGE_STAGE_ORDER = [
        stage
        for stage in _BASE_PACKAGE_STAGE_ORDER
        if stage[0] not in {"pink_team_review", "red_team_review", "gold_team_production_review"}
    ]
RUNNING_STATUSES = {"QUEUED", "IN_PROGRESS"}
AUTO_REFRESH_STATUSES = RUNNING_STATUSES | {"AWAITING_PRICING_APPROVAL", "AWAITING_EXPORT_APPROVAL"}
REVIEW_STAGE_NAMES = (
    {"pink_team_review", "red_team_review", "gold_team_production_review"}
    if BOSSKEY_ENABLE_COLOR_TEAM_REVIEWS
    else set()
)


def _parse_json(raw: str | None, default: Any) -> Any:
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def _dump_json(value: Any) -> str:
    return json.dumps(value, default=str)


def _workspace_tags(workspace: dict[str, Any]) -> list[str]:
    text = " ".join(
        [
            workspace.get("client_name", ""),
            workspace.get("opportunity_name", ""),
            json.dumps(workspace.get("structured_fields", {}), default=str),
            json.dumps(workspace.get("opportunity_summary", {}), default=str),
        ]
    ).lower()
    tags = {"janitorial"}
    if "airport" in text:
        tags.add("airport")
    if "authority" in text or "agency" in text or "public" in text:
        tags.add("public-sector")
    if "day porter" in text or "day-porter" in text:
        tags.add("day-porter")
    return sorted(tags)


class ProposalPackageService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _builder(self) -> ProposalBuilderService:
        return ProposalBuilderService(self.db)

    def _profile_service(self) -> ClientProfileService:
        return ClientProfileService(self.db)

    def _onboarding_service(self) -> ClientOnboardingService:
        return ClientOnboardingService(self.db)

    def _runtime_asset_inventory(self, opportunity_id: str) -> list[dict[str, Any]]:
        runtime_assets = self._onboarding_service().runtime_asset_inventory(opportunity_id)
        return runtime_assets if runtime_assets else approved_assets_inventory()

    def _runtime_form_templates(self, opportunity_id: str) -> list[dict[str, Any]]:
        return self._onboarding_service().runtime_form_templates(opportunity_id)

    def _active_environment(self, opportunity_id: str) -> dict[str, Any]:
        return self._onboarding_service().active_environment_for_opportunity(opportunity_id)

    def _playbook_context(self, opportunity_id: str) -> dict[str, Any]:
        environment = self._active_environment(opportunity_id)
        playbook = environment.get("playbook")
        behavior_profile = environment.get("behavior_profile")
        return {
            "client_playbook": {
                "title": getattr(playbook, "title", None),
                "version": getattr(playbook, "version", None),
                "narrative_guidance_md": getattr(playbook, "narrative_guidance_md", None),
            }
            if playbook
            else {},
            "client_behavior_profile": _parse_json(getattr(behavior_profile, "behavior_profile_json", None), {}),
        }

    def _latest_solicitation(self, opportunity_id: str) -> Solicitation | None:
        stmt = (
            select(Solicitation)
            .where(Solicitation.opportunity_id == opportunity_id)
            .order_by(Solicitation.version.desc(), Solicitation.created_at.desc())
        )
        return self.db.scalars(stmt).first()

    def _latest_builder_run(self, opportunity_id: str) -> ProposalBuilderRun | None:
        stmt = (
            select(ProposalBuilderRun)
            .where(ProposalBuilderRun.opportunity_id == opportunity_id)
            .order_by(ProposalBuilderRun.version.desc(), ProposalBuilderRun.updated_at.desc())
        )
        return self.db.scalars(stmt).first()

    def _latest_package_run(self, opportunity_id: str) -> ProposalPackageRun | None:
        stmt = (
            select(ProposalPackageRun)
            .where(ProposalPackageRun.opportunity_id == opportunity_id)
            .order_by(ProposalPackageRun.version.desc(), ProposalPackageRun.updated_at.desc())
        )
        return self.db.scalars(stmt).first()

    def _next_package_run_version(self, opportunity_id: str) -> int:
        latest = self._latest_package_run(opportunity_id)
        return 1 if latest is None else latest.version + 1

    def _stage_rows(self, run_id: str) -> list[ProposalPackageStageRun]:
        stmt = (
            select(ProposalPackageStageRun)
            .where(ProposalPackageStageRun.proposal_package_run_id == run_id)
            .order_by(ProposalPackageStageRun.stage_sequence.asc(), ProposalPackageStageRun.created_at.asc())
        )
        return list(self.db.scalars(stmt))

    def _stage_row(self, run_id: str, stage_name: str) -> ProposalPackageStageRun:
        stmt = (
            select(ProposalPackageStageRun)
            .where(
                ProposalPackageStageRun.proposal_package_run_id == run_id,
                ProposalPackageStageRun.stage_name == stage_name,
            )
            .order_by(ProposalPackageStageRun.stage_sequence.asc())
        )
        stage = self.db.scalars(stmt).first()
        if stage is None:
            raise ProposalBuilderError(f"Package stage '{stage_name}' was not found.")
        return stage

    def _run_dir(self, run: ProposalPackageRun) -> Path:
        target = EXPORTS_DIR / run.opportunity_id / "package-runs" / run.id
        target.mkdir(parents=True, exist_ok=True)
        return target

    def _run_flags(self, run: ProposalPackageRun) -> dict[str, Any]:
        return _parse_json(run.package_artifacts_json, {})

    def _is_demo_mode(self, run: ProposalPackageRun) -> bool:
        return bool(self._run_flags(run).get("demo_mode"))

    def _allow_draft_pricing_model_in_demo(self, run: ProposalPackageRun, pricing_model: Any | None) -> bool:
        if not self._is_demo_mode(run) or pricing_model is None:
            return False
        validation_report = getattr(pricing_model, "validation_report", None)
        validation_errors = list(validation_report.errors) if validation_report else []
        return bool(getattr(pricing_model, "canonical_model", None)) and not validation_errors

    def _allow_draft_template_in_demo(self, run: ProposalPackageRun, proposal_template: Any | None) -> bool:
        if not self._is_demo_mode(run) or proposal_template is None:
            return False
        validation_report = getattr(proposal_template, "validation_report", None)
        validation_errors = list(validation_report.errors) if validation_report else []
        return not validation_errors

    def _serialize_stage(self, stage: ProposalPackageStageRun) -> ProposalPackageStageResponse:
        return ProposalPackageStageResponse(
            id=stage.id,
            stage_name=stage.stage_name,
            stage_sequence=stage.stage_sequence,
            status=stage.status,
            attempt_count=stage.attempt_count,
            model_name=stage.model_name,
            reasoning_profile=stage.reasoning_profile,
            runtime_seconds=stage.runtime_seconds,
            openai_response_id=stage.openai_response_id,
            approval_required=stage.approval_required,
            approval_status=stage.approval_status,
            approved_by=stage.approved_by,
            approved_at=stage.approved_at,
            blocking_issues=_parse_json(stage.blocking_issues_json, []),
            warnings=_parse_json(stage.warnings_json, []),
            failure_reason=stage.failure_reason,
            artifact=_parse_json(stage.artifact_json, {}),
            created_at=stage.created_at,
            updated_at=stage.updated_at,
        )

    def _serialize_run(self, run: ProposalPackageRun | None) -> ProposalPackageRunResponse | None:
        if run is None:
            return None
        try:
            proposal_config = self._profile_service().opportunity_config(run.opportunity_id)
        except ClientProfileError:
            proposal_config = None
        return ProposalPackageRunResponse(
            id=run.id,
            opportunity_id=run.opportunity_id,
            source_solicitation_id=run.source_solicitation_id,
            version=run.version,
            status=run.status,
            current_stage=run.current_stage,
            generation_mode=run.generation_mode,
            generation_reason=run.generation_reason,
            proposal_config=proposal_config,
            active_onboarding_pack_id=(proposal_config.active_onboarding_pack_id if proposal_config else run.onboarding_pack_id),
            active_playbook_version=(proposal_config.active_playbook_version if proposal_config else run.playbook_version),
            client_environment_status=(proposal_config.client_environment_status if proposal_config else None),
            setup_gaps=(proposal_config.setup_gaps if proposal_config else []),
            requested_by=run.requested_by,
            requested_at=run.requested_at,
            started_at=run.started_at,
            completed_at=run.completed_at,
            approved_pricing_by=run.approved_pricing_by,
            approved_pricing_at=run.approved_pricing_at,
            approved_export_by=run.approved_export_by,
            approved_export_at=run.approved_export_at,
            blocking_issues=_parse_json(run.blocking_issues_json, []),
            warnings=_parse_json(run.warnings_json, []),
            customer_strategy=CustomerStrategyArtifact.model_validate(_parse_json(run.customer_strategy_json, {}))
            if run.customer_strategy_json
            else None,
            content_plan=ContentPlanArtifact.model_validate(_parse_json(run.content_plan_json, {}))
            if run.content_plan_json
            else None,
            pricing_package=PricingPackageArtifact.model_validate(_parse_json(run.pricing_package_json, {}))
            if run.pricing_package_json
            else None,
            form_package=FormPackageArtifact.model_validate(_parse_json(run.form_package_json, {}))
            if run.form_package_json
            else None,
            review_findings=[ReviewFindingArtifact.model_validate(item) for item in _parse_json(run.review_findings_json, [])],
            export_manifest=ExportManifestArtifact.model_validate(_parse_json(run.package_export_manifest_json, {}))
            if run.package_export_manifest_json
            else None,
            package_artifacts=_parse_json(run.package_artifacts_json, {}),
            stages=[self._serialize_stage(stage) for stage in self._stage_rows(run.id)],
            created_at=run.created_at,
            updated_at=run.updated_at,
        )

    def get_run(self, opportunity_id: str, run_id: str) -> ProposalPackageRunResponse:
        run = self.db.get(ProposalPackageRun, run_id)
        if run is None or run.opportunity_id != opportunity_id:
            raise ProposalBuilderError("Package run not found.")
        serialized = self._serialize_run(run)
        assert serialized is not None
        return serialized

    def get_latest_run_response(self, opportunity_id: str) -> ProposalPackageRunResponse | None:
        return self._serialize_run(self._latest_package_run(opportunity_id))

    def create_run(self, opportunity_id: str, payload: ProposalPackageRunCreateRequest) -> ProposalPackageRunResponse:
        opportunity = self.db.get(Opportunity, opportunity_id)
        solicitation = self._latest_solicitation(opportunity_id)
        if opportunity is None or solicitation is None:
            raise ProposalBuilderError("A parsed opportunity and solicitation are required before starting a package run.")

        latest = self._latest_package_run(opportunity_id)
        if latest and latest.status in RUNNING_STATUSES:
            raise ProposalBuilderError("A package run is already working in the background for this opportunity. Wait for it to finish before starting another one.")

        latest_builder_run = self._latest_builder_run(opportunity_id)
        run = ProposalPackageRun(
            opportunity_id=opportunity_id,
            source_solicitation_id=solicitation.id,
            proposal_builder_run_id=latest_builder_run.id if latest_builder_run else None,
            version=self._next_package_run_version(opportunity_id),
            status="QUEUED",
            current_stage=PACKAGE_STAGE_ORDER[0][0],
            generation_mode="PENDING",
            requested_by=payload.actor,
            package_artifacts_json=_dump_json({"demo_mode": payload.demo_mode}),
            blocking_issues_json="[]",
            warnings_json="[]",
        )
        self.db.add(run)
        self.db.flush()
        self._profile_service().apply_snapshot_to_run(opportunity_id, run)
        for sequence, (stage_name, approval_required, reasoning_profile) in enumerate(PACKAGE_STAGE_ORDER, start=1):
            self.db.add(
                ProposalPackageStageRun(
                    proposal_package_run_id=run.id,
                    stage_name=stage_name,
                    stage_sequence=sequence,
                    status="PENDING",
                    approval_required=approval_required,
                    approval_status="PENDING" if approval_required else None,
                    reasoning_profile=reasoning_profile,
                )
            )
        self.db.flush()
        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=payload.actor,
            action="proposal_package_run_created",
            after_state_json=_dump_json({"run_id": run.id, "version": run.version}),
        )
        self.db.commit()
        self.db.refresh(run)
        serialized = self._serialize_run(run)
        assert serialized is not None
        return serialized

    def _update_run_lists(self, run: ProposalPackageRun, *, warnings: list[str] | None = None, blockers: list[str] | None = None) -> None:
        if warnings:
            existing_warnings = _parse_json(run.warnings_json, [])
            run.warnings_json = _dump_json(sorted(set(existing_warnings + warnings)))
        if blockers is not None:
            existing_blockers = _parse_json(run.blocking_issues_json, [])
            run.blocking_issues_json = _dump_json(sorted(set(existing_blockers + blockers)))

    def _mark_stage_in_progress(self, run: ProposalPackageRun, stage: ProposalPackageStageRun) -> float:
        now = datetime.now(UTC).replace(tzinfo=None)
        run.status = "IN_PROGRESS"
        run.current_stage = stage.stage_name
        if run.started_at is None:
            run.started_at = now
        stage.status = "IN_PROGRESS"
        stage.attempt_count += 1
        stage.started_at = now
        stage.failure_reason = None
        self.db.flush()
        return time.monotonic()

    def _mark_stage_complete(
        self,
        run: ProposalPackageRun,
        stage: ProposalPackageStageRun,
        *,
        started_clock: float,
        artifact: dict[str, Any] | None = None,
        warnings: list[str] | None = None,
        blockers: list[str] | None = None,
        model_name: str | None = None,
        response_id: str | None = None,
        token_usage: dict[str, Any] | None = None,
        input_sources: list[str] | None = None,
        generation_mode: str | None = None,
        generation_reason: str | None = None,
        waiting_for_approval: bool = False,
    ) -> None:
        now = datetime.now(UTC).replace(tzinfo=None)
        stage.runtime_seconds = int(max(time.monotonic() - started_clock, 0))
        stage.completed_at = now
        stage.model_name = model_name
        stage.openai_response_id = response_id
        stage.token_usage_json = _dump_json(token_usage or {})
        stage.input_sources_json = _dump_json(input_sources or [])
        stage.artifact_json = _dump_json(artifact or {})
        stage.warnings_json = _dump_json(warnings or [])
        stage.blocking_issues_json = _dump_json(blockers or [])
        if waiting_for_approval:
            stage.status = "AWAITING_APPROVAL"
            stage.approval_status = "PENDING"
        else:
            stage.status = "COMPLETED"
        if generation_mode:
            run.generation_mode = generation_mode
        if generation_reason:
            run.generation_reason = generation_reason
        self._update_run_lists(run, warnings=warnings, blockers=blockers)
        self.db.flush()

    def _mark_stage_completed_with_gaps(
        self,
        run: ProposalPackageRun,
        stage: ProposalPackageStageRun,
        *,
        started_clock: float,
        message: str,
        artifact: dict[str, Any] | None = None,
        warnings: list[str] | None = None,
        blockers: list[str] | None = None,
        model_name: str | None = None,
        response_id: str | None = None,
        token_usage: dict[str, Any] | None = None,
        input_sources: list[str] | None = None,
        generation_mode: str | None = None,
        generation_reason: str | None = None,
        waiting_for_approval: bool = False,
    ) -> None:
        now = datetime.now(UTC).replace(tzinfo=None)
        stage.runtime_seconds = int(max(time.monotonic() - started_clock, 0))
        stage.completed_at = now
        stage.model_name = model_name
        stage.openai_response_id = response_id
        stage.token_usage_json = _dump_json(token_usage or {})
        stage.input_sources_json = _dump_json(input_sources or [])
        stage.artifact_json = _dump_json(artifact or {})
        merged_warnings = sorted(set((warnings or []) + [message]))
        stage.warnings_json = _dump_json(merged_warnings)
        stage.blocking_issues_json = _dump_json(blockers or [])
        stage.failure_reason = message
        if waiting_for_approval:
            stage.status = "AWAITING_APPROVAL"
            stage.approval_status = "PENDING"
        else:
            stage.status = "COMPLETED_WITH_GAPS"
        if generation_mode:
            run.generation_mode = generation_mode
        if generation_reason:
            run.generation_reason = generation_reason
        self._update_run_lists(run, warnings=merged_warnings, blockers=blockers or [])
        self.db.flush()

    def _mark_stage_failed(self, run: ProposalPackageRun, stage: ProposalPackageStageRun, *, started_clock: float, message: str, blockers: list[str] | None = None) -> None:
        now = datetime.now(UTC).replace(tzinfo=None)
        stage.runtime_seconds = int(max(time.monotonic() - started_clock, 0))
        stage.completed_at = now
        stage.status = "FAILED"
        stage.failure_reason = message
        stage.blocking_issues_json = _dump_json(blockers or [])
        run.status = "BLOCKED"
        run.current_stage = stage.stage_name
        run.generation_mode = "ERROR"
        run.generation_reason = "stage_failed"
        self._update_run_lists(run, warnings=[message], blockers=blockers or [])
        self.db.flush()

    def _stage_index(self, stage_name: str) -> int:
        for index, (candidate, _approval, _reasoning) in enumerate(PACKAGE_STAGE_ORDER):
            if candidate == stage_name:
                return index
        raise ProposalBuilderError(f"Unknown package stage '{stage_name}'.")

    def approve_stage(self, opportunity_id: str, run_id: str, payload: ProposalPackageStageApprovalRequest) -> ProposalPackageRunResponse:
        run = self.db.get(ProposalPackageRun, run_id)
        if run is None or run.opportunity_id != opportunity_id:
            raise ProposalBuilderError("Package run not found.")
        stage = self._stage_row(run_id, payload.stage_name)
        now = datetime.now(UTC).replace(tzinfo=None)
        if stage.approval_required is None:
            if not (run.status == "BLOCKED" and payload.stage_name in REVIEW_STAGE_NAMES and stage.status == "FAILED"):
                raise ProposalBuilderError("The selected stage does not require approval.")
            stage.status = "COMPLETED"
            stage.failure_reason = None
            stage.blocking_issues_json = _dump_json([])
            existing_stage_warnings = _parse_json(stage.warnings_json, [])
            stage.warnings_json = _dump_json(
                sorted(
                    set(
                        existing_stage_warnings
                        + [f"{payload.stage_name.replace('_', ' ').title()} findings were acknowledged and the workflow resumed."]
                    )
                )
            )
            stage.approval_status = "ACKNOWLEDGED"
            stage.approved_by = payload.actor
            stage.approved_at = now
            existing_run_warnings = _parse_json(run.warnings_json, [])
            run.warnings_json = _dump_json(
                sorted(
                    set(
                        existing_run_warnings
                        + [f"{payload.stage_name.replace('_', ' ').title()} findings were acknowledged by {payload.actor}."]
                    )
                )
            )
            run.blocking_issues_json = _dump_json([])
        else:
            stage.approval_status = "APPROVED"
            stage.approved_by = payload.actor
            stage.approved_at = now
            if payload.stage_name == "pricing":
                stage.status = "COMPLETED"
                run.approved_pricing_by = payload.actor
                run.approved_pricing_at = now
            elif payload.stage_name == "export_package":
                run.approved_export_by = payload.actor
                run.approved_export_at = now
        run.status = "QUEUED"
        run.current_stage = payload.stage_name
        run.generation_mode = "PENDING"
        run.generation_reason = "approval_granted"
        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=payload.actor,
            action="proposal_package_stage_approved",
            after_state_json=_dump_json({"run_id": run.id, "stage_name": payload.stage_name}),
        )
        self.db.commit()
        self.db.refresh(run)
        serialized = self._serialize_run(run)
        assert serialized is not None
        return serialized

    def rerun_stage(self, opportunity_id: str, run_id: str, payload: ProposalPackageStageApprovalRequest) -> ProposalPackageRunResponse:
        run = self.db.get(ProposalPackageRun, run_id)
        if run is None or run.opportunity_id != opportunity_id:
            raise ProposalBuilderError("Package run not found.")
        if payload.demo_mode is not None:
            run_flags = self._run_flags(run)
            run_flags["demo_mode"] = payload.demo_mode
            run.package_artifacts_json = _dump_json(run_flags)
        start_index = self._stage_index(payload.stage_name)
        for stage in self._stage_rows(run_id):
            if stage.stage_sequence >= start_index + 1:
                stage.status = "PENDING"
                stage.failure_reason = None
                stage.artifact_json = None
                stage.blocking_issues_json = None
                stage.warnings_json = None
                stage.completed_at = None
                if stage.approval_required:
                    stage.approval_status = "PENDING"
                    stage.approved_by = None
                    stage.approved_at = None
        run.status = "QUEUED"
        run.current_stage = payload.stage_name
        run.generation_mode = "PENDING"
        run.generation_reason = "rerun_requested"
        run.blocking_issues_json = _dump_json([])
        if payload.stage_name == "pricing":
            run.approved_pricing_by = None
            run.approved_pricing_at = None
            run.pricing_package_json = None
        if payload.stage_name == "export_package":
            run.approved_export_by = None
            run.approved_export_at = None
            run.package_export_manifest_json = None
        self.db.commit()
        self.db.refresh(run)
        serialized = self._serialize_run(run)
        assert serialized is not None
        return serialized

    def _ai_client(self, workspace: dict[str, Any], *, stage_name: str):
        builder = self._builder()
        requirement_count = len(workspace.get("requirements_list", []))
        source_text_length = len(json.dumps(workspace.get("structured_fields", {}), default=str)) + len(
            json.dumps(workspace.get("requirements_list", []), default=str)
        )
        return builder._openai_client(
            stage_name="draft" if stage_name in {"customer_strategy", "content_plan", "full_draft", "pink_team_review", "red_team_review"} else "skeleton",
            source_text_length=source_text_length,
            requirement_count=requirement_count,
        )

    def _strategy_prompt(self) -> str:
        return (
            "You are building a customer strategy artifact for a facilities-management proposal package. "
            "Use only grounded solicitation details and approved company assets supplied in the payload. "
            "Return JSON only. Keep the strategy buyer-facing, specific, and aligned to evaluator priorities."
        )

    def _strategy_payload(self, workspace: dict[str, Any]) -> dict[str, Any]:
        return {
            "workspace": workspace,
            "apmp_topics": summarize_apmp_topics(),
            "approved_assets": self._runtime_asset_inventory(workspace["opportunity_id"]),
            **self._playbook_context(workspace["opportunity_id"]),
        }

    def _content_plan_prompt(self) -> str:
        return (
            "You are preparing a proposal content plan. Use the customer strategy, the approved asset inventory, "
            "and the solicitation requirements to create section briefs for a full package draft. "
            "Return JSON only and cite approved asset ids explicitly."
        )

    def _full_draft_prompt(self) -> str:
        return (
            "You are drafting a red-team-ready proposal package for a facilities-management and janitorial team. "
            "Use only the provided solicitation facts and approved assets. Do not mention internal process labels. "
            "Return JSON only with buyer-facing sections and separate internal notes."
        )

    def _review_prompt(self, review_stage: str) -> str:
        return (
            f"You are running a {review_stage.replace('_', ' ')} review over a proposal package. "
            "Use APMP-style rubric topics supplied in the payload. Return only structured findings with pass, needs_revision, or fail dispositions."
        )

    def _review_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "findings": {
                    "type": "array",
                    "items": ReviewFindingArtifact.model_json_schema(),
                }
            },
        }

    def _content_plan_schema(self) -> dict[str, Any]:
        return ContentPlanArtifact.model_json_schema()

    def _customer_strategy_schema(self) -> dict[str, Any]:
        return CustomerStrategyArtifact.model_json_schema()

    def _full_draft_schema(self) -> dict[str, Any]:
        return DraftStageArtifactResponse.model_json_schema()

    def _strategy_defaults(self, workspace: dict[str, Any]) -> CustomerStrategyArtifact:
        criteria = workspace.get("evaluation_criteria", [])
        win_themes = workspace.get("win_themes", [])
        buyer_priorities = [str(item.get("criterion", "")).strip() for item in criteria if str(item.get("criterion", "")).strip()]
        proof_assets = select_assets(
            asset_type="reference",
            tags=_workspace_tags(workspace),
            assets=self._runtime_asset_inventory(workspace["opportunity_id"]),
        )
        return CustomerStrategyArtifact(
            buyer_priorities=buyer_priorities[:5],
            strategic_positioning="Position the team as a low-risk, highly visible service operator with disciplined quality control and mobilization readiness.",
            bid_recommendation="Proceed with a controlled full-package run while validating staffing and pricing assumptions.",
            value_propositions=[
                {
                    "title": "Visible Operational Control",
                    "buyer_outcome": "Consistent facility presentation and rapid issue escalation.",
                    "differentiators": ["Visible supervision", "Daily QA routines", "Clear reporting"],
                    "supporting_requirement_codes": [row.get("requirement_code", "") for row in workspace.get("requirements_list", [])[:3]],
                    "supporting_asset_ids": [asset.id for asset in proof_assets[:1]],
                }
            ],
            proof_points=[
                {
                    "title": "Comparable High-Traffic Experience",
                    "statement": "Use approved airport and civic-facility references to support execution confidence.",
                    "supporting_asset_ids": [asset.id for asset in proof_assets[:2]],
                    "supporting_requirement_codes": [row.get("requirement_code", "") for row in workspace.get("requirements_list", [])[:2]],
                }
            ],
            win_theme_titles=[str(item.get("title", "")).strip() for item in win_themes if str(item.get("title", "")).strip()][:4],
            apmp_findings=[],
        )

    def _content_plan_defaults(self, workspace: dict[str, Any], strategy: CustomerStrategyArtifact) -> ContentPlanArtifact:
        approved_assets = select_assets(
            tags=_workspace_tags(workspace),
            assets=self._runtime_asset_inventory(workspace["opportunity_id"]),
        )
        asset_ids = [asset.id for asset in approved_assets]
        section_briefs = []
        for section_name in (
            "Cover Letter",
            "Executive Summary",
            "Technical Approach",
            "Management and Staffing Plan",
            "Transition and Mobilization Plan",
            "Quality Assurance and Reporting",
            "Past Performance and References",
            "Pricing Narrative",
            "Assumptions and Exceptions",
            "Compliance Appendix",
        ):
            section_briefs.append(
                {
                    "section_title": section_name,
                    "objective": f"Draft a strong {section_name.lower()} section grounded in the solicitation and approved content.",
                    "evaluator_priorities": strategy.buyer_priorities[:3],
                    "win_themes": strategy.win_theme_titles[:3],
                    "value_propositions": [item.title for item in strategy.value_propositions[:3]],
                    "proof_points": [item.title for item in strategy.proof_points[:3]],
                    "cited_requirement_codes": [row.get("requirement_code", "") for row in workspace.get("requirements_list", [])[:5]],
                    "approved_asset_ids": asset_ids[:6],
                    "required_graphics_or_actions": ["Add a visual staffing/oversight graphic." if "Management" in section_name else ""],
                    "drafting_instructions": [
                        "Keep the writing buyer-facing and specific.",
                        "Use only approved company assets and RFP facts.",
                    ],
                }
            )
        return ContentPlanArtifact(
            section_briefs=section_briefs,
            missing_asset_inputs=[],
            apmp_findings=[],
        )

    def _full_draft_defaults(self, workspace: dict[str, Any], content_plan: ContentPlanArtifact) -> DraftStageArtifactResponse:
        sections: list[DraftSectionArtifact] = []
        client_name = workspace.get("client_name", "the buyer")
        opportunity_name = workspace.get("opportunity_name", "this opportunity")
        criteria = ", ".join(item.get("criterion", "") for item in workspace.get("evaluation_criteria", [])[:4] if item.get("criterion"))
        for brief in content_plan.section_briefs:
            title = brief.section_title
            body = (
                f"{client_name} is seeking a reliable partner for {opportunity_name}. "
                f"This section addresses {criteria or 'the stated evaluation priorities'} with a disciplined, low-risk operating approach."
            )
            if title == "Technical Approach":
                body += "\n\n- Document daily service routines and issue escalation.\n- Tie quality control to inspection logs and responsive correction."
            elif title == "Management and Staffing Plan":
                body += "\n\n- Present supervisory coverage, account leadership, and staffing control.\n- Show how staffing remains aligned to site needs and service windows."
            elif title == "Transition and Mobilization Plan":
                body += "\n\n- Outline kickoff, onboarding, training, and early performance checkpoints."
            elif title == "Quality Assurance and Reporting":
                body += "\n\n- Explain inspection cadence, issue tracking, KPI reporting, and customer communication."
            elif title == "Past Performance and References":
                body += "\n\n- Use approved references to reinforce comparable public-facing facility experience."
            elif title == "Pricing Narrative":
                body += "\n\n- Connect commercial discipline to transparent staffing assumptions and workbook controls."
            elif title == "Assumptions and Exceptions":
                body += "\n\n- State unresolved assumptions plainly and avoid unsupported commitments."
            elif title == "Compliance Appendix":
                body += "\n\n- Summarize mandatory forms, insurance, and attachment readiness."
            sections.append(
                DraftSectionArtifact(
                    section_title=title,
                    body_markdown=body,
                    used_content_block_ids=brief.approved_asset_ids[:4],
                    cited_requirement_codes=brief.cited_requirement_codes[:6],
                )
            )
        return DraftStageArtifactResponse(
            draft_package=DraftPackageArtifact(
                sections=sections,
                client_sections=sections,
                internal_notes=[
                    "Review any unresolved staffing, pricing, and attachment assumptions before final production.",
                    "Insert named resumes, references, and local-office specifics from the approved library.",
                ],
                unresolved_items=workspace.get("document_gaps", []),
                editor_notes="Tighten differentiators, confirm attachments, and finalize forms before export.",
                used_content_block_ids=sorted({asset_id for section in sections for asset_id in section.used_content_block_ids}),
                cited_requirement_codes=sorted({code for section in sections for code in section.cited_requirement_codes}),
            ),
            warnings=[],
        )

    def _run_ai_structured_stage(
        self,
        *,
        workspace: dict[str, Any],
        stage_name: str,
        system_prompt: str,
        payload: dict[str, Any],
        schema_name: str,
        schema: dict[str, Any],
        reasoning_effort: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        client = self._ai_client(workspace, stage_name=stage_name)
        if not client.available:
            raise ProposalBuilderError("OPENAI_API_KEY is required for the full package engine.")
        requirement_count = len(workspace.get("requirements_list", []))
        source_text_length = len(json.dumps(payload, default=str))
        guardrails = self._builder()._stage_ai_guardrails(
            stage_name=stage_name,
            source_text_length=source_text_length,
            requirement_count=requirement_count,
        )
        try:
            return client.generate_json_with_metadata(
                system_prompt=system_prompt,
                user_payload=payload,
                schema_name=schema_name,
                schema=schema,
                reasoning_effort=reasoning_effort,
                background=True,
                poll_interval_seconds=4,
                max_wait_seconds=max(client.timeout_seconds * 6, 900),
                max_output_tokens=guardrails["max_output_tokens"],
                max_estimated_input_tokens=guardrails["max_estimated_input_tokens"],
                guardrail_label=stage_name,
            )
        except (OpenAIStructuredOutputError, ValueError) as exc:
            raise ProposalBuilderError(str(exc)) from exc

    def _load_workspace(self, opportunity_id: str) -> dict[str, Any]:
        return self._builder().get_workspace(opportunity_id).model_dump(mode="json")

    def _write_review_report(self, run_dir: Path, findings: list[ReviewFindingArtifact]) -> str:
        report_path = run_dir / "review-findings.md"
        lines = ["# Review Findings", ""]
        for finding in findings:
            lines.append(f"## {finding.review_stage}: {finding.title}")
            lines.append(f"- Severity: {finding.severity}")
            lines.append(f"- Disposition: {finding.disposition}")
            lines.append(f"- Recommendation: {finding.recommendation}")
            if finding.section_title:
                lines.append(f"- Section: {finding.section_title}")
            lines.append("")
        report_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
        return report_path.as_posix()

    def process_run(self, run_id: str, *, actor: str, start_stage_name: str | None = None) -> None:
        run = self.db.get(ProposalPackageRun, run_id)
        if run is None:
            return
        self._profile_service().apply_snapshot_to_run(run.opportunity_id, run)
        self.db.flush()
        start_index = self._stage_index(start_stage_name) if start_stage_name else 0
        workspace: dict[str, Any] | None = None
        customer_strategy: CustomerStrategyArtifact | None = (
            CustomerStrategyArtifact.model_validate(_parse_json(run.customer_strategy_json, {}))
            if run.customer_strategy_json
            else None
        )
        content_plan: ContentPlanArtifact | None = (
            ContentPlanArtifact.model_validate(_parse_json(run.content_plan_json, {}))
            if run.content_plan_json
            else None
        )
        review_findings = [ReviewFindingArtifact.model_validate(item) for item in _parse_json(run.review_findings_json, [])]

        for stage_name, approval_required, reasoning_profile in PACKAGE_STAGE_ORDER[start_index:]:
            stage = self._stage_row(run.id, stage_name)
            if stage.status == "COMPLETED" and (not approval_required or stage.approval_status == "APPROVED"):
                continue
            if stage_name == "export_package" and stage.approval_required and stage.approval_status != "APPROVED":
                run.status = "AWAITING_EXPORT_APPROVAL"
                run.current_stage = stage_name
                self.db.commit()
                return

            started_clock = self._mark_stage_in_progress(run, stage)
            opportunity_id = run.opportunity_id
            try:
                if workspace is None:
                    workspace = self._load_workspace(opportunity_id)

                if stage_name == "ingest":
                    solicitation = self._latest_solicitation(opportunity_id)
                    artifact = {
                        "opportunity_name": workspace["opportunity_name"],
                        "client_name": workspace["client_name"],
                        "source_filename": solicitation.source_filename if solicitation else "",
                    }
                    self._mark_stage_complete(run, stage, started_clock=started_clock, artifact=artifact, generation_mode="LIVE", generation_reason="system_orchestrated")

                elif stage_name == "extract_and_classify":
                    builder_run = self._builder().run_extract_stage(opportunity_id, actor=actor)
                    run.proposal_builder_run_id = builder_run.id
                    workspace = self._load_workspace(opportunity_id)
                    artifact = {
                        "opportunity_summary": builder_run.opportunity_summary.model_dump() if builder_run.opportunity_summary else {},
                        "document_gaps": builder_run.document_gaps,
                        "evaluation_criteria_count": len(builder_run.evaluation_criteria),
                    }
                    self._mark_stage_complete(
                        run,
                        stage,
                        started_clock=started_clock,
                        artifact=artifact,
                        warnings=builder_run.warnings,
                        generation_mode=builder_run.generation_mode,
                        generation_reason=builder_run.generation_reason,
                        model_name=builder_run.model_name,
                    )

                elif stage_name == "compliance_and_submission_map":
                    builder_run = self._builder().run_skeleton_stage(opportunity_id, actor=actor)
                    run.proposal_builder_run_id = builder_run.id
                    workspace = self._load_workspace(opportunity_id)
                    unmapped = [row for row in workspace.get("compliance_matrix", []) if row.get("status") == "UNMAPPED"]
                    blockers = ["Some requirements are still unmapped in the compliance matrix."] if unmapped else []
                    artifact = {
                        "outline_sections": [section.get("proposal_section", "") for section in (workspace.get("proposal_outline", {}) or {}).get("sections", [])],
                        "win_theme_titles": [item.get("title", "") for item in workspace.get("win_themes", [])],
                        "unmapped_requirements": len(unmapped),
                    }
                    self._mark_stage_complete(
                        run,
                        stage,
                        started_clock=started_clock,
                        artifact=artifact,
                        warnings=builder_run.warnings,
                        blockers=blockers,
                        generation_mode=builder_run.generation_mode,
                        generation_reason=builder_run.generation_reason,
                        model_name=builder_run.model_name,
                    )

                elif stage_name == "customer_strategy":
                    parsed, metadata = self._run_ai_structured_stage(
                        workspace=workspace,
                        stage_name=stage_name,
                        system_prompt=self._strategy_prompt(),
                        payload=self._strategy_payload(workspace),
                        schema_name="proposal_package_customer_strategy",
                        schema=self._customer_strategy_schema(),
                        reasoning_effort=reasoning_profile or "high",
                    )
                    customer_strategy = CustomerStrategyArtifact.model_validate(parsed)
                    customer_strategy.apmp_findings = apmp_findings_for_gaps(stage_name=stage_name, gaps=workspace.get("document_gaps", []))
                    run.customer_strategy_json = _dump_json(customer_strategy.model_dump())
                    self._mark_stage_complete(
                        run,
                        stage,
                        started_clock=started_clock,
                        artifact=customer_strategy.model_dump(),
                        token_usage=metadata.get("usage", {}),
                        input_sources=["workspace", "apmp_topics", "approved_assets"],
                        generation_mode="LIVE",
                        generation_reason="live_model_background",
                        model_name=self._ai_client(workspace, stage_name=stage_name).model,
                        response_id=str(metadata.get("response_id") or ""),
                    )

                elif stage_name == "content_plan":
                    if customer_strategy is None:
                        raise ProposalBuilderError("Customer strategy must exist before content planning.")
                    tags = _workspace_tags(workspace)
                    runtime_assets = self._runtime_asset_inventory(opportunity_id)
                    playbook_context = self._playbook_context(opportunity_id)
                    asset_blockers = required_asset_blockers(tags=tags, assets=runtime_assets)
                    if asset_blockers:
                        content_plan = self._content_plan_defaults(workspace, customer_strategy)
                        content_plan.missing_asset_inputs = asset_blockers
                        content_plan.apmp_findings = apmp_findings_for_gaps(stage_name=stage_name, gaps=asset_blockers)
                        run.content_plan_json = _dump_json(content_plan.model_dump())
                        self._mark_stage_completed_with_gaps(
                            run,
                            stage,
                            started_clock=started_clock,
                            message="The content plan used safe defaults because approved client content is still missing.",
                            artifact=content_plan.model_dump(),
                            blockers=asset_blockers,
                            generation_mode="FALLBACK_SAMPLE",
                            generation_reason="content_plan_defaults_missing_assets",
                        )
                    else:
                        parsed, metadata = self._run_ai_structured_stage(
                            workspace=workspace,
                            stage_name=stage_name,
                            system_prompt=self._content_plan_prompt(),
                            payload={
                                "workspace": workspace,
                                "customer_strategy": customer_strategy.model_dump(),
                                "approved_assets": runtime_assets,
                                **playbook_context,
                                "apmp_topics": summarize_apmp_topics(),
                            },
                            schema_name="proposal_package_content_plan",
                            schema=self._content_plan_schema(),
                            reasoning_effort=reasoning_profile or "high",
                        )
                        content_plan = ContentPlanArtifact.model_validate(parsed)
                        run.content_plan_json = _dump_json(content_plan.model_dump())
                        if content_plan.missing_asset_inputs:
                            self._mark_stage_completed_with_gaps(
                                run,
                                stage,
                                started_clock=started_clock,
                                message="The content plan was built, but it still needs more approved client material.",
                                artifact=content_plan.model_dump(),
                                blockers=content_plan.missing_asset_inputs,
                                token_usage=metadata.get("usage", {}),
                                input_sources=["workspace", "customer_strategy", "approved_assets", "client_playbook", "apmp_topics"],
                                generation_mode="LIVE",
                                generation_reason="live_model_background",
                                model_name=self._ai_client(workspace, stage_name=stage_name).model,
                                response_id=str(metadata.get("response_id") or ""),
                            )
                        else:
                            self._mark_stage_complete(
                                run,
                                stage,
                                started_clock=started_clock,
                                artifact=content_plan.model_dump(),
                                blockers=content_plan.missing_asset_inputs,
                                token_usage=metadata.get("usage", {}),
                                input_sources=["workspace", "customer_strategy", "approved_assets", "client_playbook", "apmp_topics"],
                                generation_mode="LIVE",
                                generation_reason="live_model_background",
                                model_name=self._ai_client(workspace, stage_name=stage_name).model,
                                response_id=str(metadata.get("response_id") or ""),
                            )

                elif stage_name == "full_draft":
                    if content_plan is None:
                        raise ProposalBuilderError("Content plan must exist before drafting.")
                    runtime_assets = self._runtime_asset_inventory(opportunity_id)
                    playbook_context = self._playbook_context(opportunity_id)
                    parsed, metadata = self._run_ai_structured_stage(
                        workspace=workspace,
                        stage_name=stage_name,
                        system_prompt=self._full_draft_prompt(),
                        payload={
                            "workspace": workspace,
                            "customer_strategy": customer_strategy.model_dump() if customer_strategy else {},
                            "content_plan": content_plan.model_dump(),
                            "approved_assets": runtime_assets,
                            **playbook_context,
                        },
                        schema_name="proposal_package_full_draft",
                        schema=self._full_draft_schema(),
                        reasoning_effort=reasoning_profile or "high",
                    )
                    draft_response = DraftStageArtifactResponse.model_validate(parsed)
                    latest_builder_run = self._latest_builder_run(opportunity_id)
                    if latest_builder_run is not None:
                        latest_builder_run.draft_package_json = _dump_json(draft_response.draft_package.model_dump())
                        latest_builder_run.status = "DRAFT_READY"
                        run.proposal_builder_run_id = latest_builder_run.id
                        self.db.flush()
                    self._mark_stage_complete(
                        run,
                        stage,
                        started_clock=started_clock,
                        artifact=draft_response.draft_package.model_dump(),
                        warnings=draft_response.warnings,
                        blockers=draft_response.draft_package.unresolved_items,
                        token_usage=metadata.get("usage", {}),
                        input_sources=["workspace", "customer_strategy", "content_plan", "approved_assets", "client_playbook"],
                        generation_mode="LIVE",
                        generation_reason="live_model_background",
                        model_name=self._ai_client(workspace, stage_name=stage_name).model,
                        response_id=str(metadata.get("response_id") or ""),
                    )
                    workspace = self._load_workspace(opportunity_id)

                elif stage_name == "pricing":
                    proposal_config = self._profile_service().opportunity_config(opportunity_id)
                    selected_pricing_model = self._profile_service().selected_pricing_model(opportunity_id)
                    demo_allows_draft_pricing = self._allow_draft_pricing_model_in_demo(run, selected_pricing_model)
                    stage_warnings: list[str] = []
                    config_blockers: list[str] = []
                    if proposal_config.client_profile_id and any("pricing model" in item.lower() for item in proposal_config.validation_errors):
                        if demo_allows_draft_pricing and selected_pricing_model is not None and selected_pricing_model.status != "APPROVED":
                            stage_warnings.append(
                                f"Testing mode used draft pricing model '{selected_pricing_model.name}'. Approve it before live client use."
                            )
                        else:
                            config_blockers.extend(proposal_config.validation_errors)
                            if selected_pricing_model is not None:
                                stage_warnings.append(
                                    f"The selected client pricing model '{selected_pricing_model.name}' is not approved. Pricing stayed in draft mode so the package could keep moving."
                                )
                            else:
                                stage_warnings.append(
                                    "No approved client pricing model was configured. The package used the safest available pricing defaults so work could continue."
                                )
                    pricing_package = build_pricing_package(
                        workspace=workspace,
                        target_dir=self._run_dir(run) / "pricing",
                        pricing_model=selected_pricing_model.model_dump(mode="json") if selected_pricing_model else None,
                        approved_assets=self._runtime_asset_inventory(opportunity_id),
                    )
                    run.pricing_package_json = _dump_json(pricing_package.model_dump())
                    blockers = list(dict.fromkeys(config_blockers + pricing_package.unresolved_pricing_blockers + pricing_package.validation_errors))
                    if blockers:
                        self._mark_stage_completed_with_gaps(
                            run,
                            stage,
                            started_clock=started_clock,
                            message="Pricing was built with visible gaps. Review the assumptions and missing inputs before using it as final.",
                            artifact=pricing_package.model_dump(),
                            warnings=stage_warnings,
                            blockers=blockers,
                            generation_mode="LIVE",
                            generation_reason="deterministic_pricing_partial",
                            waiting_for_approval=True,
                        )
                    else:
                        self._mark_stage_complete(
                            run,
                            stage,
                            started_clock=started_clock,
                            artifact=pricing_package.model_dump(),
                            warnings=stage_warnings,
                            generation_mode="LIVE",
                            generation_reason="deterministic_pricing",
                            waiting_for_approval=True,
                        )
                    run.status = "AWAITING_PRICING_APPROVAL"
                    run.current_stage = stage_name
                    self.db.commit()
                    return

                elif stage_name == "forms_and_attachments":
                    pricing_package = PricingPackageArtifact.model_validate(_parse_json(run.pricing_package_json, {}))
                    form_package = build_form_package(
                        workspace=workspace,
                        pricing_package=pricing_package,
                        target_dir=self._run_dir(run) / "forms",
                        approved_assets=self._runtime_asset_inventory(opportunity_id),
                        form_templates=self._runtime_form_templates(opportunity_id),
                    )
                    run.form_package_json = _dump_json(form_package.model_dump())
                    if form_package.blocked_forms:
                        self._mark_stage_completed_with_gaps(
                            run,
                            stage,
                            started_clock=started_clock,
                            message="Forms and attachments were built as far as possible, but some required source material is still missing.",
                            artifact=form_package.model_dump(),
                            warnings=form_package.unresolved_field_map_gaps,
                            blockers=form_package.blocked_forms,
                            generation_mode="LIVE",
                            generation_reason="deterministic_forms_partial",
                        )
                    else:
                        self._mark_stage_complete(
                            run,
                            stage,
                            started_clock=started_clock,
                            artifact=form_package.model_dump(),
                            warnings=form_package.unresolved_field_map_gaps,
                            generation_mode="LIVE",
                            generation_reason="deterministic_forms",
                        )

                elif stage_name in {"pink_team_review", "red_team_review", "gold_team_production_review"}:
                    if content_plan is None:
                        raise ProposalBuilderError("Content plan must exist before review.")
                    playbook_context = self._playbook_context(opportunity_id)
                    parsed, metadata = self._run_ai_structured_stage(
                        workspace=workspace,
                        stage_name=stage_name,
                        system_prompt=self._review_prompt(stage_name),
                        payload={
                            "workspace": workspace,
                            "customer_strategy": customer_strategy.model_dump() if customer_strategy else {},
                            "content_plan": content_plan.model_dump(),
                            **playbook_context,
                            "apmp_topics": summarize_apmp_topics(),
                            "stage_name": stage_name,
                        },
                        schema_name=f"proposal_package_{stage_name}",
                        schema=self._review_schema(),
                        reasoning_effort=reasoning_profile or "high",
                    )
                    findings = [ReviewFindingArtifact.model_validate(item) for item in parsed.get("findings", [])]
                    review_findings.extend(findings)
                    run.review_findings_json = _dump_json([item.model_dump() for item in review_findings])
                    hard_fails = [finding for finding in findings if finding.disposition == "fail"]
                    if hard_fails:
                        self._mark_stage_completed_with_gaps(
                            run,
                            stage,
                            started_clock=started_clock,
                            message=f"{stage_name.replace('_', ' ').title()} found important gaps, but the package kept moving.",
                            artifact={"findings": [item.model_dump() for item in findings]},
                            warnings=[finding.recommendation for finding in findings if finding.disposition == "needs_revision"],
                            blockers=[finding.recommendation for finding in hard_fails],
                            token_usage=metadata.get("usage", {}),
                            input_sources=["workspace", "customer_strategy", "content_plan", "client_playbook", "apmp_topics"],
                            generation_mode="LIVE",
                            generation_reason="live_model_background_review_gaps",
                            model_name=self._ai_client(workspace, stage_name=stage_name).model,
                            response_id=str(metadata.get("response_id") or ""),
                        )
                    else:
                        self._mark_stage_complete(
                            run,
                            stage,
                            started_clock=started_clock,
                            artifact={"findings": [item.model_dump() for item in findings]},
                            warnings=[finding.recommendation for finding in findings if finding.disposition == "needs_revision"],
                            token_usage=metadata.get("usage", {}),
                            input_sources=["workspace", "customer_strategy", "content_plan", "client_playbook", "apmp_topics"],
                            generation_mode="LIVE",
                            generation_reason="live_model_background",
                            model_name=self._ai_client(workspace, stage_name=stage_name).model,
                            response_id=str(metadata.get("response_id") or ""),
                        )

                elif stage_name == "export_package":
                    proposal_config = self._profile_service().opportunity_config(opportunity_id)
                    selected_template = self._profile_service().selected_proposal_template(opportunity_id)
                    demo_allows_draft_template = self._allow_draft_template_in_demo(run, selected_template)
                    stage_warnings = []
                    config_blockers: list[str] = []
                    export_template_payload = selected_template.model_dump(mode="json") if selected_template else None
                    if proposal_config.client_profile_id and any("template" in item.lower() for item in proposal_config.validation_errors):
                        if demo_allows_draft_template and selected_template is not None and selected_template.status != "APPROVED":
                            stage_warnings.append(
                                f"Testing mode used draft proposal template '{selected_template.name}'. Approve it before live client use."
                            )
                        else:
                            config_blockers.extend(proposal_config.validation_errors)
                            export_template_payload = None
                            if selected_template is not None:
                                stage_warnings.append(
                                    f"The selected client proposal template '{selected_template.name}' is not approved. The standard export shell was used so the package could finish."
                                )
                            else:
                                stage_warnings.append(
                                    "No approved client proposal template was configured. The standard export shell was used so the package could finish."
                                )
                    export_manifest = build_proposal_package_export_bundle(
                        workspace=workspace,
                        package_run=self._serialize_run(run).model_dump(mode="json"),
                        target_dir=self._run_dir(run) / "export",
                        proposal_template=export_template_payload,
                    )
                    run.package_export_manifest_json = _dump_json(export_manifest)
                    package_artifacts = _parse_json(run.package_artifacts_json, {})
                    package_artifacts["review_report_path"] = self._write_review_report(self._run_dir(run) / "export", review_findings)
                    run.package_artifacts_json = _dump_json(package_artifacts)
                    if config_blockers:
                        self._mark_stage_completed_with_gaps(
                            run,
                            stage,
                            started_clock=started_clock,
                            message="The package exported successfully, but it fell back to the standard shell because the client template setup is still incomplete.",
                            artifact=export_manifest,
                            warnings=stage_warnings,
                            blockers=config_blockers,
                            generation_mode="LIVE",
                            generation_reason="package_export_ready_with_fallback",
                        )
                    else:
                        self._mark_stage_complete(
                            run,
                            stage,
                            started_clock=started_clock,
                            artifact=export_manifest,
                            warnings=stage_warnings,
                            generation_mode="LIVE",
                            generation_reason="package_export_ready",
                        )
                    run.status = "COMPLETED"
                    run.current_stage = stage_name
                    run.completed_at = datetime.now(UTC).replace(tzinfo=None)

                else:
                    raise ProposalBuilderError(f"Unhandled package stage '{stage_name}'.")

                log_audit_event(
                    self.db,
                    opportunity_id=opportunity_id,
                    actor=actor,
                    action=f"proposal_package_stage_{stage_name}_completed",
                    after_state_json=_dump_json({"run_id": run.id, "stage_name": stage_name, "status": stage.status}),
                )
                self.db.commit()
                self.db.refresh(run)
            except Exception as exc:
                self._mark_stage_failed(run, stage, started_clock=started_clock, message=str(exc), blockers=[str(exc)])
                self.db.commit()
                return

        run.status = "COMPLETED"
        run.completed_at = datetime.now(UTC).replace(tzinfo=None)
        self.db.commit()

    def get_artifact_download_path(self, opportunity_id: str, run_id: str, kind: str) -> tuple[Path, str] | None:
        run = self.get_run(opportunity_id, run_id)
        manifest = run.export_manifest
        if manifest is None:
            return None
        artifact_map = {
            "proposal_docx": (manifest.client_docx_path, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            "support_bundle": (manifest.support_bundle_zip_path, "application/zip"),
            "markdown": (manifest.markdown_path, "text/markdown"),
            "json": (manifest.json_path, "application/json"),
            "pricing_workbook": (
                run.pricing_package.workbook_path if run.pricing_package else "",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
            "forms_bundle": (
                next((item.path for item in (run.form_package.completed_forms if run.form_package else []) if item.label == "Completed Forms Bundle"), ""),
                "application/zip",
            ),
        }
        path_info = artifact_map.get(kind)
        if not path_info or not path_info[0]:
            return None
        return Path(path_info[0]), path_info[1]


def run_package_background(run_id: str, actor: str, start_stage_name: str | None = None) -> None:
    db = SessionLocal()
    try:
        ProposalPackageService(db).process_run(run_id, actor=actor, start_stage_name=start_stage_name)
    finally:
        db.close()


def launch_package_background(run_id: str, actor: str, start_stage_name: str | None = None) -> None:
    worker = threading.Thread(
        target=run_package_background,
        args=(run_id, actor, start_stage_name),
        name=f"proposal-package-{run_id[:8]}",
        daemon=True,
    )
    worker.start()
