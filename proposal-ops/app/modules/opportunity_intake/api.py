from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.session_auth import get_session_user
from app.core.workflow import active_gate_for_stage
from app.web.example_presets import select_example_presets
from app.web.templating import build_templates
from app.modules.identity.service import IdentityService
from app.modules.janitorial_os.service import JanitorialOsService
from app.modules.opportunity_intake.schemas import (
    ArchiveActionRequest,
    GateInboxItemResponse,
    GateDecisionRequest,
    GateDecisionResponse,
    OpportunityDetailResponse,
    OpportunityIntakeDraftConfirmRequest,
    OpportunityIntakeDraftResponse,
    OpportunityIntakeRequest,
    OpportunityIntakeResult,
    OpportunityIntakeWithRfpResult,
    StageTransitionRequest,
    StageTransitionResponse,
    WorkflowTimelineEventResponse,
)
from app.modules.opportunity_intake.service import OpportunityIntakeService
from app.modules.rfp_parser.document_reader import extract_text_from_upload_batch


api_router = APIRouter(prefix="/api/opportunities", tags=["opportunity-intake"])
web_router = APIRouter(tags=["web"])
templates = build_templates()


def _build_intake_payload(
    *,
    name: str,
    client: str,
    buying_organization_id: str | None,
    estimated_contract_value: float,
    lead_time_days: int,
    incumbent_status: bool,
    strategic_alignment: int,
    estimated_probability_win: int,
    actor: str,
) -> OpportunityIntakeRequest:
    return OpportunityIntakeRequest(
        name=name,
        client=client,
        buying_organization_id=buying_organization_id,
        estimated_contract_value=estimated_contract_value,
        lead_time_days=lead_time_days,
        incumbent_status=incumbent_status,
        strategic_alignment=strategic_alignment,
        estimated_probability_win=estimated_probability_win,
        actor=actor,
    )


def _render_intake_form(
    request: Request,
    *,
    errors: list[str],
    form_data: dict,
    organizations: list[object],
    status_code: int = 200,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="opportunity_form.html",
        context={
            "errors": errors,
            "form_data": form_data,
            "organizations": organizations,
            "example_presets": select_example_presets("opportunity_manual_intake"),
        },
        status_code=status_code,
    )


def _render_intake_draft_review(
    request: Request,
    *,
    draft: OpportunityIntakeDraftResponse,
    errors: list[str],
    form_data: dict,
    organizations: list[object],
    status_code: int = 200,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="opportunity_intake_draft.html",
        context={"draft": draft, "errors": errors, "form_data": form_data, "organizations": organizations},
        status_code=status_code,
    )


def _draft_form_data(draft: OpportunityIntakeDraftResponse, overrides: dict | None = None) -> dict:
    form_data = draft.suggested_fields.model_dump()
    form_data["actor"] = draft.actor
    if overrides:
        form_data.update(overrides)
    return form_data


def _validation_errors(exc: ValidationError) -> list[str]:
    errors: list[str] = []
    for issue in exc.errors():
        field_name = str(issue["loc"][-1]).replace("_", " ")
        errors.append(f"{field_name.title()}: {issue['msg']}")
    return errors


def _organization_options(db: Session) -> list[object]:
    return JanitorialOsService(db).list_organizations()


def _resolve_client_value(db: Session, client: str, buying_organization_id: str | None) -> str:
    if buying_organization_id:
        organization = JanitorialOsService(db).get_organization(buying_organization_id)
        if organization:
            return organization.name
    return client


def _build_draft_confirm_payload(
    *,
    name: str,
    client: str,
    buying_organization_id: str | None,
    estimated_contract_value: str,
    lead_time_days: str,
    incumbent_status: str | None,
    strategic_alignment: str,
    estimated_probability_win: str,
    actor: str,
) -> OpportunityIntakeDraftConfirmRequest:
    normalized = {
        "name": name,
        "client": client,
        "buying_organization_id": buying_organization_id,
        "estimated_contract_value": estimated_contract_value,
        "lead_time_days": lead_time_days,
        "incumbent_status": False if incumbent_status is None else incumbent_status,
        "strategic_alignment": strategic_alignment,
        "estimated_probability_win": estimated_probability_win,
        "actor": actor or None,
    }
    return OpportunityIntakeDraftConfirmRequest.model_validate(normalized)


