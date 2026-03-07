from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.review_manager.schemas import (
    ReviewCommentCreateRequest,
    ReviewCommentResolveRequest,
    ReviewCommentResponse,
    ReviewCycleCloseRequest,
    ReviewCycleCreateRequest,
    ReviewCycleResponse,
    ReviewReadinessResponse,
    ReviewSeedFromOutlineRequest,
    ReviewSeedFromOutlineResponse,
)
from app.modules.review_manager.service import ReviewManagerService, ReviewSeedConflictError


api_router = APIRouter(prefix="/api/opportunities", tags=["review-manager"])
web_router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/web/templates")


@api_router.get("/{opportunity_id}/reviews", response_model=list[ReviewCycleResponse])
def list_reviews(opportunity_id: str, db: Session = Depends(get_db)) -> list[ReviewCycleResponse]:
    service = ReviewManagerService(db)
    return [ReviewCycleResponse.model_validate(c, from_attributes=True) for c in service.list_cycles(opportunity_id)]


@api_router.post("/{opportunity_id}/reviews", response_model=ReviewCycleResponse)
def create_review(
    opportunity_id: str, payload: ReviewCycleCreateRequest, db: Session = Depends(get_db)
) -> ReviewCycleResponse:
    service = ReviewManagerService(db)
    cycle = service.create_cycle(opportunity_id, payload)
    return ReviewCycleResponse.model_validate(cycle, from_attributes=True)


@api_router.post("/{opportunity_id}/reviews/{cycle_id}/close", response_model=ReviewCycleResponse)
def close_review(
    opportunity_id: str,
    cycle_id: str,
    payload: ReviewCycleCloseRequest,
    db: Session = Depends(get_db),
) -> ReviewCycleResponse:
    service = ReviewManagerService(db)
    cycle = service.close_cycle(opportunity_id, cycle_id, payload)
    if not cycle:
        raise HTTPException(status_code=404, detail="Review cycle not found")
    return ReviewCycleResponse.model_validate(cycle, from_attributes=True)


@api_router.post(
    "/{opportunity_id}/reviews/{cycle_id}/seed-from-outline",
    response_model=ReviewSeedFromOutlineResponse,
)
def seed_review_comments_from_outline(
    opportunity_id: str,
    cycle_id: str,
    payload: ReviewSeedFromOutlineRequest,
    db: Session = Depends(get_db),
) -> ReviewSeedFromOutlineResponse:
    service = ReviewManagerService(db)
    try:
        result = service.seed_comments_from_outline(opportunity_id, cycle_id, payload)
    except ReviewSeedConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not result:
        raise HTTPException(status_code=404, detail="Review cycle not found")
    seeded_count, skipped_count = result
    return ReviewSeedFromOutlineResponse(
        review_cycle_id=cycle_id,
        seeded_count=seeded_count,
        skipped_count=skipped_count,
    )


@api_router.get("/{opportunity_id}/reviews/readiness", response_model=ReviewReadinessResponse)
def review_readiness(opportunity_id: str, db: Session = Depends(get_db)) -> ReviewReadinessResponse:
    return ReviewManagerService(db).review_readiness(opportunity_id)


@api_router.get("/reviews/{cycle_id}/comments", response_model=list[ReviewCommentResponse])
def list_review_comments(cycle_id: str, db: Session = Depends(get_db)) -> list[ReviewCommentResponse]:
    service = ReviewManagerService(db)
    return [ReviewCommentResponse.model_validate(c, from_attributes=True) for c in service.list_comments(cycle_id)]


@api_router.post("/reviews/{cycle_id}/comments", response_model=ReviewCommentResponse)
def create_review_comment(
    cycle_id: str, payload: ReviewCommentCreateRequest, db: Session = Depends(get_db)
) -> ReviewCommentResponse:
    service = ReviewManagerService(db)
    comment = service.create_comment(cycle_id, payload)
    if not comment:
        raise HTTPException(status_code=404, detail="Review cycle not found")
    return ReviewCommentResponse.model_validate(comment, from_attributes=True)


