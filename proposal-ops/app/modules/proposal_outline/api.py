from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.proposal_outline.schemas import ProposalOutlineGenerateRequest, ProposalOutlineResponse
from app.modules.proposal_outline.service import ProposalOutlineService


api_router = APIRouter(prefix="/api/opportunities", tags=["proposal-outline"])
web_router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/web/templates")


def _to_response(service: ProposalOutlineService, outline) -> ProposalOutlineResponse:
    return ProposalOutlineResponse(
        id=outline.id,
        opportunity_id=outline.opportunity_id,
        version=outline.version,
        source=outline.source,
        sections=service.parse_sections(outline),
        created_at=outline.created_at,
    )


@api_router.get("/{opportunity_id}/proposal-outline", response_model=ProposalOutlineResponse)
def get_proposal_outline(opportunity_id: str, db: Session = Depends(get_db)) -> ProposalOutlineResponse:
    service = ProposalOutlineService(db)
    outline = service.get_latest(opportunity_id)
    if not outline:
        raise HTTPException(status_code=404, detail="Proposal outline not found")
    return _to_response(service, outline)


@api_router.get("/{opportunity_id}/proposal-outline/versions", response_model=list[ProposalOutlineResponse])
def list_proposal_outline_versions(opportunity_id: str, db: Session = Depends(get_db)) -> list[ProposalOutlineResponse]:
    service = ProposalOutlineService(db)
    outlines = service.list_versions(opportunity_id)
    if not outlines:
        raise HTTPException(status_code=404, detail="Proposal outline not found")
    return [_to_response(service, o) for o in outlines]


@api_router.post("/{opportunity_id}/proposal-outline/generate", response_model=ProposalOutlineResponse)
def generate_proposal_outline(
    opportunity_id: str, payload: ProposalOutlineGenerateRequest, db: Session = Depends(get_db)
) -> ProposalOutlineResponse:
    service = ProposalOutlineService(db)
    try:
        outline = service.generate(opportunity_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _to_response(service, outline)


@web_router.get("/opportunities/{opportunity_id}/proposal-outline", response_class=HTMLResponse)
def proposal_outline_dashboard(opportunity_id: str, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    service = ProposalOutlineService(db)
    latest = service.get_latest(opportunity_id)
    versions = service.list_versions(opportunity_id)
    sections = service.parse_sections(latest) if latest else []
    return templates.TemplateResponse(
        request=request,
        name="proposal_outline.html",
        context={
            "opportunity_id": opportunity_id,
            "outline": latest,
            "versions": versions,
            "sections": sections,
        },
    )


@web_router.post("/opportunities/{opportunity_id}/proposal-outline/generate")
def generate_proposal_outline_web(
    opportunity_id: str,
    actor: str = Form("operator"),
    include_unmapped: bool = Form(False),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    payload = ProposalOutlineGenerateRequest(actor=actor, include_unmapped=include_unmapped)
    service = ProposalOutlineService(db)
    try:
        service.generate(opportunity_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return RedirectResponse(url=f"/opportunities/{opportunity_id}/proposal-outline", status_code=303)
