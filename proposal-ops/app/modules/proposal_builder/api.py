from __future__ import annotations

import html
import json
import re
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import BOSSKEY_ENABLE_COLOR_TEAM_REVIEWS
from app.core.db import get_db
from app.modules.proposal_builder.client_profiles import ClientProfileError, ClientProfileService
from app.modules.proposal_builder.onboarding import ClientOnboardingError, ClientOnboardingService
from app.modules.proposal_builder.schemas import (
    ClientOnboardingPackActionRequest,
    ClientOnboardingPackApproveRequest,
    ClientOnboardingPackCreateRequest,
    ClientOnboardingPackResponse,
    ClientOnboardingPackUploadResponse,
    ClientOnboardingAssetUpdateRequest,
    ClientPricingModelCreateRequest,
    ClientPricingModelResponse,
    ClientPlaybookUpdateRequest,
    ClientProfileCreateRequest,
    ClientProfileDefaultsRequest,
    ClientProfileResponse,
    ClientProposalTemplateResponse,
    ProposalBuilderRunResponse,
    ProposalBuilderSectionUpdateRequest,
    ProposalBuilderStageRequest,
    ProposalBuilderStartResult,
    ProposalBuilderWorkspaceResponse,
    OpportunityProposalConfigArtifact,
    OpportunityProposalConfigSelectionRequest,
    ProposalPackageRunCreateRequest,
    ProposalPackageRunResponse,
    ProposalPackageStageApprovalRequest,
)
from app.modules.proposal_builder.package_service import ProposalPackageService, launch_package_background
from app.modules.proposal_builder.service import ProposalBuilderError, ProposalBuilderService
from app.web.templating import build_templates


