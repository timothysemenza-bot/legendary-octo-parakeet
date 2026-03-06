from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.compliance_matrix.schemas import (
    ComplianceMatrixQualityResponse,
    ComplianceMatrixRowResponse,
    ComplianceMatrixUpdateRequest,
)
from app.modules.compliance_matrix.service import ComplianceMatrixService


api_router = APIRouter(prefix="/api", tags=["compliance-matrix"])
web_router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/web/templates")


@api_router.get("/opportunities/{opportunity_id}/compliance-matrix", response_model=list[ComplianceMatrixRowResponse])
def list_compliance_matrix(
    opportunity_id: str,
    include_context: bool = False,
    db: Session = Depends(get_db),
) -> list[ComplianceMatrixRowResponse]:
    service = ComplianceMatrixService(db)
    rows = service.list_rows(opportunity_id, include_context=include_context)
    return [ComplianceMatrixRowResponse(**row) for row in rows]


@api_router.get(
    "/opportunities/{opportunity_id}/compliance-matrix/quality",
    response_model=ComplianceMatrixQualityResponse,
)
def compliance_matrix_quality(opportunity_id: str, db: Session = Depends(get_db)) -> ComplianceMatrixQualityResponse:
    service = ComplianceMatrixService(db)
    summary = service.matrix_quality(opportunity_id)
    return ComplianceMatrixQualityResponse(**summary)


@api_router.patch("/compliance-matrix/{row_id}", response_model=ComplianceMatrixRowResponse)
def update_compliance_row(
    row_id: str, payload: ComplianceMatrixUpdateRequest, db: Session = Depends(get_db)
) -> ComplianceMatrixRowResponse:
    service = ComplianceMatrixService(db)
    updated = service.update_row(
        row_id,
        proposal_section=payload.proposal_section,
        owner=payload.owner,
        status=payload.status,
        actor=payload.actor,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Matrix row not found")
    return ComplianceMatrixRowResponse(**updated)


@web_router.get("/opportunities/{opportunity_id}/compliance-matrix", response_class=HTMLResponse)
def matrix_view(
    request: Request,
    opportunity_id: str,
    include_context: bool = False,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = ComplianceMatrixService(db)
    rows = service.list_rows(opportunity_id, include_context=include_context)
    quality = service.matrix_quality(opportunity_id)
    return templates.TemplateResponse(
        request=request,
        name="compliance_matrix.html",
        context={
            "opportunity_id": opportunity_id,
            "rows": rows,
            "include_context": include_context,
            "quality": quality,
        },
    )


@web_router.post("/compliance-matrix/{row_id}")
def matrix_update_web(
    row_id: str,
    opportunity_id: str = Form(...),
    proposal_section: str = Form(...),
    owner: str = Form(...),
    status: str = Form(...),
    actor: str = Form("operator"),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    service = ComplianceMatrixService(db)
    updated = service.update_row(
        row_id,
        proposal_section=proposal_section,
        owner=owner,
        status=status,
        actor=actor,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Matrix row not found")
    return RedirectResponse(url=f"/opportunities/{opportunity_id}/compliance-matrix", status_code=303)
