from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.company_os.models import (
    ActionItem,
    ApprovalRequest,
    Engagement,
    FounderBriefRun,
    MeetingCommitment,
    ScoreboardSnapshot,
    SourceSignal,
)
from app.modules.company_os.schemas import (
    ActionItemResponse,
    ApprovalRequestResponse,
    EngagementResponse,
    FounderBriefRunResponse,
    IngestRunRequest,
    IngestRunResponse,
    MeetingCommitmentResponse,
    ProjectionRunRequest,
    ScoreboardSnapshotResponse,
    SourceSignalResponse,
    StatusUpdateRequest,
    TimelineMilestoneResponse,
    StakeholderResponse,
    KnowledgePromotionCandidateResponse,
)
from app.modules.company_os.service import (
    CompanyOsService,
    OPERATING_GUARDRAILS,
    founder_decisions,
    founder_delegation_queue,
    founder_top_moves,
    render_founder_brief_markdown,
    snapshot_cash_rows,
    snapshot_revenue_rows,
)
from app.web.templating import build_templates


api_router = APIRouter(prefix="/api/company-os", tags=["company-os"])
web_router = APIRouter(tags=["web"])
templates = build_templates()


def _signal_response(row: SourceSignal) -> SourceSignalResponse:
    return SourceSignalResponse.model_validate(row, from_attributes=True)


def _action_response(row: ActionItem) -> ActionItemResponse:
    return ActionItemResponse.model_validate(row, from_attributes=True)


def _approval_response(row: ApprovalRequest) -> ApprovalRequestResponse:
    return ApprovalRequestResponse.model_validate(row, from_attributes=True)


def _commitment_response(row: MeetingCommitment) -> MeetingCommitmentResponse:
    return MeetingCommitmentResponse.model_validate(row, from_attributes=True)


def _engagement_response(row: Engagement) -> EngagementResponse:
    return EngagementResponse(
        id=row.id,
        client_name=row.client_name,
        engagement_name=row.engagement_name,
        engagement_type=row.engagement_type,
        workflow_stage=row.workflow_stage,
        status=row.status,
        intake_date=row.intake_date,
        owner=row.owner,
        complexity_level=row.complexity_level,
        next_action=row.next_action,
        deadline=row.deadline,
        risk_level=row.risk_level,
        last_signal_id=row.last_signal_id,
        provenance_ref=row.provenance_ref,
        agent_id=row.agent_id,
        run_id=row.run_id,
        notes=row.notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
        milestones=[TimelineMilestoneResponse.model_validate(item, from_attributes=True) for item in row.milestones],
        stakeholders=[StakeholderResponse.model_validate(item, from_attributes=True) for item in row.stakeholders],
        action_items=[ActionItemResponse.model_validate(item, from_attributes=True) for item in row.action_items],
        approvals=[ApprovalRequestResponse.model_validate(item, from_attributes=True) for item in row.approvals],
        commitments=[MeetingCommitmentResponse.model_validate(item, from_attributes=True) for item in row.commitments],
        knowledge_candidates=[KnowledgePromotionCandidateResponse.model_validate(item, from_attributes=True) for item in row.knowledge_candidates],
    )


def _scoreboard_response(row: ScoreboardSnapshot) -> ScoreboardSnapshotResponse:
    return ScoreboardSnapshotResponse(
        id=row.id,
        snapshot_date=row.snapshot_date,
        pipeline_value=row.pipeline_value,
        weighted_pipeline=row.weighted_pipeline,
        meetings_booked=row.meetings_booked,
        proposal_count=row.proposal_count,
        proposal_win_rate=row.proposal_win_rate,
        active_delivery_count=row.active_delivery_count,
        overdue_invoices=row.overdue_invoices,
        total_ar_over_30=row.total_ar_over_30,
        open_hiring_roles=row.open_hiring_roles,
        urgent_risks=row.urgent_risks,
        notes=row.notes,
        agent_id=row.agent_id,
        run_id=row.run_id,
        owner=row.owner,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
        revenue_rows=snapshot_revenue_rows(row),
        cashflow_rows=snapshot_cash_rows(row),
    )


