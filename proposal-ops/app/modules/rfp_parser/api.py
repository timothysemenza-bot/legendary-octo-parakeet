from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.rfp_parser.document_reader import extract_text_from_upload
from app.modules.rfp_parser.schemas import RfpParseRequest, RfpParseResponse
from app.modules.rfp_parser.service import RfpParserService


api_router = APIRouter(prefix="/api/opportunities", tags=["rfp-parser"])
web_router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/web/templates")


@api_router.post("/{opportunity_id}/rfp/parse", response_model=RfpParseResponse)
async def parse_rfp_api(
    opportunity_id: str,
    raw_text: str | None = Form(None),
    source_filename: str = Form("manual-input.txt"),
    actor: str = Form("operator"),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
) -> RfpParseResponse:
    content = raw_text or ""
    filename = source_filename
    if file is not None:
        bytes_payload = await file.read()
        filename = file.filename or source_filename
        content = extract_text_from_upload(filename, bytes_payload)

    if len(content.strip()) < 20:
        raise HTTPException(status_code=422, detail="RFP content is too short to parse.")

    service = RfpParserService(db)
    try:
        return service.parse_and_persist(
            opportunity_id,
            RfpParseRequest(raw_text=content, source_filename=filename, actor=actor),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@web_router.get("/opportunities/{opportunity_id}/rfp-upload", response_class=HTMLResponse)
def rfp_upload_form(request: Request, opportunity_id: str) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="rfp_upload.html",
        context={"opportunity_id": opportunity_id},
    )


@web_router.post("/opportunities/{opportunity_id}/rfp-upload")
async def rfp_upload_submit(
    opportunity_id: str,
    raw_text: str = Form(""),
    actor: str = Form("operator"),
    source_filename: str = Form("manual-input.txt"),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    content = raw_text
    filename = source_filename
    if file is not None:
        payload = await file.read()
        filename = file.filename or source_filename
        content = extract_text_from_upload(filename, payload)

    if len(content.strip()) < 20:
        raise HTTPException(status_code=422, detail="RFP content is too short to parse.")

    service = RfpParserService(db)
    service.parse_and_persist(
        opportunity_id,
        RfpParseRequest(raw_text=content, source_filename=filename, actor=actor),
    )
    return RedirectResponse(url=f"/opportunities/{opportunity_id}/compliance-matrix", status_code=303)

