from enum import StrEnum

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.params import Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.web.example_presets import select_example_presets
from app.web.templating import build_templates
from app.modules.janitorial_os.service import JanitorialOsService
from app.modules.opportunity_intelligence.schemas import (
    ConfidenceLevel,
    HypothesisStage,
    HypothesisConversionCreate,
    HypothesisConversionResponse,
    OpportunityHypothesisCreate,
    OpportunityHypothesisResponse,
    OpportunityIntelligenceSummaryResponse,
    SignalEventCreate,
    SignalEventResponse,
    SignalEventType,
    SignalSourceCreate,
    SignalSourceResponse,
    SignalSourceType,
)
from app.modules.opportunity_intake.schemas import PursuitStage
from app.modules.opportunity_intelligence.service import OpportunityIntelligenceService


api_router = APIRouter(prefix="/api/intelligence", tags=["opportunity-intelligence"])
web_router = APIRouter(tags=["web"])
templates = build_templates()


def _choice_label(value: str) -> str:
    return value if any(char.islower() for char in value) else value.replace("_", " ").title()


def _choice_token(value: str) -> str:
    return str(value).strip().upper().replace("-", "_").replace("/", "_").replace(" ", "_")


def _enum_options(enum_cls: type[StrEnum]) -> list[dict[str, str]]:
    return [{"value": item.value, "label": _choice_label(item.value)} for item in enum_cls]


INTELLIGENCE_FORM_OPTIONS = {
    "source_types": _enum_options(SignalSourceType),
    "signal_types": _enum_options(SignalEventType),
    "hypothesis_stages": _enum_options(HypothesisStage),
    "confidence_levels": _enum_options(ConfidenceLevel),
    "pursuit_stages": _enum_options(PursuitStage),
}


def _validation_errors(exc: ValidationError) -> list[str]:
    return [f"{str(issue['loc'][-1]).replace('_', ' ').title()}: {issue['msg']}" for issue in exc.errors()]


def _validation_field_names(exc: ValidationError) -> list[str]:
    return sorted({str(issue["loc"][-1]) for issue in exc.errors() if issue.get("loc")})


def _ux_validation_context(
    *,
    page_key: str,
    form_name: str,
    errors: list[str],
    field_names: list[str] | None = None,
) -> dict[str, object]:
    return {
        "page_key": page_key,
        "form_name": form_name,
        "error_count": len(errors),
        "field_names": field_names or [],
    }


def _intelligence_context(
    service: OpportunityIntelligenceService,
    *,
    errors: list[str] | None = None,
    source_form_data: dict[str, object] | None = None,
    event_form_data: dict[str, object] | None = None,
    hypothesis_form_data: dict[str, object] | None = None,
    conversion_form_data: dict[str, dict[str, object]] | None = None,
) -> dict[str, object]:
    janitorial_service = JanitorialOsService(service.db)
    sources = service.list_signal_sources()
    signals = service.list_signal_events()
    hypotheses = service.list_opportunity_hypotheses()
    contractors = janitorial_service.list_contractors()
    organizations = janitorial_service.list_organizations()
    return {
        "summary": service.summary(),
        "sources": [service._source_response(row) for row in sources],
        "signal_events": [service._signal_response(row) for row in signals[:12]],
        "hypotheses": [service._hypothesis_response(row) for row in hypotheses[:12]],
        "contractors": contractors,
        "organizations": organizations,
        "errors": errors or [],
        "source_form_data": source_form_data or {},
        "event_form_data": event_form_data or {},
        "hypothesis_form_data": hypothesis_form_data or {},
        "conversion_form_data": conversion_form_data or {},
        "form_options": INTELLIGENCE_FORM_OPTIONS,
        "example_presets": select_example_presets(
            "signal_source_create",
            "signal_event_create",
            "opportunity_hypothesis_create",
        ),
    }


@api_router.get("/sources", response_model=list[SignalSourceResponse])
def list_signal_sources(db: Session = Depends(get_db)) -> list[SignalSourceResponse]:
    service = OpportunityIntelligenceService(db)
    return [service._source_response(row) for row in service.list_signal_sources()]


