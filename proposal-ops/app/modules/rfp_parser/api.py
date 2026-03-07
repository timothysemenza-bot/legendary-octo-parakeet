from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.rfp_parser.document_reader import extract_text_from_upload
from app.modules.rfp_parser.schemas import (
    RfpParseRequest,
    RfpParseResponse,
    RfpReparseRequest,
    SolicitationComparisonResponse,
    RfpSourceDocumentInput,
    SolicitationVersionRecord,
)
from app.modules.rfp_parser.service import RfpParserService


api_router = APIRouter(prefix="/api/opportunities", tags=["rfp-parser"])
web_router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/web/templates")


def _build_source_documents(
    *,
    filename: str,
    content: str,
    content_type: str | None,
    source_size_bytes: int,
    source_payload: bytes | None = None,
) -> list[RfpSourceDocumentInput]:
    return [
        RfpSourceDocumentInput(
            source_filename=filename,
            content_type=content_type or "text/plain",
            parse_status="PARSED",
            skip_reason=None,
            document_family_id=None,
            upload_order=1,
            source_size_bytes=source_size_bytes,
            extracted_text_length=len(content.strip()),
            content_text=content.strip(),
            source_payload=source_payload,
        )
    ]


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
    bytes_payload: bytes | None = None
    source_size_bytes = len(content.encode("utf-8"))
    if file is not None:
        bytes_payload = await file.read()
        filename = file.filename or source_filename
        content = extract_text_from_upload(filename, bytes_payload)
        source_size_bytes = len(bytes_payload)

    if len(content.strip()) < 20:
        raise HTTPException(status_code=422, detail="RFP content is too short to parse.")

    service = RfpParserService(db)
    try:
        return service.parse_and_persist(
            opportunity_id,
            RfpParseRequest(
                raw_text=content,
                source_filename=filename,
                actor=actor,
                source_documents=_build_source_documents(
                    filename=filename,
                    content=content,
                    content_type=file.content_type if file is not None else "text/plain",
                    source_size_bytes=source_size_bytes,
                    source_payload=bytes_payload if file is not None else None,
                ),
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@api_router.get("/{opportunity_id}/rfp/versions", response_model=list[SolicitationVersionRecord])
def list_rfp_versions_api(
    opportunity_id: str,
    db: Session = Depends(get_db),
) -> list[SolicitationVersionRecord]:
    return RfpParserService(db).list_versions(opportunity_id)


@api_router.post("/{opportunity_id}/rfp/reparse", response_model=RfpParseResponse)
def reparse_rfp_api(
    opportunity_id: str,
    payload: RfpReparseRequest,
    db: Session = Depends(get_db),
) -> RfpParseResponse:
    service = RfpParserService(db)
    try:
        return service.reparse_solicitation(opportunity_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@api_router.post("/{opportunity_id}/rfp/reparse-document-set", response_model=RfpParseResponse)
async def reparse_rfp_document_set_api(
    opportunity_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> RfpParseResponse:
    form = await request.form()
    actor = str(form.get("actor", "operator"))
    source_solicitation_id = str(form.get("source_solicitation_id", "")).strip()
    retain_document_ids = [str(item) for item in form.getlist("retain_document_ids") if str(item).strip()]
    uploads: list[tuple[str, bytes]] = []
    for item in form.getlist("files"):
        if not hasattr(item, "read") or not hasattr(item, "filename"):
            continue
        payload = await item.read()
        uploads.append((item.filename or "uploaded-document.txt", payload))

    service = RfpParserService(db)
    try:
        return service.reparse_with_document_set(
            opportunity_id,
            actor=actor,
            source_solicitation_id=source_solicitation_id or None,
            retained_document_ids=retain_document_ids,
            uploads=uploads,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@api_router.get("/{opportunity_id}/rfp/source-documents/{source_document_id}/download")
def download_rfp_source_document_api(
    opportunity_id: str,
    source_document_id: str,
    db: Session = Depends(get_db),
) -> FileResponse:
    result = RfpParserService(db).get_source_document_download_path(opportunity_id, source_document_id)
    if not result:
        raise HTTPException(status_code=404, detail="Stored source document not found.")
    path, filename = result
    return FileResponse(path, filename=filename, media_type="application/octet-stream")


@api_router.post("/{opportunity_id}/rfp/source-documents/{source_document_id}/replace", response_model=RfpParseResponse)
async def replace_rfp_source_document_api(
    opportunity_id: str,
    source_document_id: str,
    actor: str = Form("operator"),
    source_solicitation_id: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> RfpParseResponse:
    payload = await file.read()
    service = RfpParserService(db)
    try:
        return service.replace_source_document(
            opportunity_id,
            actor=actor,
            source_solicitation_id=source_solicitation_id or None,
            source_document_id=source_document_id,
            replacement_upload=(file.filename or "replacement-document.txt", payload),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@api_router.get("/{opportunity_id}/rfp/compare", response_model=SolicitationComparisonResponse)
def compare_rfp_versions_api(
    opportunity_id: str,
    base_solicitation_id: str,
    compare_solicitation_id: str,
    db: Session = Depends(get_db),
) -> SolicitationComparisonResponse:
    service = RfpParserService(db)
    try:
        return service.compare_versions(
            opportunity_id,
            base_solicitation_id=base_solicitation_id,
            compare_solicitation_id=compare_solicitation_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@web_router.get("/opportunities/{opportunity_id}/rfp-upload", response_class=HTMLResponse)
def rfp_upload_form(
    request: Request,
    opportunity_id: str,
    base_solicitation_id: str | None = None,
    compare_solicitation_id: str | None = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = RfpParserService(db)
    versions = service.list_versions(opportunity_id)
    comparison = None
    selected_base_id = base_solicitation_id
    selected_compare_id = compare_solicitation_id
    if len(versions) >= 2 and not (selected_base_id and selected_compare_id):
        selected_base_id = versions[1].solicitation_id
        selected_compare_id = versions[0].solicitation_id
    if selected_base_id and selected_compare_id:
        try:
            comparison = service.compare_versions(
                opportunity_id,
                base_solicitation_id=selected_base_id,
                compare_solicitation_id=selected_compare_id,
            )
        except ValueError:
            comparison = None
    return templates.TemplateResponse(
        request=request,
        name="rfp_upload.html",
        context={
            "opportunity_id": opportunity_id,
            "versions": versions,
            "comparison": comparison,
            "selected_base_id": selected_base_id,
            "selected_compare_id": selected_compare_id,
        },
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
    file_payload: bytes | None = None
    source_size_bytes = len(content.encode("utf-8"))
    if file is not None:
        file_payload = await file.read()
        filename = file.filename or source_filename
        content = extract_text_from_upload(filename, file_payload)
        source_size_bytes = len(file_payload)

    if len(content.strip()) < 20:
        raise HTTPException(status_code=422, detail="RFP content is too short to parse.")

    service = RfpParserService(db)
    service.parse_and_persist(
        opportunity_id,
        RfpParseRequest(
            raw_text=content,
            source_filename=filename,
            actor=actor,
            source_documents=_build_source_documents(
                filename=filename,
                content=content,
                content_type=file.content_type if file is not None else "text/plain",
                source_size_bytes=source_size_bytes,
                source_payload=file_payload,
            ),
        ),
    )
    return RedirectResponse(url=f"/opportunities/{opportunity_id}/compliance-matrix", status_code=303)


@web_router.post("/opportunities/{opportunity_id}/rfp/reparse")
def rfp_reparse_submit(
    opportunity_id: str,
    actor: str = Form("operator"),
    source_solicitation_id: str = Form(""),
    include_parsed_only: str = Form("false"),
    override_source_filename: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    service = RfpParserService(db)
    try:
        source_documents: list[RfpSourceDocumentInput] = []
        if source_solicitation_id:
            source_rows = service.list_source_documents_for_solicitation(source_solicitation_id)
            for idx, row in enumerate(source_rows, start=1):
                if include_parsed_only == "true" and row.parse_status != "PARSED":
                    continue
                source_documents.append(
                    RfpSourceDocumentInput(
                        source_filename=override_source_filename or row.source_filename,
                        content_type=row.content_type,
                        parse_status=row.parse_status,
                        skip_reason=row.skip_reason,
                        document_family_id=row.document_family_id,
                        upload_order=idx,
                        source_size_bytes=row.source_size_bytes,
                        extracted_text_length=row.extracted_text_length,
                        content_text=row.content_text,
                        source_sha256=row.source_sha256,
                        storage_path=row.storage_path,
                    )
                )
            service.reparse_solicitation(
                opportunity_id,
                RfpReparseRequest(
                    actor=actor,
                    source_solicitation_id=source_solicitation_id or None,
                    source_documents=source_documents,
                ),
            )
        else:
            service.reparse_solicitation(
                opportunity_id,
                RfpReparseRequest(
                    actor=actor,
                    source_solicitation_id=None,
                ),
            )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return RedirectResponse(url=f"/opportunities/{opportunity_id}/compliance-matrix", status_code=303)


@web_router.post("/opportunities/{opportunity_id}/rfp/reparse-document-set")
async def rfp_reparse_document_set_submit(
    opportunity_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    form = await request.form()
    actor = str(form.get("actor", "operator"))
    source_solicitation_id = str(form.get("source_solicitation_id", "")).strip()
    retain_document_ids = [str(item) for item in form.getlist("retain_document_ids") if str(item).strip()]
    uploads: list[tuple[str, bytes]] = []
    for item in form.getlist("files"):
        if not hasattr(item, "read") or not hasattr(item, "filename"):
            continue
        payload = await item.read()
        uploads.append((item.filename or "uploaded-document.txt", payload))

    service = RfpParserService(db)
    try:
        service.reparse_with_document_set(
            opportunity_id,
            actor=actor,
            source_solicitation_id=source_solicitation_id or None,
            retained_document_ids=retain_document_ids,
            uploads=uploads,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RedirectResponse(url=f"/opportunities/{opportunity_id}/compliance-matrix", status_code=303)


@web_router.post("/opportunities/{opportunity_id}/rfp/source-documents/{source_document_id}/replace")
async def rfp_replace_source_document_submit(
    opportunity_id: str,
    source_document_id: str,
    actor: str = Form("operator"),
    source_solicitation_id: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    payload = await file.read()
    service = RfpParserService(db)
    try:
        service.replace_source_document(
            opportunity_id,
            actor=actor,
            source_solicitation_id=source_solicitation_id or None,
            source_document_id=source_document_id,
            replacement_upload=(file.filename or "replacement-document.txt", payload),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RedirectResponse(url=f"/opportunities/{opportunity_id}/compliance-matrix", status_code=303)
