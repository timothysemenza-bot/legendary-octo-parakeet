from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.capture_plan.schemas import CapturePlanResponse, CapturePlanUpdateRequest
from app.modules.capture_plan.service import CapturePlanService


api_router = APIRouter(prefix="/api/opportunities", tags=["capture-plan"])
web_router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/web/templates")


@api_router.get("/{opportunity_id}/capture-plan", response_model=CapturePlanResponse)
def get_capture_plan(opportunity_id: str, db: Session = Depends(get_db)) -> CapturePlanResponse:
    service = CapturePlanService(db)
    plan = service.get_latest(opportunity_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Capture plan not found")
    return CapturePlanResponse.model_validate(plan, from_attributes=True)


@api_router.get("/{opportunity_id}/capture-plan/versions", response_model=list[CapturePlanResponse])
def list_capture_plan_versions(opportunity_id: str, db: Session = Depends(get_db)) -> list[CapturePlanResponse]:
    service = CapturePlanService(db)
    plans = service.list_versions(opportunity_id)
    if not plans:
        raise HTTPException(status_code=404, detail="Capture plan not found")
    return [CapturePlanResponse.model_validate(p, from_attributes=True) for p in plans]


@api_router.post("/{opportunity_id}/capture-plan", response_model=CapturePlanResponse)
def create_capture_plan_version(
    opportunity_id: str,
    payload: CapturePlanUpdateRequest,
    db: Session = Depends(get_db),
) -> CapturePlanResponse:
    service = CapturePlanService(db)
    try:
        plan = service.create_version(opportunity_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CapturePlanResponse.model_validate(plan, from_attributes=True)


@web_router.get("/opportunities/{opportunity_id}/capture-plan", response_class=HTMLResponse)
def capture_plan_view(opportunity_id: str, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    service = CapturePlanService(db)
    latest = service.get_latest(opportunity_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Capture plan not found")
    versions = service.list_versions(opportunity_id)
    return templates.TemplateResponse(
        request=request,
        name="capture_plan.html",
        context={
            "opportunity_id": opportunity_id,
            "plan": latest,
            "versions": versions,
        },
    )


@web_router.post("/opportunities/{opportunity_id}/capture-plan")
def capture_plan_update_web(
    opportunity_id: str,
    summary: str = Form(...),
    client_priorities: str = Form(...),
    competitive_landscape: str = Form(...),
    win_themes_draft: str = Form(...),
    solution_positioning: str = Form(...),
    timeline: str = Form(...),
    actor: str = Form("operator"),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    payload = CapturePlanUpdateRequest(
        summary=summary,
        client_priorities=client_priorities,
        competitive_landscape=competitive_landscape,
        win_themes_draft=win_themes_draft,
        solution_positioning=solution_positioning,
        timeline=timeline,
        actor=actor,
    )
    service = CapturePlanService(db)
    try:
        service.create_version(opportunity_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RedirectResponse(url=f"/opportunities/{opportunity_id}/capture-plan", status_code=303)
