from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.session_auth import get_session_user
from app.core.workflow import active_gate_for_stage
from app.modules.identity.service import IdentityService
from app.modules.opportunity_intake.schemas import (
    GateInboxItemResponse,
    GateDecisionRequest,
    GateDecisionResponse,
    OpportunityDetailResponse,
    OpportunityIntakeRequest,
    OpportunityIntakeResult,
    StageTransitionRequest,
    StageTransitionResponse,
    WorkflowTimelineEventResponse,
)
from app.modules.opportunity_intake.service import OpportunityIntakeService


api_router = APIRouter(prefix="/api/opportunities", tags=["opportunity-intake"])
web_router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/web/templates")


@api_router.post("/intake", response_model=OpportunityIntakeResult)
def intake_opportunity(payload: OpportunityIntakeRequest, db: Session = Depends(get_db)) -> OpportunityIntakeResult:
    service = OpportunityIntakeService(db)
    return service.intake(payload)


@api_router.get("", response_model=list[OpportunityDetailResponse])
def list_opportunities(db: Session = Depends(get_db)) -> list[OpportunityDetailResponse]:
    service = OpportunityIntakeService(db)
    opportunities = service.list_opportunities()
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
def home(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    service = OpportunityIntakeService(db)
    opportunities = service.list_opportunities()
    return templates.TemplateResponse(
        request=request,
        name="opportunity_list.html",
        context={"opportunities": opportunities},
    )


@web_router.get("/intake", response_class=HTMLResponse)
def intake_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="opportunity_form.html",
        context={"errors": []},
    )


@web_router.post("/intake", response_class=HTMLResponse)
def intake_submit(
    request: Request,
    name: str = Form(...),
    client: str = Form(...),
    estimated_contract_value: float = Form(...),
    lead_time_days: int = Form(...),
    incumbent_status: bool = Form(False),
    strategic_alignment: int = Form(...),
    estimated_probability_win: int = Form(...),
    actor: str = Form("operator"),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    payload = OpportunityIntakeRequest(
        name=name,
        client=client,
        estimated_contract_value=estimated_contract_value,
        lead_time_days=lead_time_days,
        incumbent_status=incumbent_status,
        strategic_alignment=strategic_alignment,
        estimated_probability_win=estimated_probability_win,
        actor=actor,
    )
    service = OpportunityIntakeService(db)
    result = service.intake(payload)
    detail = service.get_detail(result.id)
    return templates.TemplateResponse(
        request=request,
        name="opportunity_result.html",
        context={"result": result, "detail": detail},
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