api_router = APIRouter(prefix="/api/opportunities", tags=["proposal-builder"])
admin_api_router = APIRouter(prefix="/api", tags=["client-profiles"])
web_router = APIRouter(tags=["web"])
templates = build_templates()
_ORDERED_LIST_PATTERN = re.compile(r"^\d+\.\s+")
_TABLE_SEPARATOR_PATTERN = re.compile(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$")

_PACKAGE_ENGINE_TRAIL = [
    {
        "key": "read_rfp",
        "label": "Read the RFP",
        "description": "Ingest files, extract the requirements, and map the checklist.",
        "stage_names": ["ingest", "extract_and_classify", "compliance_and_submission_map"],
        "color": "coral",
    },
    {
        "key": "shape_response",
        "label": "Shape the response",
        "description": "Build strategy, structure the response, and plan the sections.",
        "stage_names": ["customer_strategy", "content_plan"],
        "color": "berry",
    },
    {
        "key": "draft_package",
        "label": "Draft the package",
        "description": "Write the proposal package from the approved context.",
        "stage_names": ["full_draft"],
        "color": "sky",
    },
    {
        "key": "pricing_forms",
        "label": "Prepare pricing and forms",
        "description": "Assemble pricing, forms, and required submission files.",
        "stage_names": ["pricing", "forms_and_attachments"],
        "color": "gold",
    },
    {
        "key": "export_files",
        "label": "Build final files",
        "description": "Generate the final download package and export files.",
        "stage_names": ["export_package"],
        "color": "forest",
    },
]

if BOSSKEY_ENABLE_COLOR_TEAM_REVIEWS:
    _PACKAGE_ENGINE_TRAIL.insert(
        4,
        {
            "key": "quality_check",
            "label": "Quality check",
            "description": "Run the color-team review cycle before final export.",
            "stage_names": ["pink_team_review", "red_team_review", "gold_team_production_review"],
            "color": "plum",
        },
    )


async def _read_uploads(files: list[UploadFile] | None) -> list[tuple[str, bytes]]:
    payloads: list[tuple[str, bytes]] = []
    for file in files or []:
        payloads.append((file.filename or "uploaded-rfp.txt", await file.read()))
    return payloads


def _split_csv_values(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def _friendly_stage_name(stage_name: str | None) -> str:
    if not stage_name:
        return "Starting up"
    return stage_name.replace("_", " ").title()


def _stage_is_complete(stage) -> bool:
    if stage is None or stage.status not in {"COMPLETED", "COMPLETED_WITH_GAPS"}:
        return False
    if stage.approval_required:
        return stage.approval_status == "APPROVED"
    return True


def _build_package_stage_trail(package_run: ProposalPackageRunResponse | None) -> tuple[list[dict[str, str | bool]], str | None]:
    stage_lookup = {stage.stage_name: stage for stage in package_run.stages} if package_run else {}
    trail: list[dict[str, str | bool]] = []
    highlighted = False
    for group in _PACKAGE_ENGINE_TRAIL:
        members = [stage_lookup.get(name) for name in group["stage_names"]]
        current_in_group = bool(package_run and package_run.current_stage in group["stage_names"])
        blocked_in_group = any(stage and stage.status == "FAILED" for stage in members)
        completed_with_gaps = any(stage and stage.status == "COMPLETED_WITH_GAPS" for stage in members)
        waiting_approval = any(
            stage and stage.status == "AWAITING_APPROVAL" and (stage.approval_status or "PENDING") == "PENDING"
            for stage in members
        )
        running_in_group = any(stage and stage.status in {"QUEUED", "IN_PROGRESS"} for stage in members)
        completed = bool(members) and all(_stage_is_complete(stage) for stage in members)
        state = "future"
        detail = "Waiting"
        if package_run is None:
            state = "future"
            detail = "Waiting to start"
        elif blocked_in_group or (package_run.status == "BLOCKED" and current_in_group):
            state = "blocked"
            detail = "Needs more input"
            highlighted = True
        elif waiting_approval or (
            current_in_group and package_run.status in {"AWAITING_PRICING_APPROVAL", "AWAITING_EXPORT_APPROVAL"}
        ):
            state = "needs_attention"
            detail = "Needs your approval"
            highlighted = True
        elif current_in_group or running_in_group or (package_run.status in {"QUEUED", "IN_PROGRESS"} and not highlighted and not completed):
            state = "active"
            detail = f"Working now: {_friendly_stage_name(package_run.current_stage)}" if current_in_group else "Working now"
            highlighted = True
        elif completed:
            state = "complete"
            detail = "Built with gaps" if completed_with_gaps else "Done"
        trail.append(
            {
                "key": group["key"],
                "label": group["label"],
                "description": group["description"],
                "color": group["color"],
                "state": state,
                "detail": detail,
                "is_current": current_in_group,
            }
        )
    if package_run is None:
        trail[0]["state"] = "up_next"
        trail[0]["detail"] = "Start here"
    elif not highlighted:
        first_open = next((item for item in trail if item["state"] == "future"), None)
        if first_open is not None:
            first_open["state"] = "up_next"
            first_open["detail"] = "Up next"
    current_detail = None
    active_item = next((item for item in trail if item["state"] == "active"), None)
    if active_item is not None:
        current_detail = f"{active_item['label']}: {active_item['detail']}"
    else:
        attention_item = next((item for item in trail if item["state"] in {"needs_attention", "blocked"}), None)
        if attention_item is not None:
            current_detail = f"{attention_item['label']}: {attention_item['detail']}"
    return trail, current_detail


def _format_preview_inline(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"`(.+?)`", r"<code>\1</code>", escaped)
    return escaped


def _table_cells(line: str) -> list[str]:
    stripped = line.strip().strip("|")
    return [cell.strip() for cell in stripped.split("|")]


def _render_markdownish_preview(body: str) -> str:
    lines = body.splitlines()
    rendered: list[str] = []
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped:
            index += 1
            continue
        if stripped.startswith("### "):
            rendered.append(f"<h3>{_format_preview_inline(stripped[4:].strip())}</h3>")
            index += 1
            continue
        if stripped.startswith("- "):
            items: list[str] = []
            while index < len(lines) and lines[index].strip().startswith("- "):
                items.append(lines[index].strip()[2:].strip())
                index += 1
            rendered.append(
                "<ul>" + "".join(f"<li>{_format_preview_inline(item)}</li>" for item in items) + "</ul>"
            )
            continue
        if _ORDERED_LIST_PATTERN.match(stripped):
            items = []
            while index < len(lines) and _ORDERED_LIST_PATTERN.match(lines[index].strip()):
                items.append(_ORDERED_LIST_PATTERN.sub("", lines[index].strip(), count=1).strip())
                index += 1
            rendered.append(
                "<ol>" + "".join(f"<li>{_format_preview_inline(item)}</li>" for item in items) + "</ol>"
            )
            continue
        if (
            "|" in stripped
            and index + 1 < len(lines)
            and _TABLE_SEPARATOR_PATTERN.match(lines[index + 1].strip())
        ):
            header_cells = _table_cells(stripped)
            index += 2
            row_cells: list[list[str]] = []
            while index < len(lines) and "|" in lines[index]:
                row_line = lines[index].strip()
                if not row_line:
                    break
                row_cells.append(_table_cells(row_line))
                index += 1
            rendered.append(
                "<table class=\"proposal-preview-table\"><thead><tr>"
                + "".join(f"<th>{_format_preview_inline(cell)}</th>" for cell in header_cells)
                + "</tr></thead><tbody>"
                + "".join(
                    "<tr>" + "".join(f"<td>{_format_preview_inline(cell)}</td>" for cell in row) + "</tr>"
                    for row in row_cells
                )
                + "</tbody></table>"
            )
            continue

        paragraph_lines = [stripped]
        index += 1
        while index < len(lines):
            next_line = lines[index].strip()
            if (
                not next_line
                or next_line.startswith("### ")
                or next_line.startswith("- ")
                or _ORDERED_LIST_PATTERN.match(next_line)
                or (
                    "|" in next_line
                    and index + 1 < len(lines)
                    and _TABLE_SEPARATOR_PATTERN.match(lines[index + 1].strip())
                )
            ):
                break
            paragraph_lines.append(next_line)
            index += 1
        rendered.append(f"<p>{_format_preview_inline(' '.join(paragraph_lines))}</p>")
    return "\n".join(rendered)


def _preview_sections(workspace: ProposalBuilderWorkspaceResponse) -> list[dict[str, object]]:
    return [
        {
            "index": index,
            "section_title": section.section_title,
            "body_markdown": section.body_markdown,
            "body_html": _render_markdownish_preview(section.body_markdown),
        }
        for index, section in enumerate(workspace.client_sections)
    ]


def _render_start_page(
    request: Request,
    *,
    errors: list[str] | None = None,
    form_data: dict | None = None,
    draft_id: str | None = None,
    suggested_name: str | None = None,
    suggested_client: str | None = None,
    warnings: list[str] | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="proposal_builder_start.html",
        context={
            "minimal_shell": True,
            "errors": errors or [],
            "warnings": warnings or [],
            "form_data": form_data or {},
            "draft_id": draft_id,
            "suggested_name": suggested_name or "",
            "suggested_client": suggested_client or "",
        },
        status_code=status_code,
    )


def _render_workspace(
    request: Request,
    *,
    workspace: ProposalBuilderWorkspaceResponse,
    package_run: ProposalPackageRunResponse | None = None,
    success_message: str | None = None,
    error_message: str | None = None,
) -> HTMLResponse:
    blocked_stage = None
    if package_run is not None and package_run.current_stage:
        blocked_stage = next((stage for stage in package_run.stages if stage.stage_name == package_run.current_stage), None)
    package_stage_trail, package_stage_trail_current = _build_package_stage_trail(package_run)
    blocked_review_stage = bool(
        BOSSKEY_ENABLE_COLOR_TEAM_REVIEWS
        and blocked_stage
        and package_run is not None
        and package_run.status == "BLOCKED"
        and blocked_stage.stage_name in {"pink_team_review", "red_team_review", "gold_team_production_review"}
    )
    return templates.TemplateResponse(
        request=request,
        name="proposal_builder_workspace.html",
        context={
            "minimal_shell": True,
            "workspace": workspace,
            "package_run": package_run,
            "package_stage_trail": package_stage_trail,
            "package_stage_trail_current": package_stage_trail_current,
            "blocked_stage": blocked_stage,
            "blocked_review_stage": blocked_review_stage,
            "success_message": success_message,
            "error_message": error_message,
        },
    )


def _render_preview(
    request: Request,
    *,
    workspace: ProposalBuilderWorkspaceResponse,
    package_run: ProposalPackageRunResponse | None = None,
    success_message: str | None = None,
    error_message: str | None = None,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="proposal_builder_preview.html",
        context={
            "minimal_shell": True,
            "workspace": workspace,
            "package_run": package_run,
            "preview_sections": _preview_sections(workspace),
            "success_message": success_message,
            "error_message": error_message,
        },
    )


def _render_client_profiles_page(
    request: Request,
    *,
    profiles: list[ClientProfileResponse],
    success_message: str | None = None,
    error_message: str | None = None,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="client_profiles.html",
        context={
            "minimal_shell": True,
            "profiles": profiles,
            "success_message": success_message,
            "error_message": error_message,
        },
    )


def _render_client_profile_detail(
    request: Request,
    *,
    profile: ClientProfileResponse,
    success_message: str | None = None,
    error_message: str | None = None,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="client_profile_detail.html",
        context={
            "minimal_shell": True,
            "profile": profile,
            "success_message": success_message,
            "error_message": error_message,
        },
    )


def _render_client_onboarding_page(
    request: Request,
    *,
    packs: list[ClientOnboardingPackResponse],
    success_message: str | None = None,
    error_message: str | None = None,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="client_onboarding.html",
        context={
            "minimal_shell": True,
            "packs": packs,
            "success_message": success_message,
            "error_message": error_message,
        },
    )


def _render_client_onboarding_detail(
    request: Request,
    *,
    pack: ClientOnboardingPackResponse,
    success_message: str | None = None,
    error_message: str | None = None,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="client_onboarding_detail.html",
        context={
            "minimal_shell": True,
            "pack": pack,
            "success_message": success_message,
            "error_message": error_message,
        },
    )


@api_router.get("/{opportunity_id}/proposal-builder", response_model=ProposalBuilderWorkspaceResponse)
def get_proposal_builder_workspace(
    opportunity_id: str, db: Session = Depends(get_db)
) -> ProposalBuilderWorkspaceResponse:
    service = ProposalBuilderService(db)
    try:
        return service.get_workspace(opportunity_id)
    except ProposalBuilderError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@api_router.post("/{opportunity_id}/proposal-package/runs", response_model=ProposalPackageRunResponse)
def start_proposal_package_run_api(
    opportunity_id: str,
    payload: ProposalPackageRunCreateRequest,
    db: Session = Depends(get_db),
) -> ProposalPackageRunResponse:
    service = ProposalPackageService(db)
    try:
        run = service.create_run(opportunity_id, payload)
    except ProposalBuilderError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    launch_package_background(run.id, payload.actor, None)
    return run


@api_router.get("/{opportunity_id}/proposal-package/runs/{run_id}", response_model=ProposalPackageRunResponse)
def get_proposal_package_run_api(
    opportunity_id: str,
    run_id: str,
    db: Session = Depends(get_db),
) -> ProposalPackageRunResponse:
    service = ProposalPackageService(db)
    try:
        return service.get_run(opportunity_id, run_id)
    except ProposalBuilderError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@api_router.post("/{opportunity_id}/proposal-package/runs/{run_id}/approve-stage", response_model=ProposalPackageRunResponse)
def approve_proposal_package_stage_api(
    opportunity_id: str,
    run_id: str,
    payload: ProposalPackageStageApprovalRequest,
    db: Session = Depends(get_db),
) -> ProposalPackageRunResponse:
    service = ProposalPackageService(db)
    try:
        run = service.approve_stage(opportunity_id, run_id, payload)
    except ProposalBuilderError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    launch_package_background(run.id, payload.actor, payload.stage_name)
    return run


@api_router.post("/{opportunity_id}/proposal-package/runs/{run_id}/rerun-stage", response_model=ProposalPackageRunResponse)
def rerun_proposal_package_stage_api(
    opportunity_id: str,
    run_id: str,
    payload: ProposalPackageStageApprovalRequest,
    db: Session = Depends(get_db),
) -> ProposalPackageRunResponse:
    service = ProposalPackageService(db)
    try:
        run = service.rerun_stage(opportunity_id, run_id, payload)
    except ProposalBuilderError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    launch_package_background(run.id, payload.actor, payload.stage_name)
    return run


@api_router.get("/{opportunity_id}/proposal-package/runs/{run_id}/artifacts/{kind}")
def download_proposal_package_artifact_api(
    opportunity_id: str,
    run_id: str,
    kind: str,
    db: Session = Depends(get_db),
) -> FileResponse:
    service = ProposalPackageService(db)
    resolved = service.get_artifact_download_path(opportunity_id, run_id, kind)
    if not resolved:
        raise HTTPException(status_code=404, detail="Requested package artifact is not available.")
    path, media_type = resolved
    if not path.exists():
        raise HTTPException(status_code=404, detail="Package artifact was not found on disk.")
    return FileResponse(path, media_type=media_type, filename=Path(path).name)


@api_router.post("/{opportunity_id}/proposal-builder/extract", response_model=ProposalBuilderRunResponse)
def run_extract_stage_api(
    opportunity_id: str, payload: ProposalBuilderStageRequest, db: Session = Depends(get_db)
) -> ProposalBuilderRunResponse:
    service = ProposalBuilderService(db)
    try:
        return service.run_extract_stage(opportunity_id, actor=payload.actor)
    except ProposalBuilderError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@api_router.post("/{opportunity_id}/proposal-builder/skeleton", response_model=ProposalBuilderRunResponse)
def run_skeleton_stage_api(
    opportunity_id: str, payload: ProposalBuilderStageRequest, db: Session = Depends(get_db)
) -> ProposalBuilderRunResponse:
    service = ProposalBuilderService(db)
    try:
        return service.run_skeleton_stage(opportunity_id, actor=payload.actor)
    except ProposalBuilderError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@api_router.post("/{opportunity_id}/proposal-builder/draft", response_model=ProposalBuilderRunResponse)
def run_draft_stage_api(
    opportunity_id: str, payload: ProposalBuilderStageRequest, db: Session = Depends(get_db)
) -> ProposalBuilderRunResponse:
    service = ProposalBuilderService(db)
    try:
        return service.run_draft_stage(opportunity_id, actor=payload.actor)
    except ProposalBuilderError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@api_router.post("/{opportunity_id}/proposal-builder/export", response_model=ProposalBuilderRunResponse)
def run_export_stage_api(
    opportunity_id: str, payload: ProposalBuilderStageRequest, db: Session = Depends(get_db)
) -> ProposalBuilderRunResponse:
    service = ProposalBuilderService(db)
    try:
        return service.run_export_stage(opportunity_id, actor=payload.actor)
    except ProposalBuilderError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@api_router.post("/{opportunity_id}/proposal-builder/sections/{section_index}", response_model=ProposalBuilderRunResponse)
def update_draft_section_api(
    opportunity_id: str,
    section_index: int,
    payload: ProposalBuilderSectionUpdateRequest,
    db: Session = Depends(get_db),
) -> ProposalBuilderRunResponse:
    service = ProposalBuilderService(db)
    try:
        return service.update_draft_section(
            opportunity_id,
            actor=payload.actor,
            section_index=section_index,
            body_markdown=payload.body_markdown,
        )
    except ProposalBuilderError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@api_router.post("/{opportunity_id}/proposal-builder/best-draft", response_model=ProposalBuilderRunResponse)
def build_presentable_artifact_api(
    opportunity_id: str, payload: ProposalBuilderStageRequest, db: Session = Depends(get_db)
) -> ProposalBuilderRunResponse:
    service = ProposalBuilderService(db)
    try:
        return service.build_presentable_artifact(opportunity_id, actor=payload.actor)
    except ProposalBuilderError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@api_router.get("/{opportunity_id}/proposal-builder/export/{kind}")
def download_export_artifact(opportunity_id: str, kind: str, db: Session = Depends(get_db)) -> FileResponse:
    service = ProposalBuilderService(db)
    resolved = service.get_export_download_path(opportunity_id, kind)
    if not resolved:
        raise HTTPException(status_code=404, detail="Requested export artifact is not available.")
    path, media_type = resolved
    if not path.exists():
        raise HTTPException(status_code=404, detail="Export artifact was not found on disk.")
    return FileResponse(path, media_type=media_type, filename=Path(path).name)


@admin_api_router.get("/client-profiles", response_model=list[ClientProfileResponse])
def list_client_profiles_api(db: Session = Depends(get_db)) -> list[ClientProfileResponse]:
    return ClientProfileService(db).list_profiles()


@admin_api_router.get("/client-profiles/{profile_id}", response_model=ClientProfileResponse)
def get_client_profile_api(profile_id: str, db: Session = Depends(get_db)) -> ClientProfileResponse:
    try:
        return ClientProfileService(db).get_profile(profile_id)
    except ClientProfileError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@admin_api_router.post("/client-profiles", response_model=ClientProfileResponse)
def create_client_profile_api(payload: ClientProfileCreateRequest, db: Session = Depends(get_db)) -> ClientProfileResponse:
    try:
        return ClientProfileService(db).create_profile(payload)
    except ClientProfileError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@admin_api_router.post("/client-profiles/{profile_id}/pricing-models/import", response_model=ClientPricingModelResponse)
async def import_client_pricing_model_api(
    profile_id: str,
    file: UploadFile = File(...),
    name: str | None = Form(None),
    db: Session = Depends(get_db),
) -> ClientPricingModelResponse:
    try:
        return ClientProfileService(db).import_pricing_model(
            profile_id,
            name=name,
            filename=file.filename or "pricing-model.xlsx",
            content=await file.read(),
        )
    except (ClientProfileError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@admin_api_router.post("/client-profiles/{profile_id}/pricing-models", response_model=ClientPricingModelResponse)
def create_client_pricing_model_api(
    profile_id: str,
    payload: ClientPricingModelCreateRequest,
    db: Session = Depends(get_db),
) -> ClientPricingModelResponse:
    try:
        return ClientProfileService(db).create_pricing_model(profile_id, payload)
    except ClientProfileError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@admin_api_router.post("/client-profiles/{profile_id}/proposal-templates", response_model=ClientProposalTemplateResponse)
async def upload_client_proposal_template_api(
    profile_id: str,
    file: UploadFile = File(...),
    name: str | None = Form(None),
    db: Session = Depends(get_db),
) -> ClientProposalTemplateResponse:
    try:
        return ClientProfileService(db).upload_proposal_template(
            profile_id,
            name=name,
            filename=file.filename or "proposal-template.docx",
            content=await file.read(),
        )
    except ClientProfileError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@admin_api_router.post("/client-profiles/{profile_id}/defaults", response_model=ClientProfileResponse)
def set_client_profile_defaults_api(
    profile_id: str,
    payload: ClientProfileDefaultsRequest,
    db: Session = Depends(get_db),
) -> ClientProfileResponse:
    try:
        return ClientProfileService(db).set_defaults(profile_id, payload)
    except ClientProfileError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@admin_api_router.get("/client-onboarding/packs", response_model=list[ClientOnboardingPackResponse])
def list_client_onboarding_packs_api(db: Session = Depends(get_db)) -> list[ClientOnboardingPackResponse]:
    return ClientOnboardingService(db).list_packs()


@admin_api_router.post("/client-onboarding/packs", response_model=ClientOnboardingPackUploadResponse)
async def create_client_onboarding_pack_api(
    actor: str = Form("admin"),
    pack_name: str = Form(""),
    client_display_name: str = Form(""),
    archive: UploadFile | None = File(None),
    files: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
) -> ClientOnboardingPackUploadResponse:
    service = ClientOnboardingService(db)
    try:
        archive_payload = None
        if archive is not None:
            archive_payload = (archive.filename or "client-onboarding-pack.zip", await archive.read())
        return service.create_pack(
            ClientOnboardingPackCreateRequest(
                actor=actor,
                pack_name=pack_name or None,
                client_display_name=client_display_name or None,
            ),
            archive=archive_payload,
            files=await _read_uploads(files),
        )
    except ClientOnboardingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@admin_api_router.get("/client-onboarding/packs/{pack_id}", response_model=ClientOnboardingPackResponse)
def get_client_onboarding_pack_api(pack_id: str, db: Session = Depends(get_db)) -> ClientOnboardingPackResponse:
    try:
        return ClientOnboardingService(db).get_pack(pack_id)
    except ClientOnboardingError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@admin_api_router.post("/client-onboarding/packs/{pack_id}/classify", response_model=ClientOnboardingPackResponse)
def classify_client_onboarding_pack_api(
    pack_id: str,
    payload: ClientOnboardingPackActionRequest,
    db: Session = Depends(get_db),
) -> ClientOnboardingPackResponse:
    try:
        return ClientOnboardingService(db).classify_pack(pack_id, payload)
    except ClientOnboardingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@admin_api_router.post("/client-onboarding/packs/{pack_id}/assets/{asset_id}", response_model=ClientOnboardingPackResponse)
def update_client_onboarding_asset_api(
    pack_id: str,
    asset_id: str,
    payload: ClientOnboardingAssetUpdateRequest,
    db: Session = Depends(get_db),
) -> ClientOnboardingPackResponse:
    try:
        return ClientOnboardingService(db).update_asset(pack_id, asset_id, payload)
    except ClientOnboardingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@admin_api_router.post("/client-onboarding/packs/{pack_id}/playbook", response_model=ClientOnboardingPackResponse)
def save_client_onboarding_playbook_api(
    pack_id: str,
    payload: ClientPlaybookUpdateRequest,
    db: Session = Depends(get_db),
) -> ClientOnboardingPackResponse:
    try:
        return ClientOnboardingService(db).save_playbook(pack_id, payload)
    except ClientOnboardingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@admin_api_router.post("/client-onboarding/packs/{pack_id}/approve", response_model=ClientOnboardingPackResponse)
def approve_client_onboarding_pack_api(
    pack_id: str,
    payload: ClientOnboardingPackApproveRequest,
    db: Session = Depends(get_db),
) -> ClientOnboardingPackResponse:
    try:
        return ClientOnboardingService(db).approve_pack(pack_id, payload)
    except ClientOnboardingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@admin_api_router.post("/client-onboarding/packs/{pack_id}/activate", response_model=ClientOnboardingPackResponse)
def activate_client_onboarding_pack_api(
    pack_id: str,
    payload: ClientOnboardingPackActionRequest,
    db: Session = Depends(get_db),
) -> ClientOnboardingPackResponse:
    try:
        return ClientOnboardingService(db).activate_pack(pack_id, payload)
    except ClientOnboardingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@admin_api_router.post("/opportunities/{opportunity_id}/proposal-config/select-profile", response_model=OpportunityProposalConfigArtifact)
def select_opportunity_profile_api(
    opportunity_id: str,
    payload: OpportunityProposalConfigSelectionRequest,
    db: Session = Depends(get_db),
) -> OpportunityProposalConfigArtifact:
    try:
        return ClientProfileService(db).select_profile(opportunity_id, payload)
    except ClientProfileError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@admin_api_router.post("/opportunities/{opportunity_id}/proposal-config/select-pricing-model", response_model=OpportunityProposalConfigArtifact)
def select_opportunity_pricing_model_api(
    opportunity_id: str,
    payload: OpportunityProposalConfigSelectionRequest,
    db: Session = Depends(get_db),
) -> OpportunityProposalConfigArtifact:
    try:
        return ClientProfileService(db).select_pricing_model(opportunity_id, payload)
    except ClientProfileError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@admin_api_router.post("/opportunities/{opportunity_id}/proposal-config/select-template", response_model=OpportunityProposalConfigArtifact)
def select_opportunity_template_api(
    opportunity_id: str,
    payload: OpportunityProposalConfigSelectionRequest,
    db: Session = Depends(get_db),
) -> OpportunityProposalConfigArtifact:
    try:
        return ClientProfileService(db).select_template(opportunity_id, payload)
    except ClientProfileError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@web_router.get("/proposal-builder", response_class=HTMLResponse)
def proposal_builder_start_page(request: Request) -> HTMLResponse:
    return _render_start_page(request)


@web_router.post("/proposal-builder/start")
async def proposal_builder_start(
    request: Request,
    actor: str = Form("operator"),
    raw_text: str = Form(""),
    raw_text_filename: str = Form("pasted-rfp.txt"),
    use_demo_sample: str = Form(""),
    files: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
):
    service = ProposalBuilderService(db)
    try:
        result = service.start_from_inputs(
            actor=actor,
            files=await _read_uploads(files),
            raw_text=raw_text,
            raw_text_filename=raw_text_filename,
            use_demo_sample=bool(use_demo_sample),
        )
    except ProposalBuilderError as exc:
        return _render_start_page(
            request,
            errors=[str(exc)],
            form_data={"actor": actor, "raw_text": raw_text, "raw_text_filename": raw_text_filename},
            status_code=422,
        )

    if result.needs_confirmation:
        return _render_start_page(
            request,
            errors=["Review the inferred name and client before continuing."],
            draft_id=result.draft_id,
            suggested_name=result.suggested_name,
            suggested_client=result.suggested_client,
            warnings=result.warnings,
        )
    return RedirectResponse(url=f"/opportunities/{result.opportunity_id}/proposal-builder", status_code=303)


@web_router.post("/proposal-builder/confirm")
def proposal_builder_confirm_start(
    request: Request,
    draft_id: str = Form(...),
    actor: str = Form("operator"),
    name: str = Form(...),
    client: str = Form(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = ProposalBuilderService(db)
    try:
        result = service.confirm_start(draft_id=draft_id, actor=actor, name=name, client=client)
    except ProposalBuilderError as exc:
        return _render_start_page(
            request,
            errors=[str(exc)],
            draft_id=draft_id,
            suggested_name=name,
            suggested_client=client,
            status_code=422,
        )
    return RedirectResponse(url=f"/opportunities/{result.opportunity_id}/proposal-builder", status_code=303)


@web_router.get("/opportunities/{opportunity_id}/proposal-builder", response_class=HTMLResponse)
def proposal_builder_workspace(
    request: Request, opportunity_id: str, db: Session = Depends(get_db)
) -> HTMLResponse:
    service = ProposalBuilderService(db)
    package_service = ProposalPackageService(db)
    try:
        workspace = service.get_workspace(opportunity_id)
    except ProposalBuilderError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _render_workspace(
        request,
        workspace=workspace,
        package_run=package_service.get_latest_run_response(opportunity_id),
    )


@web_router.get("/opportunities/{opportunity_id}/proposal-builder/preview", response_class=HTMLResponse)
def proposal_builder_preview_page(
    request: Request, opportunity_id: str, db: Session = Depends(get_db)
) -> HTMLResponse:
    service = ProposalBuilderService(db)
    package_service = ProposalPackageService(db)
    try:
        workspace = service.get_workspace(opportunity_id)
    except ProposalBuilderError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _render_preview(
        request,
        workspace=workspace,
        package_run=package_service.get_latest_run_response(opportunity_id),
    )


@web_router.get("/client-profiles", response_class=HTMLResponse)
def client_profiles_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    return _render_client_profiles_page(request, profiles=ClientProfileService(db).list_profiles())


@web_router.post("/client-profiles")
def create_client_profile_web(
    request: Request,
    display_name: str = Form(...),
    aliases: str = Form(""),
    approved_content_tags: str = Form(""),
    region_tags: str = Form(""),
    service_tags: str = Form(""),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = ClientProfileService(db)
    try:
        service.create_profile(
            ClientProfileCreateRequest(
                display_name=display_name,
                aliases=_split_csv_values(aliases),
                approved_content_tags=_split_csv_values(approved_content_tags),
                region_tags=_split_csv_values(region_tags),
                service_tags=_split_csv_values(service_tags),
            )
        )
        return _render_client_profiles_page(
            request,
            profiles=service.list_profiles(),
            success_message="Client profile created.",
        )
    except ClientProfileError as exc:
        return _render_client_profiles_page(request, profiles=service.list_profiles(), error_message=str(exc))


@web_router.get("/client-profiles/{profile_id}", response_class=HTMLResponse)
def client_profile_detail_page(request: Request, profile_id: str, db: Session = Depends(get_db)) -> HTMLResponse:
    service = ClientProfileService(db)
    try:
        profile = service.get_profile(profile_id)
    except ClientProfileError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _render_client_profile_detail(request, profile=profile)


@web_router.post("/client-profiles/{profile_id}/pricing-models/import")
async def import_client_pricing_model_web(
    request: Request,
    profile_id: str,
    name: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = ClientProfileService(db)
    try:
        service.import_pricing_model(
            profile_id,
            name=name or None,
            filename=file.filename or "pricing-model.xlsx",
            content=await file.read(),
        )
        profile = service.get_profile(profile_id)
        return _render_client_profile_detail(request, profile=profile, success_message="Pricing model imported.")
    except (ClientProfileError, json.JSONDecodeError) as exc:
        profile = service.get_profile(profile_id)
        return _render_client_profile_detail(request, profile=profile, error_message=str(exc))


@web_router.post("/client-profiles/{profile_id}/pricing-models")
def create_client_pricing_model_web(
    request: Request,
    profile_id: str,
    name: str = Form(...),
    assumptions: str = Form(""),
    service_tags: str = Form(""),
    region_tags: str = Form(""),
    site_multiplier: float = Form(1.0),
    continuous_coverage_multiplier: float = Form(1.35),
    labor_code: list[str] = Form([]),
    labor_label: list[str] = Form([]),
    labor_hourly_rate: list[str] = Form([]),
    labor_burden_factor: list[str] = Form([]),
    labor_markup_factor: list[str] = Form([]),
    labor_default_hours: list[str] = Form([]),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = ClientProfileService(db)
    labor_categories = []
    for index, code in enumerate(labor_code):
        if not code.strip():
            continue
        labor_categories.append(
            {
                "code": code,
                "label": labor_label[index] if index < len(labor_label) else code.replace("_", " ").title(),
                "hourly_rate": float(labor_hourly_rate[index] or 0),
                "burden_factor": float(labor_burden_factor[index] or 1),
                "markup_factor": float(labor_markup_factor[index] or 1),
                "default_hours_per_week": float(labor_default_hours[index] or 0),
            }
        )
    try:
        service.create_pricing_model(
            profile_id,
            ClientPricingModelCreateRequest(
                name=name,
                assumptions=_split_csv_values(assumptions),
                service_tags=_split_csv_values(service_tags),
                region_tags=_split_csv_values(region_tags),
                site_multiplier=site_multiplier,
                continuous_coverage_multiplier=continuous_coverage_multiplier,
                labor_categories=labor_categories,
            ),
        )
        profile = service.get_profile(profile_id)
        return _render_client_profile_detail(request, profile=profile, success_message="Pricing model created.")
    except (ClientProfileError, ValueError) as exc:
        profile = service.get_profile(profile_id)
        return _render_client_profile_detail(request, profile=profile, error_message=str(exc))


@web_router.post("/client-profiles/{profile_id}/proposal-templates")
async def upload_client_proposal_template_web(
    request: Request,
    profile_id: str,
    name: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = ClientProfileService(db)
    try:
        service.upload_proposal_template(
            profile_id,
            name=name or None,
            filename=file.filename or "proposal-template.docx",
            content=await file.read(),
        )
        profile = service.get_profile(profile_id)
        return _render_client_profile_detail(request, profile=profile, success_message="Proposal template uploaded.")
    except ClientProfileError as exc:
        profile = service.get_profile(profile_id)
        return _render_client_profile_detail(request, profile=profile, error_message=str(exc))


@web_router.post("/client-profiles/{profile_id}/defaults")
def set_client_profile_defaults_web(
    request: Request,
    profile_id: str,
    default_pricing_model_id: str = Form(""),
    default_proposal_template_id: str = Form(""),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = ClientProfileService(db)
    try:
        profile = service.set_defaults(
            profile_id,
            ClientProfileDefaultsRequest(
                default_pricing_model_id=default_pricing_model_id or None,
                default_proposal_template_id=default_proposal_template_id or None,
            ),
        )
        return _render_client_profile_detail(request, profile=profile, success_message="Client defaults updated.")
    except ClientProfileError as exc:
        profile = service.get_profile(profile_id)
        return _render_client_profile_detail(request, profile=profile, error_message=str(exc))


@web_router.get("/client-onboarding", response_class=HTMLResponse)
def client_onboarding_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    return _render_client_onboarding_page(request, packs=ClientOnboardingService(db).list_packs())


@web_router.post("/client-onboarding/packs")
async def create_client_onboarding_pack_web(
    request: Request,
    actor: str = Form("admin"),
    pack_name: str = Form(""),
    client_display_name: str = Form(""),
    archive: UploadFile | None = File(None),
    files: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = ClientOnboardingService(db)
    try:
        archive_payload = None
        if archive is not None:
            archive_payload = (archive.filename or "client-onboarding-pack.zip", await archive.read())
        result = service.create_pack(
            ClientOnboardingPackCreateRequest(
                actor=actor,
                pack_name=pack_name or None,
                client_display_name=client_display_name or None,
            ),
            archive=archive_payload,
            files=await _read_uploads(files),
        )
        return RedirectResponse(url=f"/client-onboarding/{result.pack.id}", status_code=303)
    except ClientOnboardingError as exc:
        return _render_client_onboarding_page(request, packs=service.list_packs(), error_message=str(exc))


@web_router.get("/client-onboarding/{pack_id}", response_class=HTMLResponse)
def client_onboarding_detail_page(request: Request, pack_id: str, db: Session = Depends(get_db)) -> HTMLResponse:
    service = ClientOnboardingService(db)
    try:
        pack = service.get_pack(pack_id)
    except ClientOnboardingError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _render_client_onboarding_detail(request, pack=pack)


@web_router.post("/client-onboarding/{pack_id}/classify")
def classify_client_onboarding_pack_web(
    request: Request,
    pack_id: str,
    actor: str = Form("admin"),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = ClientOnboardingService(db)
    try:
        pack = service.classify_pack(pack_id, ClientOnboardingPackActionRequest(actor=actor))
        return _render_client_onboarding_detail(request, pack=pack, success_message="Client pack reclassified.")
    except ClientOnboardingError as exc:
        pack = service.get_pack(pack_id)
        return _render_client_onboarding_detail(request, pack=pack, error_message=str(exc))


@web_router.post("/client-onboarding/{pack_id}/assets/{asset_id}")
def update_client_onboarding_asset_web(
    request: Request,
    pack_id: str,
    asset_id: str,
    actor: str = Form("admin"),
    asset_role: str = Form(...),
    asset_status: str = Form("CANDIDATE"),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = ClientOnboardingService(db)
    try:
        pack = service.update_asset(
            pack_id,
            asset_id,
            ClientOnboardingAssetUpdateRequest(actor=actor, asset_role=asset_role, asset_status=asset_status),
        )
        return _render_client_onboarding_detail(request, pack=pack, success_message="Asset classification updated.")
    except ClientOnboardingError as exc:
        pack = service.get_pack(pack_id)
        return _render_client_onboarding_detail(request, pack=pack, error_message=str(exc))


@web_router.post("/client-onboarding/{pack_id}/playbook")
def save_client_onboarding_playbook_web(
    request: Request,
    pack_id: str,
    actor: str = Form("admin"),
    title: str = Form(""),
    narrative_guidance_md: str = Form(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = ClientOnboardingService(db)
    try:
        pack = service.save_playbook(
            pack_id,
            ClientPlaybookUpdateRequest(
                actor=actor,
                title=title or None,
                narrative_guidance_md=narrative_guidance_md,
            ),
        )
        return _render_client_onboarding_detail(request, pack=pack, success_message="Playbook draft saved.")
    except ClientOnboardingError as exc:
        pack = service.get_pack(pack_id)
        return _render_client_onboarding_detail(request, pack=pack, error_message=str(exc))


@web_router.post("/client-onboarding/{pack_id}/approve")
def approve_client_onboarding_pack_web(
    request: Request,
    pack_id: str,
    actor: str = Form("admin"),
    narrative_guidance_md: str = Form(""),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = ClientOnboardingService(db)
    try:
        pack = service.approve_pack(
            pack_id,
            ClientOnboardingPackApproveRequest(
                actor=actor,
                narrative_guidance_md=narrative_guidance_md or None,
            ),
        )
        return _render_client_onboarding_detail(request, pack=pack, success_message="Playbook and defaults approved.")
    except ClientOnboardingError as exc:
        pack = service.get_pack(pack_id)
        return _render_client_onboarding_detail(request, pack=pack, error_message=str(exc))


@web_router.post("/client-onboarding/{pack_id}/activate")
def activate_client_onboarding_pack_web(
    request: Request,
    pack_id: str,
    actor: str = Form("admin"),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = ClientOnboardingService(db)
    try:
        pack = service.activate_pack(pack_id, ClientOnboardingPackActionRequest(actor=actor))
        return _render_client_onboarding_detail(request, pack=pack, success_message="Client environment activated.")
    except ClientOnboardingError as exc:
        pack = service.get_pack(pack_id)
        return _render_client_onboarding_detail(request, pack=pack, error_message=str(exc))


@web_router.post("/opportunities/{opportunity_id}/proposal-config/select-profile")
def select_opportunity_profile_web(
    request: Request,
    opportunity_id: str,
    actor: str = Form("operator"),
    target_id: str = Form(""),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    builder_service = ProposalBuilderService(db)
    package_service = ProposalPackageService(db)
    try:
        ClientProfileService(db).select_profile(
            opportunity_id, OpportunityProposalConfigSelectionRequest(actor=actor, target_id=target_id or None)
        )
        workspace = builder_service.get_workspace(opportunity_id)
        return _render_workspace(
            request,
            workspace=workspace,
            package_run=package_service.get_latest_run_response(opportunity_id),
            success_message="Client profile selection updated.",
        )
    except ClientProfileError as exc:
        workspace = builder_service.get_workspace(opportunity_id)
        return _render_workspace(
            request,
            workspace=workspace,
            package_run=package_service.get_latest_run_response(opportunity_id),
            error_message=str(exc),
        )


@web_router.post("/opportunities/{opportunity_id}/proposal-config/select-pricing-model")
def select_opportunity_pricing_model_web(
    request: Request,
    opportunity_id: str,
    actor: str = Form("operator"),
    target_id: str = Form(""),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    builder_service = ProposalBuilderService(db)
    package_service = ProposalPackageService(db)
    try:
        ClientProfileService(db).select_pricing_model(
            opportunity_id, OpportunityProposalConfigSelectionRequest(actor=actor, target_id=target_id or None)
        )
        workspace = builder_service.get_workspace(opportunity_id)
        return _render_workspace(
            request,
            workspace=workspace,
            package_run=package_service.get_latest_run_response(opportunity_id),
            success_message="Pricing model selection updated.",
        )
    except ClientProfileError as exc:
        workspace = builder_service.get_workspace(opportunity_id)
        return _render_workspace(
            request,
            workspace=workspace,
            package_run=package_service.get_latest_run_response(opportunity_id),
            error_message=str(exc),
        )


@web_router.post("/opportunities/{opportunity_id}/proposal-config/select-template")
def select_opportunity_template_web(
    request: Request,
    opportunity_id: str,
    actor: str = Form("operator"),
    target_id: str = Form(""),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    builder_service = ProposalBuilderService(db)
    package_service = ProposalPackageService(db)
    try:
        ClientProfileService(db).select_template(
            opportunity_id, OpportunityProposalConfigSelectionRequest(actor=actor, target_id=target_id or None)
        )
        workspace = builder_service.get_workspace(opportunity_id)
        return _render_workspace(
            request,
            workspace=workspace,
            package_run=package_service.get_latest_run_response(opportunity_id),
            success_message="Proposal template selection updated.",
        )
    except ClientProfileError as exc:
        workspace = builder_service.get_workspace(opportunity_id)
        return _render_workspace(
            request,
            workspace=workspace,
            package_run=package_service.get_latest_run_response(opportunity_id),
            error_message=str(exc),
        )


def _post_stage_redirect(
    request: Request,
    *,
    opportunity_id: str,
    actor: str,
    db: Session,
    stage_fn: str,
    success_message: str,
) -> HTMLResponse:
    service = ProposalBuilderService(db)
    package_service = ProposalPackageService(db)
    try:
        getattr(service, stage_fn)(opportunity_id, actor=actor)
        workspace = service.get_workspace(opportunity_id)
    except ProposalBuilderError as exc:
        workspace = service.get_workspace(opportunity_id)
        return _render_workspace(
            request,
            workspace=workspace,
            package_run=package_service.get_latest_run_response(opportunity_id),
            error_message=str(exc),
        )
    return _render_workspace(
        request,
        workspace=workspace,
        package_run=package_service.get_latest_run_response(opportunity_id),
        success_message=success_message,
    )


@web_router.post("/opportunities/{opportunity_id}/proposal-builder/extract")
def proposal_builder_extract_web(
    request: Request,
    opportunity_id: str,
    actor: str = Form("operator"),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    return _post_stage_redirect(
        request,
        opportunity_id=opportunity_id,
        actor=actor,
        db=db,
        stage_fn="run_extract_stage",
        success_message="Requirements review refreshed.",
    )


@web_router.post("/opportunities/{opportunity_id}/proposal-builder/skeleton")
def proposal_builder_skeleton_web(
    request: Request,
    opportunity_id: str,
    actor: str = Form("operator"),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    return _post_stage_redirect(
        request,
        opportunity_id=opportunity_id,
        actor=actor,
        db=db,
        stage_fn="run_skeleton_stage",
        success_message="Proposal skeleton and win themes updated.",
    )


@web_router.post("/opportunities/{opportunity_id}/proposal-builder/draft")
def proposal_builder_draft_web(
    request: Request,
    opportunity_id: str,
    actor: str = Form("operator"),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    return _post_stage_redirect(
        request,
        opportunity_id=opportunity_id,
        actor=actor,
        db=db,
        stage_fn="run_draft_stage",
        success_message="Draft sections generated.",
    )


@web_router.post("/opportunities/{opportunity_id}/proposal-builder/export")
def proposal_builder_export_web(
    request: Request,
    opportunity_id: str,
    actor: str = Form("operator"),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    return _post_stage_redirect(
        request,
        opportunity_id=opportunity_id,
        actor=actor,
        db=db,
        stage_fn="run_export_stage",
        success_message="Export bundle generated.",
    )


@web_router.post("/opportunities/{opportunity_id}/proposal-builder/preview/sections/{section_index}")
def proposal_builder_update_section_web(
    request: Request,
    opportunity_id: str,
    section_index: int,
    actor: str = Form("operator"),
    body_markdown: str = Form(""),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = ProposalBuilderService(db)
    package_service = ProposalPackageService(db)
    try:
        service.update_draft_section(
            opportunity_id,
            actor=actor,
            section_index=section_index,
            body_markdown=body_markdown,
        )
        workspace = service.get_workspace(opportunity_id)
        return _render_preview(
            request,
            workspace=workspace,
            package_run=package_service.get_latest_run_response(opportunity_id),
            success_message="Section changes saved. Refresh the Word draft when you are ready.",
        )
    except ProposalBuilderError as exc:
        workspace = service.get_workspace(opportunity_id)
        return _render_preview(
            request,
            workspace=workspace,
            package_run=package_service.get_latest_run_response(opportunity_id),
            error_message=str(exc),
        )


@web_router.post("/opportunities/{opportunity_id}/proposal-builder/best-draft")
def proposal_builder_best_draft_web(
    request: Request,
    opportunity_id: str,
    actor: str = Form("operator"),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    return _post_stage_redirect(
        request,
        opportunity_id=opportunity_id,
        actor=actor,
        db=db,
        stage_fn="build_presentable_artifact",
        success_message="Presentable Word draft generated.",
    )


@web_router.post("/opportunities/{opportunity_id}/proposal-builder/materials")
async def proposal_builder_materials_web(
    request: Request,
    opportunity_id: str,
    actor: str = Form("operator"),
    material_kind: str = Form("supporting material"),
    raw_text: str = Form(""),
    raw_text_filename: str = Form(""),
    files: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = ProposalBuilderService(db)
    package_service = ProposalPackageService(db)
    try:
        workspace = service.add_supporting_materials(
            opportunity_id,
            actor=actor,
            material_kind=material_kind,
            files=await _read_uploads(files),
            raw_text=raw_text,
            raw_text_filename=raw_text_filename,
        )
        return _render_workspace(
            request,
            workspace=workspace,
            package_run=package_service.get_latest_run_response(opportunity_id),
            success_message="New material added. The RFP summary and checklist were refreshed.",
        )
    except ProposalBuilderError as exc:
        workspace = service.get_workspace(opportunity_id)
        return _render_workspace(
            request,
            workspace=workspace,
            package_run=package_service.get_latest_run_response(opportunity_id),
            error_message=str(exc),
        )


@web_router.post("/opportunities/{opportunity_id}/proposal-package/start")
def proposal_package_start_web(
    request: Request,
    opportunity_id: str,
    actor: str = Form("operator"),
    demo_mode: bool = Form(False),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    builder_service = ProposalBuilderService(db)
    package_service = ProposalPackageService(db)
    try:
        run = package_service.create_run(
            opportunity_id,
            ProposalPackageRunCreateRequest(actor=actor, demo_mode=demo_mode),
        )
        launch_package_background(run.id, actor, None)
        return RedirectResponse(url=f"/opportunities/{opportunity_id}/proposal-builder", status_code=303)
    except ProposalBuilderError as exc:
        workspace = builder_service.get_workspace(opportunity_id)
        return _render_workspace(
            request,
            workspace=workspace,
            package_run=package_service.get_latest_run_response(opportunity_id),
            error_message=str(exc),
        )


@web_router.post("/opportunities/{opportunity_id}/proposal-package/{run_id}/approve-stage")
def proposal_package_approve_stage_web(
    request: Request,
    opportunity_id: str,
    run_id: str,
    actor: str = Form("operator"),
    stage_name: str = Form(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    builder_service = ProposalBuilderService(db)
    package_service = ProposalPackageService(db)
    try:
        run = package_service.approve_stage(
            opportunity_id,
            run_id,
            ProposalPackageStageApprovalRequest(actor=actor, stage_name=stage_name),
        )
        launch_package_background(run.id, actor, stage_name)
        return RedirectResponse(url=f"/opportunities/{opportunity_id}/proposal-builder", status_code=303)
    except ProposalBuilderError as exc:
        workspace = builder_service.get_workspace(opportunity_id)
        return _render_workspace(
            request,
            workspace=workspace,
            package_run=package_service.get_latest_run_response(opportunity_id),
            error_message=str(exc),
        )


@web_router.post("/opportunities/{opportunity_id}/proposal-package/{run_id}/rerun-stage")
def proposal_package_rerun_stage_web(
    request: Request,
    opportunity_id: str,
    run_id: str,
    actor: str = Form("operator"),
    stage_name: str = Form(...),
    demo_mode: bool = Form(False),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    builder_service = ProposalBuilderService(db)
    package_service = ProposalPackageService(db)
    try:
        run = package_service.rerun_stage(
            opportunity_id,
            run_id,
            ProposalPackageStageApprovalRequest(actor=actor, stage_name=stage_name, demo_mode=demo_mode),
        )
        launch_package_background(run.id, actor, stage_name)
        return RedirectResponse(url=f"/opportunities/{opportunity_id}/proposal-builder", status_code=303)
    except ProposalBuilderError as exc:
        workspace = builder_service.get_workspace(opportunity_id)
        return _render_workspace(
            request,
            workspace=workspace,
            package_run=package_service.get_latest_run_response(opportunity_id),
            error_message=str(exc),
        )
