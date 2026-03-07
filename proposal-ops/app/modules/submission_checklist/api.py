from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.submission_checklist.schemas import (
    FileNameValidationRequest,
    FileNameValidationResponse,
    SubmissionChecklistItemResponse,
    SubmissionChecklistItemUpdateRequest,
    SubmissionPackageValidationRequest,
    SubmissionPackageValidationResponse,
    SubmissionChecklistResponse,
    SubmissionReadinessResponse,
)
from app.modules.submission_checklist.service import SubmissionChecklistService


api_router = APIRouter(prefix="/api/opportunities", tags=["submission-checklist"])
web_router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/web/templates")


@api_router.get("/{opportunity_id}/submission/checklist", response_model=SubmissionChecklistResponse)
def get_submission_checklist(opportunity_id: str, db: Session = Depends(get_db)) -> SubmissionChecklistResponse:
    service = SubmissionChecklistService(db)
    checklist, items = service.list_checklist_items(opportunity_id)
    return SubmissionChecklistResponse(
        checklist_id=checklist.id,
        opportunity_id=opportunity_id,
        status=checklist.status,
        items=[SubmissionChecklistItemResponse.model_validate(i, from_attributes=True) for i in items],
    )


@api_router.patch(
    "/{opportunity_id}/submission/checklist/items/{item_id}",
    response_model=SubmissionChecklistItemResponse,
)
def update_submission_item(
    opportunity_id: str,
    item_id: str,
    payload: SubmissionChecklistItemUpdateRequest,
    db: Session = Depends(get_db),
) -> SubmissionChecklistItemResponse:
    item = SubmissionChecklistService(db).update_item(opportunity_id, item_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    return SubmissionChecklistItemResponse.model_validate(item, from_attributes=True)


@api_router.post("/{opportunity_id}/submission/validate-filenames", response_model=FileNameValidationResponse)
def validate_submission_filenames(
    opportunity_id: str,
    payload: FileNameValidationRequest,
    db: Session = Depends(get_db),
) -> FileNameValidationResponse:
    return SubmissionChecklistService(db).validate_file_names(opportunity_id, payload)


@api_router.post("/{opportunity_id}/submission/validate-package", response_model=SubmissionPackageValidationResponse)
def validate_submission_package(
    opportunity_id: str,
    payload: SubmissionPackageValidationRequest,
    db: Session = Depends(get_db),
) -> SubmissionPackageValidationResponse:
    return SubmissionChecklistService(db).validate_package_structure(opportunity_id, payload)


@api_router.get("/{opportunity_id}/submission/readiness", response_model=SubmissionReadinessResponse)
def submission_readiness(opportunity_id: str, db: Session = Depends(get_db)) -> SubmissionReadinessResponse:
    return SubmissionChecklistService(db).readiness(opportunity_id)


@web_router.get("/opportunities/{opportunity_id}/submission", response_class=HTMLResponse)
def submission_dashboard(opportunity_id: str, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    service = SubmissionChecklistService(db)
    checklist, items = service.list_checklist_items(opportunity_id)
    readiness = service.readiness(opportunity_id)
    return templates.TemplateResponse(
        request=request,
        name="submission_dashboard.html",
        context={
            "opportunity_id": opportunity_id,
            "checklist": checklist,
            "items": items,
            "readiness": readiness,
        },
    )


@web_router.post("/opportunities/{opportunity_id}/submission/items/{item_id}")
def update_submission_item_web(
    opportunity_id: str,
    item_id: str,
    status: str = Form(...),
    details: str = Form(""),
    actor: str = Form("operator"),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    payload = SubmissionChecklistItemUpdateRequest(status=status, details=details or None, actor=actor)
    item = SubmissionChecklistService(db).update_item(opportunity_id, item_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    return RedirectResponse(url=f"/opportunities/{opportunity_id}/submission", status_code=303)


@web_router.post("/opportunities/{opportunity_id}/submission/validate-filenames")
def validate_submission_filenames_web(
    opportunity_id: str,
    file_names: str = Form(""),
    actor: str = Form("operator"),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    parsed = [n.strip() for n in file_names.splitlines() if n.strip()]
    payload = FileNameValidationRequest(file_names=parsed, actor=actor)
    SubmissionChecklistService(db).validate_file_names(opportunity_id, payload)
    return RedirectResponse(url=f"/opportunities/{opportunity_id}/submission", status_code=303)


@web_router.post("/opportunities/{opportunity_id}/submission/validate-package")
def validate_submission_package_web(
    opportunity_id: str,
    section_names: str = Form(""),
    actor: str = Form("operator"),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    parsed = [name.strip() for name in section_names.splitlines() if name.strip()]
    payload = SubmissionPackageValidationRequest(section_names=parsed, actor=actor)
    SubmissionChecklistService(db).validate_package_structure(opportunity_id, payload)
    return RedirectResponse(url=f"/opportunities/{opportunity_id}/submission", status_code=303)