@api_router.post("/sources", response_model=SignalSourceResponse)
def create_signal_source(payload: SignalSourceCreate, db: Session = Depends(get_db)) -> SignalSourceResponse:
    service = OpportunityIntelligenceService(db)
    try:
        row = service.create_signal_source(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return service._source_response(row)


@api_router.get("/signals", response_model=list[SignalEventResponse])
def list_signal_events(db: Session = Depends(get_db)) -> list[SignalEventResponse]:
    service = OpportunityIntelligenceService(db)
    return [service._signal_response(row) for row in service.list_signal_events()]


@api_router.post("/signals", response_model=SignalEventResponse)
def create_signal_event(payload: SignalEventCreate, db: Session = Depends(get_db)) -> SignalEventResponse:
    service = OpportunityIntelligenceService(db)
    try:
        row = service.create_signal_event(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return service._signal_response(row)


@api_router.get("/hypotheses", response_model=list[OpportunityHypothesisResponse])
def list_opportunity_hypotheses(db: Session = Depends(get_db)) -> list[OpportunityHypothesisResponse]:
    service = OpportunityIntelligenceService(db)
    return [service._hypothesis_response(row) for row in service.list_opportunity_hypotheses()]


@api_router.post("/hypotheses", response_model=OpportunityHypothesisResponse)
def create_opportunity_hypothesis(
    payload: OpportunityHypothesisCreate,
    db: Session = Depends(get_db),
) -> OpportunityHypothesisResponse:
    service = OpportunityIntelligenceService(db)
    try:
        row = service.create_opportunity_hypothesis(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return service._hypothesis_response(row)


@api_router.post("/hypotheses/{hypothesis_id}/convert-to-pursuit", response_model=HypothesisConversionResponse)
def convert_hypothesis_to_pursuit(
    hypothesis_id: str,
    payload: HypothesisConversionCreate,
    db: Session = Depends(get_db),
) -> HypothesisConversionResponse:
    service = OpportunityIntelligenceService(db)
    try:
        return service.convert_hypothesis_to_pursuit(hypothesis_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@api_router.get("/summary", response_model=OpportunityIntelligenceSummaryResponse)
def opportunity_intelligence_summary(db: Session = Depends(get_db)) -> OpportunityIntelligenceSummaryResponse:
    return OpportunityIntelligenceService(db).summary()


@web_router.get("/intelligence", response_class=HTMLResponse)
def opportunity_intelligence_view(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    service = OpportunityIntelligenceService(db)
    return templates.TemplateResponse(
        request=request,
        name="opportunity_intelligence.html",
        context=_intelligence_context(service),
    )


@web_router.post("/intelligence/sources")
def create_signal_source_web(
    request: Request,
    name: str = Form(...),
    source_type: str = Form("OTHER"),
    region: str = Form(""),
    owner_scope: str = Form(""),
    source_url: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
) -> Response:
    service = OpportunityIntelligenceService(db)
    raw = {
        "name": name,
        "source_type": source_type,
        "region": region or None,
        "owner_scope": owner_scope or None,
        "source_url": source_url or None,
        "notes": notes or None,
    }
    try:
        payload = SignalSourceCreate.model_validate(raw)
        service.create_signal_source(payload)
        return RedirectResponse(url="/intelligence", status_code=303)
    except (ValidationError, ValueError) as exc:
        errors = _validation_errors(exc) if isinstance(exc, ValidationError) else [str(exc)]
        return templates.TemplateResponse(
            request=request,
            name="opportunity_intelligence.html",
            context={
                **_intelligence_context(service, errors=errors, source_form_data=raw),
                "ux_validation_context": _ux_validation_context(
                    page_key="/intelligence",
                    form_name="signal_source_create",
                    errors=errors,
                    field_names=_validation_field_names(exc) if isinstance(exc, ValidationError) else [],
                ),
            },
            status_code=422,
        )


@web_router.post("/intelligence/signals")
def create_signal_event_web(
    request: Request,
    source_id: str = Form(...),
    title: str = Form(...),
    signal_type: str = Form("OTHER"),
    signal_date: str = Form(...),
    jurisdiction: str = Form(""),
    agency_name: str = Form(""),
    program_name: str = Form(""),
    summary: str = Form(...),
    confidence_level: str = Form("MEDIUM"),
    source_url: str = Form(""),
    source_reference: str = Form(""),
    recommended_action: str = Form(""),
    db: Session = Depends(get_db),
) -> Response:
    service = OpportunityIntelligenceService(db)
    raw = {
        "source_id": source_id,
        "title": title,
        "signal_type": signal_type,
        "signal_date": signal_date,
        "jurisdiction": jurisdiction or None,
        "agency_name": agency_name or None,
        "program_name": program_name or None,
        "summary": summary,
        "confidence_level": confidence_level,
        "source_url": source_url or None,
        "source_reference": source_reference or None,
        "recommended_action": recommended_action or None,
    }
    try:
        payload = SignalEventCreate.model_validate(raw)
        service.create_signal_event(payload)
        return RedirectResponse(url="/intelligence", status_code=303)
    except (ValidationError, ValueError) as exc:
        errors = _validation_errors(exc) if isinstance(exc, ValidationError) else [str(exc)]
        return templates.TemplateResponse(
            request=request,
            name="opportunity_intelligence.html",
            context={
                **_intelligence_context(service, errors=errors, event_form_data=raw),
                "ux_validation_context": _ux_validation_context(
                    page_key="/intelligence",
                    form_name="signal_event_create",
                    errors=errors,
                    field_names=_validation_field_names(exc) if isinstance(exc, ValidationError) else [],
                ),
            },
            status_code=422,
        )


@web_router.post("/intelligence/hypotheses")
def create_opportunity_hypothesis_web(
    request: Request,
    title: str = Form(...),
    sector: str = Form(""),
    geography: str = Form(""),
    buying_organization_id: str = Form(""),
    buying_organization: str = Form(""),
    service_line: str = Form(""),
    stage: str = Form("MONITORING"),
    confidence_level: str = Form("MEDIUM"),
    expected_release_start: str = Form(""),
    expected_release_end: str = Form(""),
    summary: str = Form(...),
    recommended_action: str = Form(""),
    primary_signal_event_id: str = Form(""),
    recommended_contractor_id: str = Form(""),
    db: Session = Depends(get_db),
) -> Response:
    service = OpportunityIntelligenceService(db)
    raw = {
        "title": title,
        "sector": sector or None,
        "geography": geography or None,
        "buying_organization_id": buying_organization_id or None,
        "buying_organization": buying_organization or None,
        "service_line": service_line or None,
        "stage": stage,
        "confidence_level": confidence_level,
        "expected_release_start": expected_release_start or None,
        "expected_release_end": expected_release_end or None,
        "summary": summary,
        "recommended_action": recommended_action or None,
        "primary_signal_event_id": primary_signal_event_id or None,
        "recommended_contractor_id": recommended_contractor_id or None,
    }
    try:
        payload = OpportunityHypothesisCreate.model_validate(raw)
        service.create_opportunity_hypothesis(payload)
        return RedirectResponse(url="/intelligence", status_code=303)
    except (ValidationError, ValueError) as exc:
        errors = _validation_errors(exc) if isinstance(exc, ValidationError) else [str(exc)]
        return templates.TemplateResponse(
            request=request,
            name="opportunity_intelligence.html",
            context={
                **_intelligence_context(service, errors=errors, hypothesis_form_data=raw),
                "ux_validation_context": _ux_validation_context(
                    page_key="/intelligence",
                    form_name="opportunity_hypothesis_create",
                    errors=errors,
                    field_names=_validation_field_names(exc) if isinstance(exc, ValidationError) else [],
                ),
            },
            status_code=422,
        )


@web_router.post("/intelligence/hypotheses/{hypothesis_id}/convert-to-pursuit")
def convert_hypothesis_to_pursuit_web(
    request: Request,
    hypothesis_id: str,
    name: str = Form(""),
    client_name: str = Form(""),
    contractor_id: str = Form(""),
    estimated_contract_value: str = Form(...),
    lead_time_days: str = Form(""),
    incumbent_status: bool = Form(False),
    strategic_alignment: str = Form("3"),
    estimated_probability_win: str = Form(""),
    pursuit_stage: str = Form("EARLY_QUALIFICATION"),
    expected_rfp_date: str = Form(""),
    actor: str = Form("operator"),
    db: Session = Depends(get_db),
) -> Response:
    service = OpportunityIntelligenceService(db)
    raw = {
        "name": name or None,
        "client_name": client_name or None,
        "contractor_id": contractor_id or None,
        "estimated_contract_value": estimated_contract_value,
        "lead_time_days": lead_time_days or None,
        "incumbent_status": incumbent_status,
        "strategic_alignment": strategic_alignment,
        "estimated_probability_win": estimated_probability_win or None,
        "pursuit_stage": pursuit_stage,
        "expected_rfp_date": expected_rfp_date or None,
        "actor": actor,
    }
    try:
        payload = HypothesisConversionCreate.model_validate(raw)
        result = service.convert_hypothesis_to_pursuit(hypothesis_id, payload)
        return RedirectResponse(url=f"/opportunities/{result.opportunity.id}/capture-workbench", status_code=303)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValidationError, ValueError) as exc:
        errors = _validation_errors(exc) if isinstance(exc, ValidationError) else [str(exc)]
        return templates.TemplateResponse(
            request=request,
            name="opportunity_intelligence.html",
            context={
                **_intelligence_context(
                    service,
                    errors=errors,
                    conversion_form_data={hypothesis_id: raw},
                ),
                "ux_validation_context": _ux_validation_context(
                    page_key="/intelligence",
                    form_name="hypothesis_convert_to_pursuit",
                    errors=errors,
                    field_names=_validation_field_names(exc) if isinstance(exc, ValidationError) else [],
                ),
            },
            status_code=422,
        )
