import json
from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.janitorial_os.models import (
    CommercialEngagement,
    ContractRecord,
    Contractor,
    ContractorTouchpoint,
    Facility,
    OpportunityMatch,
    Organization,
)
from app.modules.janitorial_os.schemas import (
    CaptureActionCreate,
    CaptureActionResponse,
    CommercialCreate,
    CommercialResponse,
    ContactCreate,
    ContactResponse,
    ContractRecordCreate,
    ContractRecordResponse,
    ContractRecordUpdate,
    ContractorLaborProfile,
    ContractorProspectStage,
    ContractorCreate,
    ContractorResponse,
    ContractorScaleBand,
    ContractorTouchpointCreate,
    ContractorTouchpointResponse,
    ContractorTouchpointType,
    ContractorUnionProfile,
    ContractorUpdate,
    CreatePursuitFromContractRequest,
    DashboardSummaryResponse,
    EvidenceRecordCreate,
    EvidenceRecordResponse,
    FacilityCreate,
    FacilityResponse,
    FacilityUpdate,
    IntelligenceNoteCreate,
    IntelligenceNoteResponse,
    MatchFactorResponse,
    OpportunityMatchResponse,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
    ProfileType,
    ScoringProfileResponse,
    ScoringProfileUpdateRequest,
)
from app.modules.janitorial_os.service import JanitorialOsService
from app.modules.opportunity_intake.schemas import OpportunityDetailResponse
from app.modules.opportunity_intake.service import OpportunityIntakeService


api_router = APIRouter(tags=["janitorial-os"])
web_router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/web/templates")


def _choice_label(value: str) -> str:
    return value if any(char.islower() for char in value) else value.replace("_", " ").title()


def _enum_options(enum_cls: type) -> list[dict[str, str]]:
    return [{"value": item.value, "label": _choice_label(item.value)} for item in enum_cls]


CONTRACTOR_FORM_OPTIONS = {
    "labor_profiles": _enum_options(ContractorLaborProfile),
    "union_profiles": _enum_options(ContractorUnionProfile),
    "scale_bands": _enum_options(ContractorScaleBand),
    "prospect_stages": _enum_options(ContractorProspectStage),
    "touchpoint_types": _enum_options(ContractorTouchpointType),
    "score_choices": [{"value": str(value), "label": str(value)} for value in range(1, 6)],
}


def _with_contractor_form_options(context: dict) -> dict:
    return {**context, "form_options": CONTRACTOR_FORM_OPTIONS}


def _organization_response(row: Organization) -> OrganizationResponse:
    return OrganizationResponse.model_validate(row, from_attributes=True)


def _facility_response(db: Session, row: Facility) -> FacilityResponse:
    organization = db.get(Organization, row.organization_id)
    return FacilityResponse(
        id=row.id,
        organization_id=row.organization_id,
        parent_facility_id=row.parent_facility_id,
        name=row.name,
        facility_kind=row.facility_kind,
        facility_type=row.facility_type,
        city=row.city,
        state=row.state,
        service_complexity=row.service_complexity,
        square_footage=row.square_footage,
        notes=row.notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
        organization_name=organization.name if organization else None,
    )


def _contractor_response(row: Contractor) -> ContractorResponse:
    return ContractorResponse.model_validate(row, from_attributes=True)


def _touchpoint_response(row: ContractorTouchpoint) -> ContractorTouchpointResponse:
    return ContractorTouchpointResponse.model_validate(row, from_attributes=True)


def _match_response(row: OpportunityMatch) -> OpportunityMatchResponse:
    factors = [MatchFactorResponse.model_validate(item) for item in json.loads(row.explanation_json)]
    contractor = row.contractor
    return OpportunityMatchResponse(
        contractor_id=row.contractor_id,
        contractor_name=contractor.name if contractor else "Unknown",
        match_score=row.match_score,
        factors=factors,
        updated_at=row.updated_at,
    )


def _contact_response(row: object) -> ContactResponse:
    return ContactResponse.model_validate(row, from_attributes=True)


def _note_response(row) -> IntelligenceNoteResponse:
    return IntelligenceNoteResponse.model_validate(row, from_attributes=True)


def _evidence_response(row) -> EvidenceRecordResponse:
    return EvidenceRecordResponse.model_validate(row, from_attributes=True)


def _action_response(row) -> CaptureActionResponse:
    return CaptureActionResponse.model_validate(row, from_attributes=True)


