from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.knowledge.schemas import (
    KnowledgePromotionDecisionRequest,
    KnowledgePromotionResponse,
    KnowledgeReadinessResponse,
    LessonsRecordApproveRequest,
    LessonsRecordCreateRequest,
    LessonsRecordResponse,
)
from app.modules.knowledge.service import KnowledgeService


api_router = APIRouter(prefix="/api/opportunities", tags=["knowledge"])
web_router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/web/templates")


@api_router.get("/{opportunity_id}/lessons", response_model=list[LessonsRecordResponse])
def list_lessons(opportunity_id: str, db: Session = Depends(get_db)) -> list[LessonsRecordResponse]:
    return KnowledgeService(db).list_records(opportunity_id)


@api_router.post("/{opportunity_id}/lessons", response_model=LessonsRecordResponse)
def create_lessons(
    opportunity_id: str,
    payload: LessonsRecordCreateRequest,
    db: Session = Depends(get_db),
) -> LessonsRecordResponse:
    return KnowledgeService(db).create_record(opportunity_id, payload)


@api_router.post("/{opportunity_id}/lessons/{record_id}/approve", response_model=LessonsRecordResponse)
def approve_lessons(
    opportunity_id: str,
    record_id: str,
    payload: LessonsRecordApproveRequest,
    db: Session = Depends(get_db),
) -> LessonsRecordResponse:
    record = KnowledgeService(db).approve_record(opportunity_id, record_id, payload)
    if not record:
        raise HTTPException(status_code=404, detail="Lessons record not found")
    return record


@api_router.post("/knowledge/promotions/{promotion_id}/decision", response_model=KnowledgePromotionResponse)
def decide_knowledge_promotion(
    promotion_id: str,
    payload: KnowledgePromotionDecisionRequest,
    db: Session = Depends(get_db),
) -> KnowledgePromotionResponse:
    result = KnowledgeService(db).decide_promotion(promotion_id, payload)
    if not result:
        raise HTTPException(status_code=404, detail="Knowledge promotion not found")
    return result


@api_router.get("/{opportunity_id}/knowledge/readiness", response_model=KnowledgeReadinessResponse)
def knowledge_readiness(opportunity_id: str, db: Session = Depends(get_db)) -> KnowledgeReadinessResponse:
    return KnowledgeService(db).readiness(opportunity_id)


@web_router.get("/opportunities/{opportunity_id}/lessons", response_class=HTMLResponse)
def lessons_dashboard(opportunity_id: str, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    service = KnowledgeService(db)
    records = service.list_records(opportunity_id)
    readiness = service.readiness(opportunity_id)
    return templates.TemplateResponse(
        request=request,
        name="lessons_dashboard.html",
        context={"opportunity_id": opportunity_id, "records": records, "readiness": readiness},
    )


@web_router.post("/opportunities/{opportunity_id}/lessons")
def create_lessons_web(
    opportunity_id: str,
    outcome: str = Form(...),
    root_causes: str = Form(...),
    actions: str = Form(...),
    created_by: str = Form("operator"),
    promotion_title: str = Form(""),
    promotion_type: str = Form(""),
    promotion_rationale: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    promotions = []
    if promotion_title and promotion_type and promotion_rationale:
        promotions.append(
            {
                "asset_title": promotion_title,
                "asset_type": promotion_type,
                "rationale": promotion_rationale,
            }
        )
    payload = LessonsRecordCreateRequest(
        outcome=outcome,
        root_causes=[c.strip() for c in root_causes.splitlines() if c.strip()],
        actions=[a.strip() for a in actions.splitlines() if a.strip()],
        promotions=promotions,
        created_by=created_by,
    )
    KnowledgeService(db).create_record(opportunity_id, payload)
    return RedirectResponse(url=f"/opportunities/{opportunity_id}/lessons", status_code=303)


@web_router.post("/opportunities/{opportunity_id}/lessons/{record_id}/approve")
def approve_lessons_web(
    opportunity_id: str,
    record_id: str,
    actor: str = Form("knowledge_manager"),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    payload = LessonsRecordApproveRequest(actor=actor)
    record = KnowledgeService(db).approve_record(opportunity_id, record_id, payload)
    if not record:
        raise HTTPException(status_code=404, detail="Lessons record not found")
    return RedirectResponse(url=f"/opportunities/{opportunity_id}/lessons", status_code=303)


@web_router.post("/knowledge/promotions/{promotion_id}/decision")
def decide_knowledge_promotion_web(
    promotion_id: str,
    opportunity_id: str = Form(...),
    decision: str = Form(...),
    actor: str = Form("knowledge_manager"),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    payload = KnowledgePromotionDecisionRequest(decision=decision, actor=actor)
    result = KnowledgeService(db).decide_promotion(promotion_id, payload)
    if not result:
        raise HTTPException(status_code=404, detail="Knowledge promotion not found")
    return RedirectResponse(url=f"/opportunities/{opportunity_id}/lessons", status_code=303)