@api_router.post("/reviews/comments/{comment_id}/resolve", response_model=ReviewCommentResponse)
def resolve_review_comment(
    comment_id: str, payload: ReviewCommentResolveRequest, db: Session = Depends(get_db)
) -> ReviewCommentResponse:
    service = ReviewManagerService(db)
    comment = service.resolve_comment(comment_id, payload)
    if not comment:
        raise HTTPException(status_code=404, detail="Review comment not found")
    return ReviewCommentResponse.model_validate(comment, from_attributes=True)


@web_router.get("/opportunities/{opportunity_id}/reviews", response_class=HTMLResponse)
def review_dashboard(opportunity_id: str, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    service = ReviewManagerService(db)
    cycles = service.list_cycles(opportunity_id)
    readiness = service.review_readiness(opportunity_id)
    comments_by_cycle = {c.id: service.list_comments(c.id) for c in cycles}
    return templates.TemplateResponse(
        request=request,
        name="review_dashboard.html",
        context={
            "opportunity_id": opportunity_id,
            "cycles": cycles,
            "readiness": readiness,
            "comments_by_cycle": comments_by_cycle,
        },
    )


@web_router.post("/opportunities/{opportunity_id}/reviews")
def create_review_web(
    opportunity_id: str,
    review_type: str = Form(...),
    round_number: int = Form(1),
    actor: str = Form("operator"),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    payload = ReviewCycleCreateRequest(review_type=review_type, round_number=round_number, actor=actor)
    ReviewManagerService(db).create_cycle(opportunity_id, payload)
    return RedirectResponse(url=f"/opportunities/{opportunity_id}/reviews", status_code=303)


@web_router.post("/opportunities/{opportunity_id}/reviews/{cycle_id}/close")
def close_review_web(
    opportunity_id: str,
    cycle_id: str,
    actor: str = Form("operator"),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    payload = ReviewCycleCloseRequest(actor=actor)
    cycle = ReviewManagerService(db).close_cycle(opportunity_id, cycle_id, payload)
    if not cycle:
        raise HTTPException(status_code=404, detail="Review cycle not found")
    return RedirectResponse(url=f"/opportunities/{opportunity_id}/reviews", status_code=303)


@web_router.post("/opportunities/{opportunity_id}/reviews/{cycle_id}/seed-from-outline")
def seed_review_comments_from_outline_web(
    opportunity_id: str,
    cycle_id: str,
    actor: str = Form("operator"),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    payload = ReviewSeedFromOutlineRequest(actor=actor)
    service = ReviewManagerService(db)
    try:
        result = service.seed_comments_from_outline(opportunity_id, cycle_id, payload)
    except ReviewSeedConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not result:
        raise HTTPException(status_code=404, detail="Review cycle not found")
    return RedirectResponse(url=f"/opportunities/{opportunity_id}/reviews", status_code=303)


@web_router.post("/reviews/{cycle_id}/comments")
def create_review_comment_web(
    cycle_id: str,
    opportunity_id: str = Form(...),
    requirement_id: str = Form(""),
    section_code: str = Form(...),
    severity: str = Form(...),
    comment_text: str = Form(...),
    owner: str = Form("UNASSIGNED"),
    created_by: str = Form("reviewer"),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    payload = ReviewCommentCreateRequest(
        requirement_id=requirement_id or None,
        section_code=section_code,
        severity=severity,
        comment_text=comment_text,
        owner=owner,
        created_by=created_by,
    )
    comment = ReviewManagerService(db).create_comment(cycle_id, payload)
    if not comment:
        raise HTTPException(status_code=404, detail="Review cycle not found")
    return RedirectResponse(url=f"/opportunities/{opportunity_id}/reviews", status_code=303)


@web_router.post("/reviews/comments/{comment_id}/resolve")
def resolve_review_comment_web(
    comment_id: str,
    opportunity_id: str = Form(...),
    actor: str = Form("reviewer"),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    payload = ReviewCommentResolveRequest(actor=actor)
    comment = ReviewManagerService(db).resolve_comment(comment_id, payload)
    if not comment:
        raise HTTPException(status_code=404, detail="Review comment not found")
    return RedirectResponse(url=f"/opportunities/{opportunity_id}/reviews", status_code=303)