def _commercial_response(db: Session, row: CommercialEngagement) -> CommercialResponse:
    contractor = db.get(Contractor, row.contractor_id) if row.contractor_id else None
    return CommercialResponse(
        id=row.id,
        opportunity_id=row.opportunity_id,
        contractor_id=row.contractor_id,
        contractor_name=contractor.name if contractor else None,
        retainer_amount=row.retainer_amount,
        success_fee_type=row.success_fee_type,
        success_fee_value=row.success_fee_value,
        projected_payout_date=row.projected_payout_date,
        projected_payout_amount=row.projected_payout_amount,
        weighted_expected_value=row.weighted_expected_value,
        realized_revenue=row.realized_revenue,
        notes=row.notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _parse_contract_form(
    *,
    organization_id: str,
    title: str,
    incumbent_vendor: str,
    estimated_annual_value: str,
    estimated_total_value: str,
    start_date: str,
    expiration_date: str,
    rebid_window_start: str,
    rebid_window_end: str,
    procurement_source_url: str,
    source_type: str,
    source_notes: str,
    facility_ids: list[str] | None,
) -> ContractRecordCreate:
    return ContractRecordCreate.model_validate(
        {
            "organization_id": organization_id,
            "title": title,
            "incumbent_vendor": incumbent_vendor or None,
            "estimated_annual_value": estimated_annual_value or None,
            "estimated_total_value": estimated_total_value or None,
            "start_date": start_date or None,
            "expiration_date": expiration_date or None,
            "rebid_window_start": rebid_window_start or None,
            "rebid_window_end": rebid_window_end or None,
            "procurement_source_url": procurement_source_url or None,
            "source_type": source_type or "PUBLIC",
            "source_notes": source_notes or None,
            "facility_ids": facility_ids or [],
        }
    )


def _validation_errors(exc: ValidationError) -> list[str]:
    return [f"{str(issue['loc'][-1]).replace('_', ' ').title()}: {issue['msg']}" for issue in exc.errors()]


@api_router.get("/api/organizations", response_model=list[OrganizationResponse])
def list_organizations(db: Session = Depends(get_db)) -> list[OrganizationResponse]:
    service = JanitorialOsService(db)
    return [_organization_response(row) for row in service.list_organizations()]


@api_router.post("/api/organizations", response_model=OrganizationResponse)
def create_organization(payload: OrganizationCreate, db: Session = Depends(get_db)) -> OrganizationResponse:
    service = JanitorialOsService(db)
    try:
        return _organization_response(service.create_organization(payload))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@api_router.get("/api/organizations/{organization_id}", response_model=OrganizationResponse)
def get_organization(organization_id: str, db: Session = Depends(get_db)) -> OrganizationResponse:
    service = JanitorialOsService(db)
    organization = service.get_organization(organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return _organization_response(organization)


@api_router.put("/api/organizations/{organization_id}", response_model=OrganizationResponse)
def update_organization(
    organization_id: str, payload: OrganizationUpdate, db: Session = Depends(get_db)
) -> OrganizationResponse:
    service = JanitorialOsService(db)
    try:
        return _organization_response(service.update_organization(organization_id, payload))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@api_router.get("/api/facilities", response_model=list[FacilityResponse])
def list_facilities(db: Session = Depends(get_db)) -> list[FacilityResponse]:
    service = JanitorialOsService(db)
    return [_facility_response(db, row) for row in service.list_facilities()]


@api_router.post("/api/facilities", response_model=FacilityResponse)
def create_facility(payload: FacilityCreate, db: Session = Depends(get_db)) -> FacilityResponse:
    service = JanitorialOsService(db)
    try:
        return _facility_response(db, service.create_facility(payload))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@api_router.get("/api/facilities/{facility_id}", response_model=FacilityResponse)
def get_facility(facility_id: str, db: Session = Depends(get_db)) -> FacilityResponse:
    service = JanitorialOsService(db)
    facility = service.get_facility(facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return _facility_response(db, facility)


@api_router.put("/api/facilities/{facility_id}", response_model=FacilityResponse)
def update_facility(facility_id: str, payload: FacilityUpdate, db: Session = Depends(get_db)) -> FacilityResponse:
    service = JanitorialOsService(db)
    try:
        return _facility_response(db, service.update_facility(facility_id, payload))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@api_router.get("/api/contracts", response_model=list[ContractRecordResponse])
def list_contracts(
    state: str | None = Query(None),
    facility_kind: str | None = Query(None),
    incumbent: str | None = Query(None),
    rebid_within_days: int | None = Query(None, ge=1),
    db: Session = Depends(get_db),
) -> list[ContractRecordResponse]:
    service = JanitorialOsService(db)
    return [
        service.get_contract_response(row.id)
        for row in service.list_contracts(
            state=state,
            facility_kind=facility_kind,
            incumbent=incumbent,
            rebid_within_days=rebid_within_days,
        )
        if service.get_contract_response(row.id) is not None
    ]


@api_router.post("/api/contracts", response_model=ContractRecordResponse)
def create_contract(payload: ContractRecordCreate, db: Session = Depends(get_db)) -> ContractRecordResponse:
    service = JanitorialOsService(db)
    try:
        contract = service.create_contract(payload)
        response = service.get_contract_response(contract.id)
        assert response is not None
        return response
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@api_router.get("/api/contracts/{contract_id}", response_model=ContractRecordResponse)
def get_contract(contract_id: str, db: Session = Depends(get_db)) -> ContractRecordResponse:
    service = JanitorialOsService(db)
    response = service.get_contract_response(contract_id)
    if not response:
        raise HTTPException(status_code=404, detail="Contract not found")
    return response


@api_router.put("/api/contracts/{contract_id}", response_model=ContractRecordResponse)
def update_contract(contract_id: str, payload: ContractRecordUpdate, db: Session = Depends(get_db)) -> ContractRecordResponse:
    service = JanitorialOsService(db)
    try:
        contract = service.update_contract(contract_id, payload)
        response = service.get_contract_response(contract.id)
        assert response is not None
        return response
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@api_router.post("/api/contracts/import", response_model=dict)
async def import_contracts(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    service = JanitorialOsService(db)
    result = service.import_contracts_csv(await file.read())
    return result.model_dump()


@api_router.get("/api/contractors", response_model=list[ContractorResponse])
def list_contractors(
    prospect_stage: ContractorProspectStage | None = Query(None),
    follow_up_before: date | None = Query(None),
    db: Session = Depends(get_db),
) -> list[ContractorResponse]:
    service = JanitorialOsService(db)
    return [
        _contractor_response(row)
        for row in service.list_contractors(
            prospect_stage=prospect_stage.value if prospect_stage else None,
            follow_up_before=follow_up_before,
        )
    ]


@api_router.post("/api/contractors", response_model=ContractorResponse)
def create_contractor(payload: ContractorCreate, db: Session = Depends(get_db)) -> ContractorResponse:
    service = JanitorialOsService(db)
    try:
        return _contractor_response(service.create_contractor(payload))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@api_router.get("/api/contractors/{contractor_id}", response_model=ContractorResponse)
def get_contractor(contractor_id: str, db: Session = Depends(get_db)) -> ContractorResponse:
    service = JanitorialOsService(db)
    contractor = service.get_contractor(contractor_id)
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")
    return _contractor_response(contractor)


@api_router.put("/api/contractors/{contractor_id}", response_model=ContractorResponse)
def update_contractor(
    contractor_id: str, payload: ContractorUpdate, db: Session = Depends(get_db)
) -> ContractorResponse:
    service = JanitorialOsService(db)
    try:
        return _contractor_response(service.update_contractor(contractor_id, payload))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@api_router.get("/api/contractors/{contractor_id}/touchpoints", response_model=list[ContractorTouchpointResponse])
def list_contractor_touchpoints(
    contractor_id: str, db: Session = Depends(get_db)
) -> list[ContractorTouchpointResponse]:
    service = JanitorialOsService(db)
    if not service.get_contractor(contractor_id):
        raise HTTPException(status_code=404, detail="Contractor not found")
    return [_touchpoint_response(row) for row in service.list_contractor_touchpoints(contractor_id)]


@api_router.post("/api/contractors/{contractor_id}/touchpoints", response_model=ContractorTouchpointResponse)
def create_contractor_touchpoint(
    contractor_id: str, payload: ContractorTouchpointCreate, db: Session = Depends(get_db)
) -> ContractorTouchpointResponse:
    service = JanitorialOsService(db)
    try:
        return _touchpoint_response(service.add_contractor_touchpoint(contractor_id, payload))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@api_router.get("/api/scoring/profiles", response_model=list[ScoringProfileResponse])
def list_scoring_profiles(profile_type: ProfileType, db: Session = Depends(get_db)) -> list[ScoringProfileResponse]:
    service = JanitorialOsService(db)
    return [ScoringProfileResponse.model_validate(row, from_attributes=True) for row in service.list_scoring_profiles(profile_type.value)]


@api_router.put("/api/scoring/profiles/{profile_id}", response_model=ScoringProfileResponse)
def update_scoring_profile(
    profile_id: str, payload: ScoringProfileUpdateRequest, db: Session = Depends(get_db)
) -> ScoringProfileResponse:
    service = JanitorialOsService(db)
    try:
        profile = service.update_scoring_profile(profile_id, payload)
        return ScoringProfileResponse.model_validate(profile, from_attributes=True)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@api_router.post("/api/contracts/{contract_id}/pursuits", response_model=OpportunityDetailResponse)
def create_pursuit_from_contract(
    contract_id: str,
    payload: CreatePursuitFromContractRequest,
    db: Session = Depends(get_db),
) -> OpportunityDetailResponse:
    service = JanitorialOsService(db)
    try:
        opportunity = service.create_pursuit_from_contract(contract_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    detail = OpportunityIntakeService(db).get_detail(opportunity.id)
    if not detail:
        raise HTTPException(status_code=404, detail="Created opportunity was not found")
    return detail


@api_router.get("/api/opportunities/{opportunity_id}/matches", response_model=list[OpportunityMatchResponse])
def list_matches(opportunity_id: str, db: Session = Depends(get_db)) -> list[OpportunityMatchResponse]:
    service = JanitorialOsService(db)
    return [_match_response(row) for row in service.list_matches(opportunity_id)]


@api_router.post("/api/opportunities/{opportunity_id}/matches", response_model=list[OpportunityMatchResponse])
def refresh_matches(opportunity_id: str, db: Session = Depends(get_db)) -> list[OpportunityMatchResponse]:
    service = JanitorialOsService(db)
    try:
        return [_match_response(row) for row in service.refresh_matches(opportunity_id)]
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@api_router.get("/api/opportunities/{opportunity_id}/contacts", response_model=list[ContactResponse])
def list_contacts(opportunity_id: str, db: Session = Depends(get_db)) -> list[ContactResponse]:
    service = JanitorialOsService(db)
    return [_contact_response(row) for row in service.list_contacts(opportunity_id)]


@api_router.post("/api/opportunities/{opportunity_id}/contacts", response_model=ContactResponse)
def create_contact(opportunity_id: str, payload: ContactCreate, db: Session = Depends(get_db)) -> ContactResponse:
    service = JanitorialOsService(db)
    return _contact_response(service.add_contact(opportunity_id, payload))


@api_router.get("/api/opportunities/{opportunity_id}/intelligence", response_model=list[IntelligenceNoteResponse])
def list_intelligence(opportunity_id: str, db: Session = Depends(get_db)) -> list[IntelligenceNoteResponse]:
    service = JanitorialOsService(db)
    return [_note_response(row) for row in service.list_intelligence_notes(opportunity_id)]


@api_router.post("/api/opportunities/{opportunity_id}/intelligence", response_model=IntelligenceNoteResponse)
def create_intelligence(
    opportunity_id: str, payload: IntelligenceNoteCreate, db: Session = Depends(get_db)
) -> IntelligenceNoteResponse:
    service = JanitorialOsService(db)
    return _note_response(service.add_intelligence_note(opportunity_id, payload))


@api_router.get("/api/opportunities/{opportunity_id}/evidence", response_model=list[EvidenceRecordResponse])
def list_evidence(opportunity_id: str, db: Session = Depends(get_db)) -> list[EvidenceRecordResponse]:
    service = JanitorialOsService(db)
    return [_evidence_response(row) for row in service.list_evidence(opportunity_id)]


@api_router.post("/api/opportunities/{opportunity_id}/evidence", response_model=EvidenceRecordResponse)
def create_evidence(
    opportunity_id: str, payload: EvidenceRecordCreate, db: Session = Depends(get_db)
) -> EvidenceRecordResponse:
    service = JanitorialOsService(db)
    return _evidence_response(service.add_evidence(opportunity_id, payload))


@api_router.get("/api/opportunities/{opportunity_id}/capture-actions", response_model=list[CaptureActionResponse])
def list_capture_actions(opportunity_id: str, db: Session = Depends(get_db)) -> list[CaptureActionResponse]:
    service = JanitorialOsService(db)
    return [_action_response(row) for row in service.list_capture_actions(opportunity_id)]


@api_router.post("/api/opportunities/{opportunity_id}/capture-actions", response_model=CaptureActionResponse)
def create_capture_action(
    opportunity_id: str, payload: CaptureActionCreate, db: Session = Depends(get_db)
) -> CaptureActionResponse:
    service = JanitorialOsService(db)
    return _action_response(service.add_capture_action(opportunity_id, payload))


@api_router.get("/api/opportunities/{opportunity_id}/commercials", response_model=CommercialResponse | None)
def get_commercial(opportunity_id: str, db: Session = Depends(get_db)) -> CommercialResponse | None:
    service = JanitorialOsService(db)
    commercial = service.get_commercial(opportunity_id)
    return _commercial_response(db, commercial) if commercial else None


@api_router.post("/api/opportunities/{opportunity_id}/commercials", response_model=CommercialResponse)
def upsert_commercial(
    opportunity_id: str, payload: CommercialCreate, db: Session = Depends(get_db)
) -> CommercialResponse:
    service = JanitorialOsService(db)
    try:
        commercial = service.upsert_commercial(opportunity_id, payload)
        return _commercial_response(db, commercial)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@api_router.get("/api/dashboard/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummaryResponse:
    service = JanitorialOsService(db)
    return service.dashboard_summary()


@api_router.post("/api/dashboard/seed-demo")
def seed_demo(db: Session = Depends(get_db)) -> dict:
    service = JanitorialOsService(db)
    service.seed_demo_data()
    return {"status": "ok"}


@web_router.get("/dashboard", response_class=HTMLResponse)
def dashboard_view(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    service = JanitorialOsService(db)
    summary = service.dashboard_summary()
    opportunities = OpportunityIntakeService(db).list_opportunities()[:10]
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"summary": summary, "opportunities": opportunities},
    )


@web_router.post("/dashboard/seed-demo")
def seed_demo_web(db: Session = Depends(get_db)) -> RedirectResponse:
    service = JanitorialOsService(db)
    service.seed_demo_data()
    return RedirectResponse(url="/dashboard", status_code=303)


@web_router.get("/organizations", response_class=HTMLResponse)
def organizations_view(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    service = JanitorialOsService(db)
    return templates.TemplateResponse(
        request=request,
        name="organizations.html",
        context={"organizations": service.list_organizations(), "errors": [], "form_data": {}},
    )


@web_router.post("/organizations")
def organizations_create_web(
    request: Request,
    name: str = Form(...),
    organization_type: str = Form("OTHER"),
    city: str = Form(""),
    state: str = Form(""),
    website_url: str = Form(""),
    procurement_url: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
) -> Response:
    service = JanitorialOsService(db)
    raw = {
        "name": name,
        "organization_type": organization_type,
        "city": city or None,
        "state": state or None,
        "website_url": website_url or None,
        "procurement_url": procurement_url or None,
        "notes": notes or None,
    }
    try:
        payload = OrganizationCreate.model_validate(raw)
        service.create_organization(payload)
        return RedirectResponse(url="/organizations", status_code=303)
    except (ValidationError, ValueError) as exc:
        errors = _validation_errors(exc) if isinstance(exc, ValidationError) else [str(exc)]
        return templates.TemplateResponse(
            request=request,
            name="organizations.html",
            context={"organizations": service.list_organizations(), "errors": errors, "form_data": raw},
            status_code=422,
        )


@web_router.get("/organizations/{organization_id}", response_class=HTMLResponse)
def organization_detail_view(request: Request, organization_id: str, db: Session = Depends(get_db)) -> HTMLResponse:
    service = JanitorialOsService(db)
    organization = service.get_organization(organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    facilities = [row for row in service.list_facilities() if row.organization_id == organization_id]
    contracts = [row for row in service.list_contracts() if row.organization_id == organization_id]
    return templates.TemplateResponse(
        request=request,
        name="organization_detail.html",
        context={"organization": organization, "facilities": facilities, "contracts": contracts, "errors": []},
    )


@web_router.post("/organizations/{organization_id}")
def organization_update_web(
    organization_id: str,
    name: str = Form(...),
    organization_type: str = Form("OTHER"),
    city: str = Form(""),
    state: str = Form(""),
    website_url: str = Form(""),
    procurement_url: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    service = JanitorialOsService(db)
    payload = OrganizationUpdate.model_validate(
        {
            "name": name,
            "organization_type": organization_type,
            "city": city or None,
            "state": state or None,
            "website_url": website_url or None,
            "procurement_url": procurement_url or None,
            "notes": notes or None,
        }
    )
    service.update_organization(organization_id, payload)
    return RedirectResponse(url=f"/organizations/{organization_id}", status_code=303)


@web_router.get("/facilities", response_class=HTMLResponse)
def facilities_view(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    service = JanitorialOsService(db)
    return templates.TemplateResponse(
        request=request,
        name="facilities.html",
        context={
            "facilities": service.list_facilities(),
            "organizations": service.list_organizations(),
            "errors": [],
            "form_data": {},
        },
    )


@web_router.post("/facilities")
def facilities_create_web(
    request: Request,
    organization_id: str = Form(...),
    parent_facility_id: str = Form(""),
    name: str = Form(...),
    facility_kind: str = Form("FACILITY"),
    facility_type: str = Form("GENERAL"),
    city: str = Form(""),
    state: str = Form(""),
    service_complexity: str = Form("MEDIUM"),
    square_footage: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
) -> Response:
    service = JanitorialOsService(db)
    raw = {
        "organization_id": organization_id,
        "parent_facility_id": parent_facility_id or None,
        "name": name,
        "facility_kind": facility_kind,
        "facility_type": facility_type,
        "city": city or None,
        "state": state or None,
        "service_complexity": service_complexity,
        "square_footage": square_footage or None,
        "notes": notes or None,
    }
    try:
        payload = FacilityCreate.model_validate(raw)
        service.create_facility(payload)
        return RedirectResponse(url="/facilities", status_code=303)
    except (ValidationError, ValueError) as exc:
        errors = _validation_errors(exc) if isinstance(exc, ValidationError) else [str(exc)]
        return templates.TemplateResponse(
            request=request,
            name="facilities.html",
            context={
                "facilities": service.list_facilities(),
                "organizations": service.list_organizations(),
                "errors": errors,
                "form_data": raw,
            },
            status_code=422,
        )


@web_router.get("/facilities/{facility_id}", response_class=HTMLResponse)
def facility_detail_view(request: Request, facility_id: str, db: Session = Depends(get_db)) -> HTMLResponse:
    service = JanitorialOsService(db)
    facility = service.get_facility(facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return templates.TemplateResponse(
        request=request,
        name="facility_detail.html",
        context={
            "facility": facility,
            "organizations": service.list_organizations(),
            "errors": [],
        },
    )


@web_router.post("/facilities/{facility_id}")
def facility_update_web(
    facility_id: str,
    organization_id: str = Form(...),
    parent_facility_id: str = Form(""),
    name: str = Form(...),
    facility_kind: str = Form("FACILITY"),
    facility_type: str = Form("GENERAL"),
    city: str = Form(""),
    state: str = Form(""),
    service_complexity: str = Form("MEDIUM"),
    square_footage: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    service = JanitorialOsService(db)
    payload = FacilityUpdate.model_validate(
        {
            "organization_id": organization_id,
            "parent_facility_id": parent_facility_id or None,
            "name": name,
            "facility_kind": facility_kind,
            "facility_type": facility_type,
            "city": city or None,
            "state": state or None,
            "service_complexity": service_complexity,
            "square_footage": square_footage or None,
            "notes": notes or None,
        }
    )
    service.update_facility(facility_id, payload)
    return RedirectResponse(url=f"/facilities/{facility_id}", status_code=303)


@web_router.get("/contracts", response_class=HTMLResponse)
def contracts_view(
    request: Request,
    state: str | None = None,
    facility_kind: str | None = None,
    incumbent: str | None = None,
    rebid_within_days: int | None = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = JanitorialOsService(db)
    contracts = service.list_contracts(
        state=state,
        facility_kind=facility_kind,
        incumbent=incumbent,
        rebid_within_days=rebid_within_days,
    )
    return templates.TemplateResponse(
        request=request,
        name="contracts.html",
        context={
            "contracts": [service.get_contract_response(row.id) for row in contracts],
            "organizations": service.list_organizations(),
            "facilities": service.list_facilities(),
            "errors": [],
            "filters": {
                "state": state or "",
                "facility_kind": facility_kind or "",
                "incumbent": incumbent or "",
                "rebid_within_days": rebid_within_days or "",
            },
            "form_data": {},
        },
    )


@web_router.post("/contracts")
def contracts_create_web(
    request: Request,
    organization_id: str = Form(...),
    title: str = Form(...),
    incumbent_vendor: str = Form(""),
    estimated_annual_value: str = Form(""),
    estimated_total_value: str = Form(""),
    start_date: str = Form(""),
    expiration_date: str = Form(""),
    rebid_window_start: str = Form(""),
    rebid_window_end: str = Form(""),
    procurement_source_url: str = Form(""),
    source_type: str = Form("PUBLIC"),
    source_notes: str = Form(""),
    facility_ids: list[str] = Form([]),
    db: Session = Depends(get_db),
) -> Response:
    service = JanitorialOsService(db)
    try:
        payload = _parse_contract_form(
            organization_id=organization_id,
            title=title,
            incumbent_vendor=incumbent_vendor,
            estimated_annual_value=estimated_annual_value,
            estimated_total_value=estimated_total_value,
            start_date=start_date,
            expiration_date=expiration_date,
            rebid_window_start=rebid_window_start,
            rebid_window_end=rebid_window_end,
            procurement_source_url=procurement_source_url,
            source_type=source_type,
            source_notes=source_notes,
            facility_ids=facility_ids,
        )
        service.create_contract(payload)
        return RedirectResponse(url="/contracts", status_code=303)
    except (ValidationError, ValueError) as exc:
        errors = _validation_errors(exc) if isinstance(exc, ValidationError) else [str(exc)]
        return templates.TemplateResponse(
            request=request,
            name="contracts.html",
            context={
                "contracts": [service.get_contract_response(row.id) for row in service.list_contracts()],
                "organizations": service.list_organizations(),
                "facilities": service.list_facilities(),
                "errors": errors,
                "filters": {"state": "", "facility_kind": "", "incumbent": "", "rebid_within_days": ""},
                "form_data": {
                    "organization_id": organization_id,
                    "title": title,
                    "incumbent_vendor": incumbent_vendor,
                    "estimated_annual_value": estimated_annual_value,
                    "estimated_total_value": estimated_total_value,
                    "start_date": start_date,
                    "expiration_date": expiration_date,
                    "rebid_window_start": rebid_window_start,
                    "rebid_window_end": rebid_window_end,
                    "procurement_source_url": procurement_source_url,
                    "source_type": source_type,
                    "source_notes": source_notes,
                    "facility_ids": facility_ids,
                },
            },
            status_code=422,
        )


@web_router.post("/contracts/import")
async def contracts_import_web(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    service = JanitorialOsService(db)
    service.import_contracts_csv(await file.read())
    return RedirectResponse(url="/contracts", status_code=303)


@web_router.get("/contracts/{contract_id}", response_class=HTMLResponse)
def contract_detail_view(request: Request, contract_id: str, db: Session = Depends(get_db)) -> HTMLResponse:
    service = JanitorialOsService(db)
    contract = service.get_contract_response(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return templates.TemplateResponse(
        request=request,
        name="contract_detail.html",
        context={
            "contract": contract,
            "organizations": service.list_organizations(),
            "facilities": service.list_facilities(),
            "errors": [],
        },
    )


@web_router.post("/contracts/{contract_id}")
def contract_update_web(
    contract_id: str,
    organization_id: str = Form(...),
    title: str = Form(...),
    incumbent_vendor: str = Form(""),
    estimated_annual_value: str = Form(""),
    estimated_total_value: str = Form(""),
    start_date: str = Form(""),
    expiration_date: str = Form(""),
    rebid_window_start: str = Form(""),
    rebid_window_end: str = Form(""),
    procurement_source_url: str = Form(""),
    source_type: str = Form("PUBLIC"),
    source_notes: str = Form(""),
    facility_ids: list[str] = Form([]),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    service = JanitorialOsService(db)
    payload = _parse_contract_form(
        organization_id=organization_id,
        title=title,
        incumbent_vendor=incumbent_vendor,
        estimated_annual_value=estimated_annual_value,
        estimated_total_value=estimated_total_value,
        start_date=start_date,
        expiration_date=expiration_date,
        rebid_window_start=rebid_window_start,
        rebid_window_end=rebid_window_end,
        procurement_source_url=procurement_source_url,
        source_type=source_type,
        source_notes=source_notes,
        facility_ids=facility_ids,
    )
    service.update_contract(contract_id, ContractRecordUpdate.model_validate(payload.model_dump()))
    return RedirectResponse(url=f"/contracts/{contract_id}", status_code=303)


@web_router.post("/contracts/{contract_id}/pursuits")
def create_pursuit_from_contract_web(
    contract_id: str,
    title: str = Form(""),
    primary_facility_id: str = Form(""),
    pursuit_stage: str = Form("INTELLIGENCE"),
    confidence_level: str = Form("MEDIUM"),
    expected_rfp_date: str = Form(""),
    provenance_summary: str = Form(...),
    strategic_fit: str = Form("3"),
    incumbent_vulnerability: str = Form("3"),
    rebid_probability: str = Form("3"),
    relationship_access: str = Form("3"),
    contractor_fit: str = Form("3"),
    operational_complexity: str = Form("3"),
    margin_potential: str = Form("3"),
    pre_rfp_influence: str = Form("3"),
    timeline_urgency: str = Form("3"),
    actor: str = Form("operator"),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    service = JanitorialOsService(db)
    payload = CreatePursuitFromContractRequest.model_validate(
        {
            "title": title or None,
            "primary_facility_id": primary_facility_id or None,
            "pursuit_stage": pursuit_stage,
            "confidence_level": confidence_level,
            "expected_rfp_date": expected_rfp_date or None,
            "provenance_summary": provenance_summary,
            "strategic_fit": strategic_fit,
            "incumbent_vulnerability": incumbent_vulnerability,
            "rebid_probability": rebid_probability,
            "relationship_access": relationship_access,
            "contractor_fit": contractor_fit,
            "operational_complexity": operational_complexity,
            "margin_potential": margin_potential,
            "pre_rfp_influence": pre_rfp_influence,
            "timeline_urgency": timeline_urgency,
            "actor": actor,
        }
    )
    opportunity = service.create_pursuit_from_contract(contract_id, payload)
    return RedirectResponse(url=f"/opportunities/{opportunity.id}", status_code=303)


@web_router.get("/contractors", response_class=HTMLResponse)
def contractors_view(
    request: Request,
    prospect_stage: str | None = Query(None),
    follow_up_before: date | None = Query(None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = JanitorialOsService(db)
    return templates.TemplateResponse(
        request=request,
        name="contractors.html",
        context=_with_contractor_form_options(
            {
                "contractors": service.list_contractors(
                    prospect_stage=prospect_stage or None,
                    follow_up_before=follow_up_before,
                ),
                "errors": [],
                "form_data": {},
                "filters": {
                    "prospect_stage": prospect_stage or "",
                    "follow_up_before": follow_up_before.isoformat() if follow_up_before else "",
                },
            }
        ),
    )


@web_router.post("/contractors")
def contractors_create_web(
    request: Request,
    name: str = Form(...),
    service_geographies: str = Form(""),
    headquarters_city: str = Form(""),
    headquarters_state: str = Form(""),
    vertical_experience: str = Form(""),
    labor_profile: str = Form(""),
    union_profile: str = Form(""),
    diversity_certs: str = Form(""),
    airport_experience: bool = Form(False),
    healthcare_experience: bool = Form(False),
    education_experience: bool = Form(False),
    municipal_experience: bool = Form(False),
    scale_band: str = Form("REGIONAL"),
    relationship_strength: str = Form("3"),
    prospect_stage: str = Form("TARGET"),
    next_follow_up_date: str = Form(""),
    relationship_notes: str = Form(""),
    strategic_fit_notes: str = Form(""),
    db: Session = Depends(get_db),
) -> Response:
    service = JanitorialOsService(db)
    raw = {
        "name": name,
        "service_geographies": service_geographies or None,
        "headquarters_city": headquarters_city or None,
        "headquarters_state": headquarters_state or None,
        "vertical_experience": vertical_experience or None,
        "labor_profile": labor_profile or None,
        "union_profile": union_profile or None,
        "diversity_certs": diversity_certs or None,
        "airport_experience": airport_experience,
        "healthcare_experience": healthcare_experience,
        "education_experience": education_experience,
        "municipal_experience": municipal_experience,
        "scale_band": scale_band,
        "relationship_strength": relationship_strength,
        "prospect_stage": prospect_stage,
        "next_follow_up_date": next_follow_up_date or None,
        "relationship_notes": relationship_notes or None,
        "strategic_fit_notes": strategic_fit_notes or None,
    }
    try:
        payload = ContractorCreate.model_validate(raw)
        service.create_contractor(payload)
        return RedirectResponse(url="/contractors", status_code=303)
    except (ValidationError, ValueError) as exc:
        errors = _validation_errors(exc) if isinstance(exc, ValidationError) else [str(exc)]
        return templates.TemplateResponse(
            request=request,
            name="contractors.html",
            context=_with_contractor_form_options(
                {
                    "contractors": service.list_contractors(),
                    "errors": errors,
                    "form_data": raw,
                    "filters": {"prospect_stage": "", "follow_up_before": ""},
                }
            ),
            status_code=422,
        )


@web_router.get("/contractors/{contractor_id}", response_class=HTMLResponse)
def contractor_detail_view(request: Request, contractor_id: str, db: Session = Depends(get_db)) -> HTMLResponse:
    service = JanitorialOsService(db)
    contractor = service.get_contractor(contractor_id)
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")
    return templates.TemplateResponse(
        request=request,
        name="contractor_detail.html",
        context=_with_contractor_form_options(
            {
                "contractor": contractor,
                "touchpoints": service.list_contractor_touchpoints(contractor_id),
                "errors": [],
            }
        ),
    )


@web_router.post("/contractors/{contractor_id}")
def contractor_update_web(
    request: Request,
    contractor_id: str,
    name: str = Form(...),
    service_geographies: str = Form(""),
    headquarters_city: str = Form(""),
    headquarters_state: str = Form(""),
    vertical_experience: str = Form(""),
    labor_profile: str = Form(""),
    union_profile: str = Form(""),
    diversity_certs: str = Form(""),
    airport_experience: bool = Form(False),
    healthcare_experience: bool = Form(False),
    education_experience: bool = Form(False),
    municipal_experience: bool = Form(False),
    scale_band: str = Form("REGIONAL"),
    relationship_strength: str = Form("3"),
    prospect_stage: str = Form("TARGET"),
    next_follow_up_date: str = Form(""),
    relationship_notes: str = Form(""),
    strategic_fit_notes: str = Form(""),
    db: Session = Depends(get_db),
) -> Response:
    service = JanitorialOsService(db)
    raw = {
        "name": name,
        "service_geographies": service_geographies or None,
        "headquarters_city": headquarters_city or None,
        "headquarters_state": headquarters_state or None,
        "vertical_experience": vertical_experience or None,
        "labor_profile": labor_profile or None,
        "union_profile": union_profile or None,
        "diversity_certs": diversity_certs or None,
        "airport_experience": airport_experience,
        "healthcare_experience": healthcare_experience,
        "education_experience": education_experience,
        "municipal_experience": municipal_experience,
        "scale_band": scale_band,
        "relationship_strength": relationship_strength,
        "prospect_stage": prospect_stage,
        "next_follow_up_date": next_follow_up_date or None,
        "relationship_notes": relationship_notes or None,
        "strategic_fit_notes": strategic_fit_notes or None,
    }
    try:
        payload = ContractorUpdate.model_validate(raw)
        service.update_contractor(contractor_id, payload)
        return RedirectResponse(url=f"/contractors/{contractor_id}", status_code=303)
    except ValidationError as exc:
        contractor = service.get_contractor(contractor_id)
        if not contractor:
            raise HTTPException(status_code=404, detail="Contractor not found") from exc
        errors = _validation_errors(exc)
        return templates.TemplateResponse(
            request=request,
            name="contractor_detail.html",
            context=_with_contractor_form_options(
                {
                    "contractor": contractor,
                    "touchpoints": service.list_contractor_touchpoints(contractor_id),
                    "errors": errors,
                }
            ),
            status_code=422,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@web_router.post("/contractors/{contractor_id}/touchpoints")
def contractor_touchpoint_create_web(
    request: Request,
    contractor_id: str,
    contact_name: str = Form(""),
    touchpoint_type: str = Form("NOTE"),
    touchpoint_at: str = Form(...),
    summary: str = Form(...),
    next_step: str = Form(""),
    next_follow_up_date: str = Form(""),
    db: Session = Depends(get_db),
) -> Response:
    service = JanitorialOsService(db)
    try:
        payload = ContractorTouchpointCreate.model_validate(
            {
                "contact_name": contact_name or None,
                "touchpoint_type": touchpoint_type,
                "touchpoint_at": touchpoint_at,
                "summary": summary,
                "next_step": next_step or None,
                "next_follow_up_date": next_follow_up_date or None,
            }
        )
        service.add_contractor_touchpoint(contractor_id, payload)
        return RedirectResponse(url=f"/contractors/{contractor_id}", status_code=303)
    except (ValidationError, ValueError) as exc:
        contractor = service.get_contractor(contractor_id)
        if not contractor:
            raise HTTPException(status_code=404, detail="Contractor not found") from exc
        errors = _validation_errors(exc) if isinstance(exc, ValidationError) else [str(exc)]
        return templates.TemplateResponse(
            request=request,
            name="contractor_detail.html",
            context=_with_contractor_form_options(
                {
                    "contractor": contractor,
                    "touchpoints": service.list_contractor_touchpoints(contractor_id),
                    "errors": errors,
                }
            ),
            status_code=422,
        )


@web_router.get("/settings/scoring", response_class=HTMLResponse)
def scoring_settings_view(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    service = JanitorialOsService(db)
    return templates.TemplateResponse(
        request=request,
        name="scoring_settings.html",
        context={
            "opportunity_profiles": service.list_scoring_profiles(ProfileType.OPPORTUNITY.value),
            "contractor_profiles": service.list_scoring_profiles(ProfileType.CONTRACTOR_FIT.value),
        },
    )


@web_router.post("/settings/scoring/{profile_id}")
async def scoring_settings_update_web(
    request: Request,
    profile_id: str,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    service = JanitorialOsService(db)
    form = await request.form()
    criteria = []
    for key, value in form.items():
        if not key.startswith("criterion_"):
            continue
        criteria.append({"code": key.replace("criterion_", "", 1), "weight": value})
    payload = ScoringProfileUpdateRequest.model_validate({"criteria": criteria})
    service.update_scoring_profile(profile_id, payload)
    return RedirectResponse(url="/settings/scoring", status_code=303)


@web_router.get("/opportunities/{opportunity_id}/capture-workbench", response_class=HTMLResponse)
def capture_workbench_view(request: Request, opportunity_id: str, db: Session = Depends(get_db)) -> HTMLResponse:
    service = JanitorialOsService(db)
    detail = OpportunityIntakeService(db).get_detail(opportunity_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    matches = service.list_matches(opportunity_id)
    contacts = service.list_contacts(opportunity_id)
    notes = service.list_intelligence_notes(opportunity_id)
    evidence = service.list_evidence(opportunity_id)
    actions = service.list_capture_actions(opportunity_id)
    commercial = service.get_commercial(opportunity_id)
    return templates.TemplateResponse(
        request=request,
        name="capture_workbench.html",
        context={
            "detail": detail,
            "matches": [_match_response(row) for row in matches],
            "contacts": contacts,
            "notes": notes,
            "evidence": evidence,
            "actions": actions,
            "commercial": _commercial_response(db, commercial) if commercial else None,
            "contractors": service.list_contractors(),
        },
    )


@web_router.post("/opportunities/{opportunity_id}/capture-workbench/matches")
def capture_workbench_refresh_matches(opportunity_id: str, db: Session = Depends(get_db)) -> RedirectResponse:
    JanitorialOsService(db).refresh_matches(opportunity_id)
    return RedirectResponse(url=f"/opportunities/{opportunity_id}/capture-workbench", status_code=303)


@web_router.post("/opportunities/{opportunity_id}/capture-workbench/contacts")
def capture_workbench_add_contact(
    opportunity_id: str,
    organization_id: str = Form(""),
    contractor_id: str = Form(""),
    full_name: str = Form(...),
    role_title: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    contact_side: str = Form("BUYER"),
    source_type: str = Form("PUBLIC"),
    confidence_level: str = Form("MEDIUM"),
    notes: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    payload = ContactCreate.model_validate(
        {
            "organization_id": organization_id or None,
            "contractor_id": contractor_id or None,
            "full_name": full_name,
            "role_title": role_title or None,
            "email": email or None,
            "phone": phone or None,
            "contact_side": contact_side,
            "source_type": source_type,
            "confidence_level": confidence_level,
            "notes": notes or None,
        }
    )
    JanitorialOsService(db).add_contact(opportunity_id, payload)
    return RedirectResponse(url=f"/opportunities/{opportunity_id}/capture-workbench", status_code=303)


@web_router.post("/opportunities/{opportunity_id}/capture-workbench/intelligence")
def capture_workbench_add_note(
    opportunity_id: str,
    title: str = Form(...),
    note_type: str = Form("INTELLIGENCE"),
    note_text: str = Form(...),
    source_class: str = Form("PUBLIC"),
    provenance: str = Form(...),
    confidence_level: str = Form("MEDIUM"),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    payload = IntelligenceNoteCreate.model_validate(
        {
            "title": title,
            "note_type": note_type,
            "note_text": note_text,
            "source_class": source_class,
            "provenance": provenance,
            "confidence_level": confidence_level,
        }
    )
    JanitorialOsService(db).add_intelligence_note(opportunity_id, payload)
    return RedirectResponse(url=f"/opportunities/{opportunity_id}/capture-workbench", status_code=303)


@web_router.post("/opportunities/{opportunity_id}/capture-workbench/evidence")
def capture_workbench_add_evidence(
    opportunity_id: str,
    intelligence_note_id: str = Form(""),
    contract_id: str = Form(""),
    source_class: str = Form("PUBLIC"),
    provenance: str = Form(...),
    source_url: str = Form(""),
    summary: str = Form(...),
    confidence_level: str = Form("MEDIUM"),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    payload = EvidenceRecordCreate.model_validate(
        {
            "intelligence_note_id": intelligence_note_id or None,
            "contract_id": contract_id or None,
            "source_class": source_class,
            "provenance": provenance,
            "source_url": source_url or None,
            "summary": summary,
            "confidence_level": confidence_level,
        }
    )
    JanitorialOsService(db).add_evidence(opportunity_id, payload)
    return RedirectResponse(url=f"/opportunities/{opportunity_id}/capture-workbench", status_code=303)


@web_router.post("/opportunities/{opportunity_id}/capture-workbench/actions")
def capture_workbench_add_action(
    opportunity_id: str,
    title: str = Form(...),
    action_type: str = Form("RESEARCH"),
    status: str = Form("OPEN"),
    owner: str = Form("operator"),
    due_date: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    payload = CaptureActionCreate.model_validate(
        {
            "title": title,
            "action_type": action_type,
            "status": status,
            "owner": owner,
            "due_date": due_date or None,
            "notes": notes or None,
        }
    )
    JanitorialOsService(db).add_capture_action(opportunity_id, payload)
    return RedirectResponse(url=f"/opportunities/{opportunity_id}/capture-workbench", status_code=303)


@web_router.post("/opportunities/{opportunity_id}/capture-workbench/commercials")
def capture_workbench_upsert_commercial(
    opportunity_id: str,
    contractor_id: str = Form(""),
    retainer_amount: str = Form(""),
    success_fee_type: str = Form(""),
    success_fee_value: str = Form(""),
    projected_payout_date: str = Form(""),
    projected_payout_amount: str = Form(""),
    realized_revenue: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    payload = CommercialCreate.model_validate(
        {
            "contractor_id": contractor_id or None,
            "retainer_amount": retainer_amount or None,
            "success_fee_type": success_fee_type or None,
            "success_fee_value": success_fee_value or None,
            "projected_payout_date": projected_payout_date or None,
            "projected_payout_amount": projected_payout_amount or None,
            "realized_revenue": realized_revenue or None,
            "notes": notes or None,
        }
    )
    JanitorialOsService(db).upsert_commercial(opportunity_id, payload)
    return RedirectResponse(url=f"/opportunities/{opportunity_id}/capture-workbench", status_code=303)