def _brief_response(row: FounderBriefRun) -> FounderBriefRunResponse:
    return FounderBriefRunResponse(
        id=row.id,
        brief_date=row.brief_date,
        executive_control_summary=row.executive_control_summary,
        decisions_needed=founder_decisions(row),
        revenue_watch=row.revenue_watch,
        delivery_risk_watch=row.delivery_risk_watch,
        cash_collections_watch=row.cash_collections_watch,
        people_capacity_watch=row.people_capacity_watch,
        top_moves=founder_top_moves(row),
        delegation_queue=founder_delegation_queue(row),
        scoreboard_snapshot_id=row.scoreboard_snapshot_id,
        agent_id=row.agent_id,
        run_id=row.run_id,
        owner=row.owner,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _ingest_response(summary) -> IngestRunResponse:
    return IngestRunResponse(
        run_id=summary.run_id,
        sources_scanned=summary.sources_scanned,
        items_discovered=summary.items_discovered,
        signals_created=summary.signals_created,
        engagements_created=summary.engagements_created,
        engagements_updated=summary.engagements_updated,
        actions_created=summary.actions_created,
        approvals_created=summary.approvals_created,
        commitments_created=summary.commitments_created,
        knowledge_candidates_created=summary.knowledge_candidates_created,
        projections_written=summary.projections_written or [],
        founder_brief_id=summary.founder_brief_id,
        scoreboard_snapshot_id=summary.scoreboard_snapshot_id,
        created_at=summary.created_at,
    )


def _next_url(next_url: str | None, default_url: str) -> str:
    text = (next_url or "").strip()
    return text or default_url


def _service(db: Session) -> CompanyOsService:
    return CompanyOsService(db)


@api_router.post("/ingest", response_model=IngestRunResponse)
def run_company_os_ingest(payload: IngestRunRequest, db: Session = Depends(get_db)) -> IngestRunResponse:
    summary = _service(db).run_manual_cycle(
        source_config_path=payload.source_config_path,
        marketing_agents_root=payload.marketing_agents_root,
        owner=payload.owner,
    )
    return _ingest_response(summary)


@api_router.post("/projections", response_model=list[str])
def run_company_os_projections(payload: ProjectionRunRequest, db: Session = Depends(get_db)) -> list[str]:
    return _service(db).run_projection_cycle(marketing_agents_root=payload.marketing_agents_root)


@api_router.get("/signals", response_model=list[SourceSignalResponse])
def list_company_os_signals(db: Session = Depends(get_db)) -> list[SourceSignalResponse]:
    return [_signal_response(row) for row in _service(db).list_signals()]


@api_router.get("/engagements", response_model=list[EngagementResponse])
def list_company_os_engagements(db: Session = Depends(get_db)) -> list[EngagementResponse]:
    return [_engagement_response(row) for row in _service(db).list_engagements()]


@api_router.get("/engagements/{engagement_id}", response_model=EngagementResponse)
def get_company_os_engagement(engagement_id: str, db: Session = Depends(get_db)) -> EngagementResponse:
    engagement = _service(db).get_engagement(engagement_id)
    if engagement is None:
        raise HTTPException(status_code=404, detail="Engagement not found.")
    return _engagement_response(engagement)


@api_router.post("/engagements/{engagement_id}/status", response_model=EngagementResponse)
def update_company_os_engagement(engagement_id: str, payload: StatusUpdateRequest, db: Session = Depends(get_db)) -> EngagementResponse:
    try:
        engagement = _service(db).update_engagement_status(engagement_id, status=payload.status, owner=payload.owner, note=payload.note)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _engagement_response(engagement)


@api_router.get("/actions", response_model=list[ActionItemResponse])
def list_company_os_actions(db: Session = Depends(get_db)) -> list[ActionItemResponse]:
    return [_action_response(row) for row in _service(db).list_actions()]


@api_router.post("/actions/{action_id}/status", response_model=ActionItemResponse)
def update_company_os_action(action_id: str, payload: StatusUpdateRequest, db: Session = Depends(get_db)) -> ActionItemResponse:
    try:
        row = _service(db).update_action_status(action_id, status=payload.status, owner=payload.owner, note=payload.note)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _action_response(row)


@api_router.get("/approvals", response_model=list[ApprovalRequestResponse])
def list_company_os_approvals(db: Session = Depends(get_db)) -> list[ApprovalRequestResponse]:
    return [_approval_response(row) for row in _service(db).list_approvals()]


@api_router.post("/approvals/{approval_id}/status", response_model=ApprovalRequestResponse)
def update_company_os_approval(approval_id: str, payload: StatusUpdateRequest, db: Session = Depends(get_db)) -> ApprovalRequestResponse:
    try:
        row = _service(db).update_approval_status(approval_id, status=payload.status, owner=payload.owner, note=payload.note)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _approval_response(row)


@api_router.get("/commitments", response_model=list[MeetingCommitmentResponse])
def list_company_os_commitments(db: Session = Depends(get_db)) -> list[MeetingCommitmentResponse]:
    return [_commitment_response(row) for row in _service(db).list_commitments()]


@api_router.post("/commitments/{commitment_id}/status", response_model=MeetingCommitmentResponse)
def update_company_os_commitment(commitment_id: str, payload: StatusUpdateRequest, db: Session = Depends(get_db)) -> MeetingCommitmentResponse:
    try:
        row = _service(db).update_commitment_status(commitment_id, status=payload.status, owner=payload.owner, note=payload.note)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _commitment_response(row)


@api_router.get("/scoreboard/latest", response_model=ScoreboardSnapshotResponse)
def latest_company_os_scoreboard(db: Session = Depends(get_db)) -> ScoreboardSnapshotResponse:
    snapshot = _service(db).latest_scoreboard_snapshot()
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Scoreboard snapshot not found.")
    return _scoreboard_response(snapshot)


@api_router.post("/scoreboard/generate", response_model=ScoreboardSnapshotResponse)
def generate_company_os_scoreboard(db: Session = Depends(get_db)) -> ScoreboardSnapshotResponse:
    snapshot = _service(db).generate_scoreboard_snapshot()
    return _scoreboard_response(snapshot)


@api_router.get("/founder-brief/latest", response_model=FounderBriefRunResponse)
def latest_company_os_founder_brief(db: Session = Depends(get_db)) -> FounderBriefRunResponse:
    brief = _service(db).latest_founder_brief()
    if brief is None:
        raise HTTPException(status_code=404, detail="Founder brief not found.")
    return _brief_response(brief)


@api_router.post("/founder-brief/generate", response_model=FounderBriefRunResponse)
def generate_company_os_founder_brief(db: Session = Depends(get_db)) -> FounderBriefRunResponse:
    brief = _service(db).generate_founder_brief()
    return _brief_response(brief)


@web_router.get("/company-os", response_class=HTMLResponse)
def company_os_home() -> RedirectResponse:
    return RedirectResponse(url="/company-os/inbox", status_code=303)


@web_router.get("/company-os/inbox", response_class=HTMLResponse)
def company_os_inbox(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    service = _service(db)
    signals = service.list_signals(limit=50)
    approvals = service.list_approvals()
    commitments = service.list_commitments()
    return templates.TemplateResponse(
        request=request,
        name="company_os_inbox.html",
        context={
            "signals": signals,
            "approvals_open": len([row for row in approvals if row.status == "pending"]),
            "commitments_open": len([row for row in commitments if row.status != "done"]),
            "guardrails": OPERATING_GUARDRAILS,
        },
    )


@web_router.post("/company-os/run-intake")
def company_os_run_intake(
    source_config_path: str = Form(""),
    marketing_agents_root: str = Form(""),
    owner: str = Form("Timmy Semenza"),
    next_url: str = Form("/company-os/inbox"),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    _service(db).run_manual_cycle(
        source_config_path=source_config_path or None,
        marketing_agents_root=marketing_agents_root or None,
        owner=owner,
    )
    return RedirectResponse(url=_next_url(next_url, "/company-os/inbox"), status_code=303)


@web_router.post("/company-os/run-projections")
def company_os_run_projections(
    marketing_agents_root: str = Form(""),
    next_url: str = Form("/company-os/inbox"),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    _service(db).run_projection_cycle(marketing_agents_root=marketing_agents_root or None)
    return RedirectResponse(url=_next_url(next_url, "/company-os/inbox"), status_code=303)


@web_router.get("/company-os/engagements", response_class=HTMLResponse)
def company_os_engagements(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    service = _service(db)
    return templates.TemplateResponse(
        request=request,
        name="company_os_engagements.html",
        context={"engagements": service.list_engagements(), "guardrails": OPERATING_GUARDRAILS},
    )


@web_router.get("/company-os/approvals", response_class=HTMLResponse)
def company_os_approvals(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    service = _service(db)
    return templates.TemplateResponse(
        request=request,
        name="company_os_approvals.html",
        context={
            "approvals": service.list_approvals(),
            "commitments": service.list_commitments(),
            "guardrails": OPERATING_GUARDRAILS,
        },
    )


@web_router.post("/company-os/approvals/{approval_id}/status")
def company_os_approval_status(
    approval_id: str,
    status: str = Form(...),
    owner: str = Form(""),
    note: str = Form(""),
    next_url: str = Form("/company-os/approvals"),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    _service(db).update_approval_status(approval_id, status=status, owner=owner or None, note=note or None)
    return RedirectResponse(url=_next_url(next_url, "/company-os/approvals"), status_code=303)


@web_router.post("/company-os/commitments/{commitment_id}/status")
def company_os_commitment_status(
    commitment_id: str,
    status: str = Form(...),
    owner: str = Form(""),
    note: str = Form(""),
    next_url: str = Form("/company-os/approvals"),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    _service(db).update_commitment_status(commitment_id, status=status, owner=owner or None, note=note or None)
    return RedirectResponse(url=_next_url(next_url, "/company-os/approvals"), status_code=303)


@web_router.get("/company-os/founder-brief", response_class=HTMLResponse)
def company_os_founder_brief(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    service = _service(db)
    brief = service.latest_founder_brief()
    snapshot = service.latest_scoreboard_snapshot()
    return templates.TemplateResponse(
        request=request,
        name="company_os_founder_brief.html",
        context={
            "brief": brief,
            "snapshot": snapshot,
            "brief_markdown": render_founder_brief_markdown(brief, snapshot) if brief else "",
            "decisions": founder_decisions(brief),
            "top_moves": founder_top_moves(brief),
            "delegation_queue": founder_delegation_queue(brief),
            "guardrails": OPERATING_GUARDRAILS,
        },
    )


@web_router.post("/company-os/founder-brief/generate")
def company_os_generate_founder_brief(next_url: str = Form("/company-os/founder-brief"), db: Session = Depends(get_db)) -> RedirectResponse:
    _service(db).generate_founder_brief()
    return RedirectResponse(url=_next_url(next_url, "/company-os/founder-brief"), status_code=303)


@web_router.get("/company-os/scoreboard", response_class=HTMLResponse)
def company_os_scoreboard(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    service = _service(db)
    snapshot = service.latest_scoreboard_snapshot()
    return templates.TemplateResponse(
        request=request,
        name="company_os_scoreboard.html",
        context={
            "snapshot": snapshot,
            "revenue_rows": snapshot_revenue_rows(snapshot),
            "cash_rows": snapshot_cash_rows(snapshot),
            "guardrails": OPERATING_GUARDRAILS,
        },
    )


@web_router.post("/company-os/scoreboard/generate")
def company_os_generate_scoreboard(next_url: str = Form("/company-os/scoreboard"), db: Session = Depends(get_db)) -> RedirectResponse:
    _service(db).generate_scoreboard_snapshot()
    return RedirectResponse(url=_next_url(next_url, "/company-os/scoreboard"), status_code=303)