@api_router.post("/intake", response_model=OpportunityIntakeResult)
def intake_opportunity(payload: OpportunityIntakeRequest, db: Session = Depends(get_db)) -> OpportunityIntakeResult:
    service = OpportunityIntakeService(db)
    try:
        return service.intake(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@api_router.post("/intake-rfp-drafts", response_model=OpportunityIntakeDraftResponse)
async def create_intake_rfp_draft_api(
    actor: str = Form("operator"),
    files: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
) -> OpportunityIntakeDraftResponse:
    upload_payloads: list[tuple[str, bytes]] = []
    for file in files or []:
        upload_payloads.append((file.filename or "uploaded-document.txt", await file.read()))
    batch = extract_text_from_upload_batch(upload_payloads)

    service = OpportunityIntakeService(db)
    try:
        return service.create_intake_rfp_draft(actor, batch)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@api_router.get("/intake-rfp-drafts/{draft_id}", response_model=OpportunityIntakeDraftResponse)
def get_intake_rfp_draft_api(draft_id: str, db: Session = Depends(get_db)) -> OpportunityIntakeDraftResponse:
    service = OpportunityIntakeService(db)
    draft = service.get_intake_rfp_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="RFP intake draft not found")
    return draft


@api_router.post("/intake-rfp-drafts/{draft_id}/confirm", response_model=OpportunityIntakeWithRfpResult)
def confirm_intake_rfp_draft_api(
    draft_id: str,
    payload: OpportunityIntakeDraftConfirmRequest,
    db: Session = Depends(get_db),
) -> OpportunityIntakeWithRfpResult:
    service = OpportunityIntakeService(db)
    try:
        return service.confirm_intake_rfp_draft(draft_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@api_router.post("/intake-with-rfp", response_model=OpportunityIntakeWithRfpResult)
async def intake_opportunity_with_rfp(
    name: str = Form(...),
    client: str = Form(""),
    buying_organization_id: str = Form(""),
    estimated_contract_value: float = Form(...),
    lead_time_days: int = Form(...),
    incumbent_status: bool = Form(False),
    strategic_alignment: int = Form(...),
    estimated_probability_win: int = Form(...),
    actor: str = Form("operator"),
    files: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
) -> OpportunityIntakeWithRfpResult:
    payload = _build_intake_payload(
        name=name,
        client=_resolve_client_value(db, client, buying_organization_id or None),
        buying_organization_id=buying_organization_id or None,
        estimated_contract_value=estimated_contract_value,
        lead_time_days=lead_time_days,
        incumbent_status=incumbent_status,
        strategic_alignment=strategic_alignment,
        estimated_probability_win=estimated_probability_win,
        actor=actor,
    )
    upload_payloads: list[tuple[str, bytes]] = []
    for file in files or []:
        upload_payloads.append((file.filename or "uploaded-document.txt", await file.read()))
    batch = extract_text_from_upload_batch(upload_payloads)

    service = OpportunityIntakeService(db)
    try:
        return service.intake_with_rfp_batch(payload, batch)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@api_router.get("", response_model=list[OpportunityDetailResponse])
def list_opportunities(
    include_archived: bool = Query(False),
    db: Session = Depends(get_db),
) -> list[OpportunityDetailResponse]:
    service = OpportunityIntakeService(db)
    opportunities = service.list_opportunities(include_archived=include_archived)
    results: list[OpportunityDetailResponse] = []
    for item in opportunities:
        detail = service.get_detail(item.id)
        if detail:
            results.append(detail)
    return results


@api_router.get("/gates/pending", response_model=list[GateInboxItemResponse])
def list_pending_gates(db: Session = Depends(get_db)) -> list[GateInboxItemResponse]:
    service = OpportunityIntakeService(db)
    return service.list_gate_inbox()


@api_router.get("/{opportunity_id}", response_model=OpportunityDetailResponse)
def get_opportunity(opportunity_id: str, db: Session = Depends(get_db)) -> OpportunityDetailResponse:
    service = OpportunityIntakeService(db)
    detail = service.get_detail(opportunity_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return detail


@api_router.post("/{opportunity_id}/archive", response_model=OpportunityDetailResponse)
def archive_opportunity(
    opportunity_id: str,
    payload: ArchiveActionRequest,
    db: Session = Depends(get_db),
) -> OpportunityDetailResponse:
    service = OpportunityIntakeService(db)
    try:
        opportunity = service.archive_opportunity(opportunity_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    detail = service.get_detail(opportunity.id)
    assert detail is not None
    return detail


@api_router.post("/{opportunity_id}/restore", response_model=OpportunityDetailResponse)
def restore_opportunity(
    opportunity_id: str,
    payload: ArchiveActionRequest,
    db: Session = Depends(get_db),
) -> OpportunityDetailResponse:
    service = OpportunityIntakeService(db)
    try:
        opportunity = service.restore_opportunity(opportunity_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    detail = service.get_detail(opportunity.id)
    assert detail is not None
    return detail


@api_router.get("/{opportunity_id}/timeline", response_model=list[WorkflowTimelineEventResponse])
def get_opportunity_timeline(
    opportunity_id: str,
    category: str = Query("ALL"),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[WorkflowTimelineEventResponse]:
    service = OpportunityIntakeService(db)
    detail = service.get_detail(opportunity_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    rows = service.workflow_timeline(opportunity_id, category=category, limit=limit)
    return [WorkflowTimelineEventResponse.model_validate(r) for r in rows]


@api_router.post("/{opportunity_id}/gate-decisions", response_model=GateDecisionResponse)
def add_gate_decision(
    opportunity_id: str, payload: GateDecisionRequest, db: Session = Depends(get_db)
) -> GateDecisionResponse:
    service = OpportunityIntakeService(db)
    try:
        record = service.add_gate_decision(opportunity_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not record:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return GateDecisionResponse.model_validate(record, from_attributes=True)


@api_router.post("/{opportunity_id}/stage-transition", response_model=StageTransitionResponse)
def transition_stage(
    opportunity_id: str,
    payload: StageTransitionRequest,
    db: Session = Depends(get_db),
) -> StageTransitionResponse:
    service = OpportunityIntakeService(db)
    result = service.transition_stage(opportunity_id, payload)
    if not result:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    if result.blockers:
        raise HTTPException(status_code=409, detail={"blockers": result.blockers, "from_stage": result.from_stage})
    return result


@api_router.get("/{opportunity_id}/stage-transition-preview", response_model=StageTransitionResponse)
def preview_stage_transition(
    opportunity_id: str,
    next_stage: str = Query(...),
    actor: str = Query("operator"),
    actor_user_id: str | None = Query(None),
    actor_role: str = Query("proposal_manager"),
    reason: str = Query("Preview stage transition"),
    db: Session = Depends(get_db),
) -> StageTransitionResponse:
    service = OpportunityIntakeService(db)
    payload = StageTransitionRequest(
        next_stage=next_stage,
        actor=actor,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        reason=reason,
    )
    result = service.preview_stage_transition(opportunity_id, payload)
    if not result:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return result


@web_router.get("/", response_class=HTMLResponse)
def home() -> RedirectResponse:
    return RedirectResponse(url="/dashboard", status_code=303)


@web_router.get("/opportunities", response_class=HTMLResponse)
def opportunities_view(
    request: Request,
    include_archived: bool = Query(False),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = OpportunityIntakeService(db)
    opportunities = service.list_opportunities(include_archived=include_archived)
    details = [detail for item in opportunities if (detail := service.get_detail(item.id)) is not None]
    return templates.TemplateResponse(
        request=request,
        name="opportunity_list.html",
        context={"opportunities": details, "include_archived": include_archived},
    )


@web_router.get("/intake", response_class=HTMLResponse)
def intake_form(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    return _render_intake_form(
        request,
        errors=[],
        form_data={"actor": "operator"},
        organizations=_organization_options(db),
    )


@web_router.post("/intake/rfp-drafts")
async def intake_rfp_draft_submit(
    request: Request,
    actor: str = Form("operator"),
    files: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
) -> Response:
    upload_payloads: list[tuple[str, bytes]] = []
    for file in files or []:
        upload_payloads.append((file.filename or "uploaded-document.txt", await file.read()))
    batch = extract_text_from_upload_batch(upload_payloads)
    service = OpportunityIntakeService(db)
    try:
        draft = service.create_intake_rfp_draft(actor, batch)
    except ValueError as exc:
        errors = [str(exc)]
        for warning in batch.warnings:
            if warning not in errors:
                errors.append(warning)
        return _render_intake_form(
            request,
            errors=errors,
            form_data={"actor": actor},
            organizations=_organization_options(db),
            status_code=422,
        )
    return RedirectResponse(url=f"/intake/rfp-drafts/{draft.draft_id}", status_code=303)


@web_router.get("/intake/rfp-drafts/{draft_id}", response_class=HTMLResponse)
def intake_rfp_draft_review(request: Request, draft_id: str, db: Session = Depends(get_db)) -> HTMLResponse:
    service = OpportunityIntakeService(db)
    draft = service.get_intake_rfp_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="RFP intake draft not found")
    return _render_intake_draft_review(
        request,
        draft=draft,
        errors=[],
        form_data=_draft_form_data(draft),
        organizations=_organization_options(db),
    )


@web_router.post("/intake", response_class=HTMLResponse)
def intake_submit(
    request: Request,
    name: str = Form(...),
    client: str = Form(""),
    buying_organization_id: str = Form(""),
    estimated_contract_value: float = Form(...),
    lead_time_days: int = Form(...),
    incumbent_status: bool = Form(False),
    strategic_alignment: int = Form(...),
    estimated_probability_win: int = Form(...),
    actor: str = Form("operator"),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    payload = _build_intake_payload(
        name=name,
        client=_resolve_client_value(db, client, buying_organization_id or None),
        buying_organization_id=buying_organization_id or None,
        estimated_contract_value=estimated_contract_value,
        lead_time_days=lead_time_days,
        incumbent_status=incumbent_status,
        strategic_alignment=strategic_alignment,
        estimated_probability_win=estimated_probability_win,
        actor=actor,
    )
    service = OpportunityIntakeService(db)
    try:
        result = service.intake(payload)
    except ValueError as exc:
        return _render_intake_form(
            request,
            errors=[str(exc)],
            form_data=payload.model_dump(),
            organizations=_organization_options(db),
            status_code=422,
        )
    detail = service.get_detail(result.id)
    return templates.TemplateResponse(
        request=request,
        name="opportunity_result.html",
        context={"result": result, "detail": detail},
    )


@web_router.post("/intake/rfp-drafts/{draft_id}/confirm", response_class=HTMLResponse)
def intake_rfp_draft_confirm(
    request: Request,
    draft_id: str,
    name: str = Form(""),
    client: str = Form(""),
    buying_organization_id: str = Form(""),
    estimated_contract_value: str = Form(""),
    lead_time_days: str = Form(""),
    incumbent_status: str | None = Form(None),
    strategic_alignment: str = Form(""),
    estimated_probability_win: str = Form(""),
    actor: str = Form("operator"),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = OpportunityIntakeService(db)
    draft = service.get_intake_rfp_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="RFP intake draft not found")

    raw_form_data = {
        "name": name,
        "client": client,
        "buying_organization_id": buying_organization_id,
        "estimated_contract_value": estimated_contract_value,
        "lead_time_days": lead_time_days,
        "incumbent_status": incumbent_status is not None,
        "strategic_alignment": strategic_alignment,
        "estimated_probability_win": estimated_probability_win,
        "actor": actor,
    }
    try:
        payload = _build_draft_confirm_payload(
            name=name,
            client=_resolve_client_value(db, client, buying_organization_id or None),
            buying_organization_id=buying_organization_id or None,
            estimated_contract_value=estimated_contract_value,
            lead_time_days=lead_time_days,
            incumbent_status=incumbent_status,
            strategic_alignment=strategic_alignment,
            estimated_probability_win=estimated_probability_win,
            actor=actor,
        )
    except ValidationError as exc:
        return _render_intake_draft_review(
            request,
            draft=draft,
            errors=_validation_errors(exc),
            form_data=raw_form_data,
            organizations=_organization_options(db),
            status_code=422,
        )

    try:
        result = service.confirm_intake_rfp_draft(draft_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    detail = service.get_detail(result.id)
    return templates.TemplateResponse(
        request=request,
        name="opportunity_result.html",
        context={"result": result, "detail": detail, "rfp_result": result},
    )


@web_router.post("/intake-with-rfp", response_class=HTMLResponse)
async def intake_with_rfp_submit(
    request: Request,
    name: str = Form(...),
    client: str = Form(""),
    buying_organization_id: str = Form(""),
    estimated_contract_value: float = Form(...),
    lead_time_days: int = Form(...),
    incumbent_status: bool = Form(False),
    strategic_alignment: int = Form(...),
    estimated_probability_win: int = Form(...),
    actor: str = Form("operator"),
    files: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    payload = _build_intake_payload(
        name=name,
        client=_resolve_client_value(db, client, buying_organization_id or None),
        buying_organization_id=buying_organization_id or None,
        estimated_contract_value=estimated_contract_value,
        lead_time_days=lead_time_days,
        incumbent_status=incumbent_status,
        strategic_alignment=strategic_alignment,
        estimated_probability_win=estimated_probability_win,
        actor=actor,
    )
    upload_payloads: list[tuple[str, bytes]] = []
    for file in files or []:
        upload_payloads.append((file.filename or "uploaded-document.txt", await file.read()))
    batch = extract_text_from_upload_batch(upload_payloads)
    service = OpportunityIntakeService(db)
    try:
        result = service.intake_with_rfp_batch(payload, batch)
    except ValueError as exc:
        errors = [str(exc)]
        for warning in batch.warnings:
            if warning not in errors:
                errors.append(warning)
        return _render_intake_form(
            request,
            errors=errors,
            form_data=payload.model_dump(),
            organizations=_organization_options(db),
            status_code=422,
        )

    detail = service.get_detail(result.id)
    return templates.TemplateResponse(
        request=request,
        name="opportunity_result.html",
        context={"result": result, "detail": detail, "rfp_result": result},
    )


@web_router.get("/opportunities/{opportunity_id}", response_class=HTMLResponse)
def opportunity_detail(request: Request, opportunity_id: str, db: Session = Depends(get_db)) -> HTMLResponse:
    service = OpportunityIntakeService(db)
    detail = service.get_detail(opportunity_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    session_user = get_session_user(request, db)
    authorized_gates: list[str] = []
    permission_reports: list[dict] = []
    if session_user:
        identity = IdentityService(db)
        permission_reports = identity.gate_permission_reports(session_user.id, opportunity_id)
        for report in permission_reports:
            if report["allowed"]:
                authorized_gates.append(report["gate_code"])
    return templates.TemplateResponse(
        request=request,
        name="opportunity_detail.html",
        context={
            "detail": detail,
            "authorized_gates": authorized_gates,
            "session_user": session_user,
            "permission_reports": permission_reports,
        },
    )


@web_router.post("/opportunities/{opportunity_id}/archive")
def archive_opportunity_web(
    opportunity_id: str,
    actor: str = Form("operator"),
    reason: str = Form(""),
    return_to: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    service = OpportunityIntakeService(db)
    payload = ArchiveActionRequest(actor=actor, reason=reason or None)
    try:
        service.archive_opportunity(opportunity_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    destination = return_to or f"/opportunities/{opportunity_id}"
    return RedirectResponse(url=destination, status_code=303)


@web_router.post("/opportunities/{opportunity_id}/restore")
def restore_opportunity_web(
    opportunity_id: str,
    actor: str = Form("operator"),
    return_to: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    service = OpportunityIntakeService(db)
    payload = ArchiveActionRequest(actor=actor)
    try:
        service.restore_opportunity(opportunity_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    destination = return_to or f"/opportunities/{opportunity_id}"
    return RedirectResponse(url=destination, status_code=303)


@web_router.get("/opportunities/{opportunity_id}/timeline", response_class=HTMLResponse)
def opportunity_timeline(request: Request, opportunity_id: str, category: str = "ALL", db: Session = Depends(get_db)) -> HTMLResponse:
    service = OpportunityIntakeService(db)
    detail = service.get_detail(opportunity_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    rows = service.workflow_timeline(opportunity_id, category=category)
    return templates.TemplateResponse(
        request=request,
        name="opportunity_timeline.html",
        context={
            "detail": detail,
            "events": rows,
            "selected_category": category.upper(),
            "categories": ["ALL", "GATE", "STAGE", "REVIEW", "SUBMISSION", "COMPLIANCE", "KNOWLEDGE", "SYSTEM"],
        },
    )


@web_router.post("/opportunities/{opportunity_id}/gate-decisions")
def add_gate_decision_web(
    request: Request,
    opportunity_id: str,
    decision: str = Form(...),
    decider: str = Form(""),
    decider_user_id: str = Form(""),
    decider_role: str = Form("proposal_manager"),
    rationale: str = Form(...),
    gate_code: str = Form("GATE_A"),
    rework_instructions: str = Form(""),
    rework_owner: str = Form(""),
    rework_due_date: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    service = OpportunityIntakeService(db)
    session_user = get_session_user(request, db)
    if session_user:
        allowed = IdentityService(db).resolve_authorized_role_for_gate(session_user.id, gate_code, opportunity_id)
        if not allowed:
            raise HTTPException(status_code=403, detail=f"You are not authorized for {gate_code}")
    resolved_decider = session_user.display_name if session_user else (decider or "operator")
    resolved_decider_user_id = session_user.id if session_user else (decider_user_id or None)
    payload = GateDecisionRequest(
        gate_code=gate_code,
        decision=decision,
        decider=resolved_decider,
        decider_user_id=resolved_decider_user_id,
        decider_role=decider_role,
        rationale=rationale,
        rework_instructions=rework_instructions or None,
        rework_owner=rework_owner or None,
        rework_due_date=rework_due_date or None,
    )
    try:
        record = service.add_gate_decision(opportunity_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not record:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return RedirectResponse(url=f"/opportunities/{opportunity_id}", status_code=303)


@web_router.post("/opportunities/{opportunity_id}/stage-transition")
def transition_stage_web(
    request: Request,
    opportunity_id: str,
    next_stage: str = Form(...),
    actor: str = Form("operator"),
    actor_role: str = Form("proposal_manager"),
    reason: str = Form("Manual stage transition"),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    service = OpportunityIntakeService(db)
    session_user = get_session_user(request, db)
    if session_user:
        detail = service.get_detail(opportunity_id)
        if not detail:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        allowed_role = IdentityService(db).resolve_authorized_role_for_gate(
            session_user.id, active_gate_for_stage(detail.stage), opportunity_id
        )
        if not allowed_role:
            raise HTTPException(status_code=403, detail="You are not authorized to transition this opportunity stage")
        payload = StageTransitionRequest(
            next_stage=next_stage,
            actor=session_user.display_name,
            actor_user_id=session_user.id,
            actor_role=allowed_role,
            reason=reason,
        )
    else:
        payload = StageTransitionRequest(next_stage=next_stage, actor=actor, actor_role=actor_role, reason=reason)
    result = service.transition_stage(opportunity_id, payload)
    if not result:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    if result.blockers:
        raise HTTPException(status_code=409, detail={"blockers": result.blockers})
    return RedirectResponse(url=f"/opportunities/{opportunity_id}", status_code=303)


@web_router.get("/gates/inbox", response_class=HTMLResponse)
def gates_inbox(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    service = OpportunityIntakeService(db)
    items = service.list_gate_inbox()
    session_user = get_session_user(request, db)
    can_act_by_item: dict[str, bool] = {}
    if session_user:
        identity = IdentityService(db)
        for item in items:
            key = f"{item.opportunity_id}:{item.gate_code}"
            can_act_by_item[key] = (
                identity.resolve_authorized_role_for_gate(session_user.id, item.gate_code, item.opportunity_id)
                is not None
            )
    else:
        for item in items:
            can_act_by_item[f"{item.opportunity_id}:{item.gate_code}"] = True
    return templates.TemplateResponse(
        request=request,
        name="gates_inbox.html",
        context={"items": items, "can_act_by_item": can_act_by_item, "session_user": session_user},
    )


@web_router.post("/gates/inbox/decide")
def gates_inbox_decide(
    request: Request,
    opportunity_id: str = Form(...),
    gate_code: str = Form(...),
    decision: str = Form(...),
    decider: str = Form(""),
    decider_user_id: str = Form(""),
    decider_role: str = Form("proposal_manager"),
    rationale: str = Form(...),
    rework_instructions: str = Form(""),
    rework_owner: str = Form(""),
    rework_due_date: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    service = OpportunityIntakeService(db)
    session_user = get_session_user(request, db)
    if session_user:
        allowed = IdentityService(db).resolve_authorized_role_for_gate(session_user.id, gate_code, opportunity_id)
        if not allowed:
            raise HTTPException(status_code=403, detail=f"You are not authorized for {gate_code}")
    resolved_decider = session_user.display_name if session_user else (decider or "operator")
    resolved_decider_user_id = session_user.id if session_user else (decider_user_id or None)
    payload = GateDecisionRequest(
        gate_code=gate_code,
        decision=decision,
        decider=resolved_decider,
        decider_user_id=resolved_decider_user_id,
        decider_role=decider_role,
        rationale=rationale,
        rework_instructions=rework_instructions or None,
        rework_owner=rework_owner or None,
        rework_due_date=rework_due_date or None,
    )
    try:
        record = service.add_gate_decision(opportunity_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not record:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return RedirectResponse(url="/gates/inbox", status_code=303)
