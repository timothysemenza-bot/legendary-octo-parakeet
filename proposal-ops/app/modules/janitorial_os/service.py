import csv
import json
from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta
from io import StringIO
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.core.workflow import OpportunityStage
from app.modules.capture_plan.service import build_bootstrap_capture_plan_content
from app.modules.janitorial_os.models import (
    CaptureAction,
    CommercialEngagement,
    Contact,
    ContractFacility,
    ContractRecord,
    Contractor,
    ContractorTouchpoint,
    EvidenceRecord,
    Facility,
    IntelligenceNote,
    OpportunityMatch,
    Organization,
    ProposalWorkflowSummary,
    ScoringCriterion,
    ScoringProfile,
    UxEvent,
    UxFeedback,
)
from app.modules.janitorial_os.schemas import (
    CaptureActionCreate,
    CaptureActionStatus,
    CaptureActionType,
    CommercialCreate,
    ConfidenceLevel,
    ContactCreate,
    ContactSide,
    ContactSourceType,
    ContractImportResult,
    ContractRecordCreate,
    ContractRecordResponse,
    ContractRecordUpdate,
    ContractorOpportunityLinkCreate,
    ContractorOpportunityLinkResponse,
    ContractorPursuitHandoffCreate,
    ContractorResponse,
    ContractorTouchpointCreate,
    ContractorTouchpointResponse,
    ContractorWorkbenchContextResponse,
    CreatePursuitFromContractRequest,
    DashboardContractSummary,
    DashboardContractorFollowUpSummary,
    DashboardSummaryResponse,
    DashboardMatchSummary,
    DashboardOpportunitySummary,
    DashboardPursuitReadinessSummary,
    EvidenceRecordCreate,
    IntelligenceNoteType,
    ProfileType,
    ScoringProfileUpdateRequest,
    SourceClass,
    UxEventCreate,
    UxEventResponse,
    UxEventType,
    UxFeedbackCreate,
    UxFeedbackResponse,
    UxFeedbackType,
    UxFrictionFinding,
    UxFrictionSummaryResponse,
    UxPageFrictionSummary,
    UxRecommendation,
)
from app.modules.opportunity_intake.models import CapturePlan, Opportunity
from app.modules.opportunity_intake.scoring import classify_recommendation, classify_tier
from app.modules.opportunity_intake.service import sync_pursuit_fields, weighted_pipeline_value


ETHICS_GUIDANCE = (
    "Use this platform only for lawful, ethical capture planning. Record public facts, clearly marked "
    "inferences, and authorized conversations only. Do not store confidential procurement information."
)


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _sanitize_ux_value(value: Any, *, depth: int = 0) -> Any:
    if depth > 2:
        return None
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned[:160]
    if isinstance(value, list):
        sanitized = [_sanitize_ux_value(item, depth=depth + 1) for item in value[:12]]
        return [item for item in sanitized if item is not None]
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in list(value.items())[:20]:
            sanitized = _sanitize_ux_value(item, depth=depth + 1)
            if sanitized is not None:
                result[str(key)[:80]] = sanitized
        return result
    return str(value)[:160]


def _dump_ux_json(payload: dict[str, Any] | None) -> str:
    sanitized = _sanitize_ux_value(payload or {}, depth=0)
    if not isinstance(sanitized, dict):
        sanitized = {}
    return json.dumps(sanitized, sort_keys=True)


def _load_ux_json(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _ux_event_response(row: UxEvent) -> UxEventResponse:
    return UxEventResponse(
        id=row.id,
        session_id=row.session_id,
        actor=row.actor,
        event_type=row.event_type,
        page_key=row.page_key,
        path=row.path,
        referrer_path=row.referrer_path,
        form_name=row.form_name,
        target_key=row.target_key,
        field_name=row.field_name,
        duration_ms=row.duration_ms,
        count_value=row.count_value,
        metadata_json=_load_ux_json(row.metadata_json),
        created_at=row.created_at,
    )


def _ux_feedback_response(row: UxFeedback) -> UxFeedbackResponse:
    return UxFeedbackResponse(
        id=row.id,
        session_id=row.session_id,
        actor=row.actor,
        feedback_type=row.feedback_type,
        page_key=row.page_key,
        path=row.path,
        form_name=row.form_name,
        note_text=row.note_text,
        context_json=_load_ux_json(row.context_json),
        voice_note_status=row.voice_note_status,
        voice_note_asset_ref=row.voice_note_asset_ref,
        created_at=row.created_at,
    )

DEFAULT_SCORING_PROFILES: dict[str, list[tuple[str, str, int]]] = {
    ProfileType.OPPORTUNITY.value: [
        ("contract_value", "Estimated Contract Value", 12),
        ("strategic_fit", "Strategic Fit", 12),
        ("incumbent_vulnerability", "Incumbent Vulnerability", 10),
        ("rebid_probability", "Probability Of Rebid", 12),
        ("relationship_access", "Relationship Access", 10),
        ("contractor_fit", "Contractor Fit", 10),
        ("operational_complexity", "Operational Complexity Fit", 8),
        ("margin_potential", "Expected Margin Potential", 10),
        ("pre_rfp_influence", "Pre-RFP Influence", 10),
        ("timeline_urgency", "Timeline Urgency", 6),
    ],
    ProfileType.CONTRACTOR_FIT.value: [
        ("geography", "Geography", 25),
        ("scale", "Scale", 20),
        ("vertical_experience", "Vertical Experience", 20),
        ("relationship_access", "Relationship Access", 15),
        ("labor_model_fit", "Labor Model Fit", 10),
        ("certification_diversity_fit", "Certification/Diversity Fit", 10),
    ],
}


def _parse_date(raw: str | None) -> date | None:
    if not raw:
        return None
    cleaned = raw.strip()
    if not cleaned:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None


def _parse_money(raw: str | None) -> float | None:
    if raw is None:
        return None
    cleaned = raw.strip().replace("$", "").replace(",", "")
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _normalize_factor(value: int) -> float:
    return round(((value - 1) / 4.0) * 100.0, 2)


def _text_tokens(value: str | None) -> set[str]:
    if not value:
        return set()
    normalized = value.replace(",", " ").replace(";", " ").replace("/", " ").lower()
    return {token.strip() for token in normalized.split() if token.strip()}


def _match_vertical_target(organization_type: str | None, facility_type: str | None) -> str | None:
    joined = f"{organization_type or ''} {facility_type or ''}".upper()
    if "AIRPORT" in joined:
        return "AIRPORT"
    if "HOSPITAL" in joined or "HEALTH" in joined:
        return "HEALTHCARE"
    if "UNIVERSITY" in joined or "SCHOOL" in joined or "EDUCATION" in joined:
        return "EDUCATION"
    if "MUNICIPAL" in joined or "CITY" in joined or "DISTRICT" in joined:
        return "MUNICIPAL"
    return None


class JanitorialOsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ensure_default_scoring_profiles(self) -> None:
        changed = False
        for profile_type, criteria in DEFAULT_SCORING_PROFILES.items():
            stmt = select(ScoringProfile).where(
                ScoringProfile.profile_type == profile_type, ScoringProfile.is_default.is_(True)
            )
            profile = self.db.scalars(stmt).first()
            if profile:
                continue
            profile = ScoringProfile(
                profile_type=profile_type,
                name=f"Default {profile_type.replace('_', ' ').title()}",
                is_default=True,
            )
            self.db.add(profile)
            self.db.flush()
            for index, (code, label, weight) in enumerate(criteria, start=1):
                self.db.add(
                    ScoringCriterion(
                        profile_id=profile.id,
                        code=code,
                        label=label,
                        weight=weight,
                        sort_order=index,
                    )
                )
            changed = True
        if changed:
            self.db.commit()

    def list_scoring_profiles(self, profile_type: str) -> list[ScoringProfile]:
        self.ensure_default_scoring_profiles()
        stmt = (
            select(ScoringProfile)
            .where(ScoringProfile.profile_type == profile_type)
            .order_by(ScoringProfile.is_default.desc(), ScoringProfile.created_at.asc())
        )
        profiles = list(self.db.scalars(stmt))
        for profile in profiles:
            profile.criteria.sort(key=lambda row: (row.sort_order, row.code))
        return profiles

    def update_scoring_profile(self, profile_id: str, payload: ScoringProfileUpdateRequest) -> ScoringProfile:
        self.ensure_default_scoring_profiles()
        profile = self.db.get(ScoringProfile, profile_id)
        if not profile:
            raise ValueError("Scoring profile not found.")
        by_code = {criterion.code: criterion for criterion in profile.criteria}
        for item in payload.criteria:
            if item.code not in by_code:
                raise ValueError(f"Unknown scoring criterion: {item.code}")
            by_code[item.code].weight = item.weight
        self.db.commit()
        self.db.refresh(profile)
        profile.criteria.sort(key=lambda row: (row.sort_order, row.code))
        return profile

    def _default_profile(self, profile_type: str) -> ScoringProfile:
        self.ensure_default_scoring_profiles()
        stmt = select(ScoringProfile).where(
            ScoringProfile.profile_type == profile_type, ScoringProfile.is_default.is_(True)
        )
        profile = self.db.scalars(stmt).first()
        if not profile:
            raise ValueError(f"Default scoring profile not found for {profile_type}.")
        profile.criteria.sort(key=lambda row: (row.sort_order, row.code))
        return profile

    def list_organizations(self) -> list[Organization]:
        stmt = select(Organization).order_by(Organization.name.asc())
        return list(self.db.scalars(stmt))

    def get_organization(self, organization_id: str) -> Organization | None:
        return self.db.get(Organization, organization_id)

    def create_organization(self, payload: Any) -> Organization:
        existing = self.db.scalars(select(Organization).where(Organization.name == payload.name)).first()
        if existing:
            raise ValueError("Organization name already exists.")
        organization = Organization(**payload.model_dump())
        self.db.add(organization)
        self.db.commit()
        self.db.refresh(organization)
        return organization

    def update_organization(self, organization_id: str, payload: Any) -> Organization:
        organization = self.db.get(Organization, organization_id)
        if not organization:
            raise ValueError("Organization not found.")
        for key, value in payload.model_dump().items():
            setattr(organization, key, value)
        self.db.commit()
        self.db.refresh(organization)
        return organization

    def list_facilities(self) -> list[Facility]:
        stmt = select(Facility).order_by(Facility.name.asc())
        return list(self.db.scalars(stmt))

    def get_facility(self, facility_id: str) -> Facility | None:
        return self.db.get(Facility, facility_id)

    def create_facility(self, payload: Any) -> Facility:
        if not self.db.get(Organization, payload.organization_id):
            raise ValueError("organization_id is not valid.")
        facility = Facility(**payload.model_dump())
        self.db.add(facility)
        self.db.commit()
        self.db.refresh(facility)
        return facility

    def update_facility(self, facility_id: str, payload: Any) -> Facility:
        facility = self.db.get(Facility, facility_id)
        if not facility:
            raise ValueError("Facility not found.")
        if not self.db.get(Organization, payload.organization_id):
            raise ValueError("organization_id is not valid.")
        for key, value in payload.model_dump().items():
            setattr(facility, key, value)
        self.db.commit()
        self.db.refresh(facility)
        return facility

    def list_contracts(
        self,
        *,
        state: str | None = None,
        facility_kind: str | None = None,
        incumbent: str | None = None,
        rebid_within_days: int | None = None,
    ) -> list[ContractRecord]:
        stmt = select(ContractRecord).order_by(
            ContractRecord.rebid_window_start.asc().nulls_last(),
            ContractRecord.expiration_date.asc().nulls_last(),
            ContractRecord.created_at.desc(),
        )
        contracts = list(self.db.scalars(stmt))
        filtered: list[ContractRecord] = []
        today = date.today()
        state_upper = state.strip().upper() if state else None
        incumbent_filter = incumbent.strip().lower() if incumbent else None
        facility_kind_filter = facility_kind.strip().upper() if facility_kind else None
        for contract in contracts:
            organization = self.db.get(Organization, contract.organization_id)
            link_rows = self.db.scalars(
                select(ContractFacility).where(ContractFacility.contract_id == contract.id)
            ).all()
            facilities = [self.db.get(Facility, link.facility_id) for link in link_rows]
            states = {f.state.upper() for f in facilities if f and f.state}
            if organization and organization.state:
                states.add(organization.state.upper())
            if state_upper and state_upper not in states:
                continue
            if facility_kind_filter:
                kinds = {f.facility_kind for f in facilities if f}
                if facility_kind_filter not in kinds:
                    continue
            if incumbent_filter and incumbent_filter not in (contract.incumbent_vendor or "").lower():
                continue
            if rebid_within_days is not None:
                target_date = contract.rebid_window_start or contract.expiration_date
                if not target_date:
                    continue
                delta_days = (target_date - today).days
                if delta_days < 0 or delta_days > rebid_within_days:
                    continue
            filtered.append(contract)
        return filtered

    def _sync_contract_facilities(self, contract_id: str, facility_ids: list[str]) -> None:
        self.db.execute(delete(ContractFacility).where(ContractFacility.contract_id == contract_id))
        seen: set[str] = set()
        for facility_id in facility_ids:
            if not facility_id or facility_id in seen:
                continue
            facility = self.db.get(Facility, facility_id)
            if not facility:
                raise ValueError(f"Unknown facility_id: {facility_id}")
            seen.add(facility_id)
            self.db.add(ContractFacility(contract_id=contract_id, facility_id=facility_id))

    def create_contract(self, payload: ContractRecordCreate) -> ContractRecord:
        if not self.db.get(Organization, payload.organization_id):
            raise ValueError("organization_id is not valid.")
        values = payload.model_dump()
        facility_ids = values.pop("facility_ids")
        contract = ContractRecord(**values)
        self.db.add(contract)
        self.db.flush()
        self._sync_contract_facilities(contract.id, facility_ids)
        self.db.commit()
        self.db.refresh(contract)
        return contract

    def update_contract(self, contract_id: str, payload: ContractRecordUpdate) -> ContractRecord:
        contract = self.db.get(ContractRecord, contract_id)
        if not contract:
            raise ValueError("Contract not found.")
        if not self.db.get(Organization, payload.organization_id):
            raise ValueError("organization_id is not valid.")
        values = payload.model_dump()
        facility_ids = values.pop("facility_ids")
        for key, value in values.items():
            setattr(contract, key, value)
        self._sync_contract_facilities(contract_id, facility_ids)
        self.db.commit()
        self.db.refresh(contract)
        return contract

    def get_contract_response(self, contract_id: str) -> ContractRecordResponse | None:
        contract = self.db.get(ContractRecord, contract_id)
        if not contract:
            return None
        organization = self.db.get(Organization, contract.organization_id)
        links = list(self.db.scalars(select(ContractFacility).where(ContractFacility.contract_id == contract.id)))
        facilities = [self.db.get(Facility, row.facility_id) for row in links]
        return ContractRecordResponse(
            id=contract.id,
            organization_id=contract.organization_id,
            organization_name=organization.name if organization else None,
            title=contract.title,
            incumbent_vendor=contract.incumbent_vendor,
            estimated_annual_value=contract.estimated_annual_value,
            estimated_total_value=contract.estimated_total_value,
            start_date=contract.start_date,
            expiration_date=contract.expiration_date,
            rebid_window_start=contract.rebid_window_start,
            rebid_window_end=contract.rebid_window_end,
            procurement_source_url=contract.procurement_source_url,
            source_type=contract.source_type,
            source_notes=contract.source_notes,
            facility_ids=[row.facility_id for row in links],
            facility_names=[facility.name for facility in facilities if facility],
            created_at=contract.created_at,
            updated_at=contract.updated_at,
        )

    def import_contracts_csv(self, raw_csv: bytes) -> ContractImportResult:
        decoded = raw_csv.decode("utf-8-sig")
        reader = csv.DictReader(StringIO(decoded))
        warnings: list[str] = []
        contract_ids: list[str] = []
        created_facility_ids: set[str] = set()
        created_org_ids: set[str] = set()
        for row_index, row in enumerate(reader, start=2):
            org_name = (row.get("organization_name") or "").strip()
            contract_title = (row.get("contract_title") or "").strip()
            if not org_name or not contract_title:
                warnings.append(f"Row {row_index}: organization_name and contract_title are required.")
                continue
            organization = self.db.scalars(select(Organization).where(Organization.name == org_name)).first()
            if not organization:
                organization = Organization(
                    name=org_name,
                    organization_type=(row.get("organization_type") or "OTHER").strip().upper() or "OTHER",
                    city=(row.get("organization_city") or "").strip() or None,
                    state=(row.get("state") or "").strip() or None,
                )
                self.db.add(organization)
                self.db.flush()
                created_org_ids.add(organization.id)
            facility_name = (row.get("facility_name") or "").strip()
            facility = None
            if facility_name:
                stmt = select(Facility).where(
                    Facility.organization_id == organization.id,
                    Facility.name == facility_name,
                )
                facility = self.db.scalars(stmt).first()
                if not facility:
                    facility = Facility(
                        organization_id=organization.id,
                        name=facility_name,
                        facility_kind=(row.get("facility_kind") or "FACILITY").strip().upper() or "FACILITY",
                        facility_type=(row.get("facility_type") or "GENERAL").strip().upper() or "GENERAL",
                        city=(row.get("city") or "").strip() or None,
                        state=(row.get("state") or "").strip() or None,
                        service_complexity=(row.get("service_complexity") or "MEDIUM").strip().upper() or "MEDIUM",
                        square_footage=_parse_money(row.get("square_footage")),
                    )
                    self.db.add(facility)
                    self.db.flush()
                    created_facility_ids.add(facility.id)
            contract = ContractRecord(
                organization_id=organization.id,
                title=contract_title,
                incumbent_vendor=(row.get("incumbent_vendor") or "").strip() or None,
                estimated_annual_value=_parse_money(row.get("annual_value")),
                estimated_total_value=_parse_money(row.get("total_value")),
                start_date=_parse_date(row.get("start_date")),
                expiration_date=_parse_date(row.get("expiration_date")),
                rebid_window_start=_parse_date(row.get("rebid_window_start")),
                rebid_window_end=_parse_date(row.get("rebid_window_end")),
                procurement_source_url=(row.get("procurement_source_url") or "").strip() or None,
                source_type=(row.get("source_type") or "PUBLIC").strip().upper() or "PUBLIC",
                source_notes=(row.get("source_notes") or "").strip() or None,
            )
            self.db.add(contract)
            self.db.flush()
            if facility:
                self.db.add(ContractFacility(contract_id=contract.id, facility_id=facility.id))
            contract_ids.append(contract.id)
        self.db.commit()
        return ContractImportResult(
            imported_count=len(contract_ids),
            organization_count=len(created_org_ids),
            facility_count=len(created_facility_ids),
            warnings=warnings,
            contract_ids=contract_ids,
        )

    def list_contractors(
        self,
        *,
        prospect_stage: str | None = None,
        follow_up_before: date | None = None,
    ) -> list[Contractor]:
        stmt = select(Contractor)
        if prospect_stage:
            stmt = stmt.where(Contractor.prospect_stage == prospect_stage)
        if follow_up_before:
            stmt = stmt.where(
                Contractor.next_follow_up_date.is_not(None),
                Contractor.next_follow_up_date <= follow_up_before,
            )
        stmt = stmt.order_by(Contractor.name.asc())
        return list(self.db.scalars(stmt))

    def get_contractor(self, contractor_id: str) -> Contractor | None:
        return self.db.get(Contractor, contractor_id)

    def list_linkable_opportunities(self) -> list[Opportunity]:
        stmt = (
            select(Opportunity)
            .where(Opportunity.pursuit_stage.not_in(["AWARD", "LOST", "DORMANT"]))
            .order_by(Opportunity.expected_rfp_date.asc().nulls_last(), Opportunity.updated_at.desc())
        )
        return list(self.db.scalars(stmt))

    def create_contractor(self, payload: Any) -> Contractor:
        existing = self.db.scalars(select(Contractor).where(Contractor.name == payload.name)).first()
        if existing:
            raise ValueError("Contractor name already exists.")
        contractor = Contractor(**payload.model_dump())
        self.db.add(contractor)
        self.db.commit()
        self.db.refresh(contractor)
        return contractor

    def update_contractor(self, contractor_id: str, payload: Any) -> Contractor:
        contractor = self.db.get(Contractor, contractor_id)
        if not contractor:
            raise ValueError("Contractor not found.")
        for key, value in payload.model_dump().items():
            setattr(contractor, key, value)
        self.db.commit()
        self.db.refresh(contractor)
        return contractor

    def list_contractor_touchpoints(self, contractor_id: str) -> list[ContractorTouchpoint]:
        stmt = (
            select(ContractorTouchpoint)
            .where(ContractorTouchpoint.contractor_id == contractor_id)
            .order_by(ContractorTouchpoint.touchpoint_at.desc(), ContractorTouchpoint.created_at.desc())
        )
        return list(self.db.scalars(stmt))

    def list_recent_contractor_touchpoints(
        self, contractor_id: str, *, limit: int = 5
    ) -> list[ContractorTouchpoint]:
        stmt = (
            select(ContractorTouchpoint)
            .where(ContractorTouchpoint.contractor_id == contractor_id)
            .order_by(ContractorTouchpoint.touchpoint_at.desc(), ContractorTouchpoint.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt))

    def add_contractor_touchpoint(
        self, contractor_id: str, payload: ContractorTouchpointCreate
    ) -> ContractorTouchpoint:
        contractor = self.db.get(Contractor, contractor_id)
        if not contractor:
            raise ValueError("Contractor not found.")
        touchpoint = ContractorTouchpoint(contractor_id=contractor_id, **payload.model_dump())
        self.db.add(touchpoint)
        if contractor.last_touch_at is None or payload.touchpoint_at >= contractor.last_touch_at:
            contractor.last_touch_at = payload.touchpoint_at
        if payload.next_follow_up_date:
            contractor.next_follow_up_date = payload.next_follow_up_date
        self.db.commit()
        self.db.refresh(touchpoint)
        self.db.refresh(contractor)
        return touchpoint

    def _contractor_opportunity_link_summary(
        self, contractor: Contractor, commercial: CommercialEngagement
    ) -> ContractorOpportunityLinkResponse | None:
        opportunity = self.db.get(Opportunity, commercial.opportunity_id)
        if not opportunity:
            return None
        organization = self.db.get(Organization, opportunity.buying_organization_id) if opportunity.buying_organization_id else None
        contract = self.db.get(ContractRecord, opportunity.primary_contract_id) if opportunity.primary_contract_id else None
        return ContractorOpportunityLinkResponse(
            commercial_id=commercial.id,
            opportunity_id=opportunity.id,
            opportunity_name=opportunity.name,
            organization_name=organization.name if organization else opportunity.client,
            pursuit_stage=opportunity.pursuit_stage,
            proposal_stage=opportunity.proposal_stage,
            confidence_level=opportunity.confidence_level,
            expected_rfp_date=opportunity.expected_rfp_date,
            primary_contract_title=contract.title if contract else None,
            weighted_pipeline_value=opportunity.weighted_pipeline_value,
            weighted_expected_value=commercial.weighted_expected_value,
            contractor_id=contractor.id,
            contractor_name=contractor.name,
        )

    def list_contractor_opportunity_links(
        self, contractor_id: str
    ) -> list[ContractorOpportunityLinkResponse]:
        contractor = self.db.get(Contractor, contractor_id)
        if not contractor:
            raise ValueError("Contractor not found.")
        commercials = list(
            self.db.scalars(
                select(CommercialEngagement)
                .where(CommercialEngagement.contractor_id == contractor_id)
                .order_by(CommercialEngagement.updated_at.desc())
            )
        )
        links: list[ContractorOpportunityLinkResponse] = []
        for commercial in commercials:
            summary = self._contractor_opportunity_link_summary(contractor, commercial)
            if summary:
                links.append(summary)
        return links

    def get_capture_workbench_contractor_context(
        self, opportunity_id: str
    ) -> ContractorWorkbenchContextResponse | None:
        commercial = self.get_commercial(opportunity_id)
        if not commercial or not commercial.contractor_id:
            return None
        contractor = self.db.get(Contractor, commercial.contractor_id)
        if not contractor:
            return None
        recent_touchpoints = [
            ContractorTouchpointResponse.model_validate(row, from_attributes=True)
            for row in self.list_recent_contractor_touchpoints(contractor.id, limit=5)
        ]
        linked_opportunities = [
            item
            for item in self.list_contractor_opportunity_links(contractor.id)
            if item.opportunity_id != opportunity_id
        ]
        return ContractorWorkbenchContextResponse(
            contractor=ContractorResponse.model_validate(contractor, from_attributes=True),
            recent_touchpoints=recent_touchpoints,
            linked_opportunities=linked_opportunities,
        )

    def create_pursuit_from_contractor_handoff(
        self, contractor_id: str, payload: ContractorPursuitHandoffCreate
    ) -> Opportunity:
        contractor = self.db.get(Contractor, contractor_id)
        if not contractor:
            raise ValueError("Contractor not found.")
        opportunity = self.create_pursuit_from_contract(
            payload.contract_id,
            CreatePursuitFromContractRequest.model_validate(payload.model_dump(exclude={"contract_id"})),
        )
        commercial = self.link_contractor_to_opportunity(
            contractor_id,
            ContractorOpportunityLinkCreate(opportunity_id=opportunity.id, actor=payload.actor),
        )
        log_audit_event(
            self.db,
            opportunity_id=opportunity.id,
            actor=payload.actor,
            action="contractor_handoff_seeded",
            after_state_json=json.dumps(
                {
                    "contractor_id": contractor.id,
                    "commercial_id": commercial.id,
                }
            ),
        )
        self.db.commit()
        self.db.refresh(opportunity)
        return opportunity

    def link_contractor_to_opportunity(
        self, contractor_id: str, payload: ContractorOpportunityLinkCreate
    ) -> CommercialEngagement:
        contractor = self.db.get(Contractor, contractor_id)
        if not contractor:
            raise ValueError("Contractor not found.")
        opportunity = self.db.get(Opportunity, payload.opportunity_id)
        if not opportunity:
            raise ValueError("Opportunity not found.")
        commercial = self.upsert_commercial(
            payload.opportunity_id,
            CommercialCreate(contractor_id=contractor_id),
        )
        log_audit_event(
            self.db,
            opportunity_id=opportunity.id,
            actor=payload.actor,
            action="contractor_linked_to_opportunity",
            after_state_json=json.dumps(
                {
                    "contractor_id": contractor.id,
                    "commercial_id": commercial.id,
                }
            ),
        )
        self.db.commit()
        self.db.refresh(commercial)
        return commercial

    def log_ux_event(self, payload: UxEventCreate, *, actor: str | None = None) -> UxEventResponse:
        row = UxEvent(
            session_id=payload.session_id,
            actor=actor,
            page_key=payload.page_key,
            path=payload.path,
            referrer_path=payload.referrer_path,
            event_type=payload.event_type.value,
            form_name=payload.form_name,
            target_key=payload.target_key,
            field_name=payload.field_name,
            duration_ms=payload.duration_ms,
            count_value=payload.count_value,
            metadata_json=_dump_ux_json(payload.metadata_json),
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return _ux_event_response(row)

    def submit_ux_feedback(self, payload: UxFeedbackCreate, *, actor: str | None = None) -> UxFeedbackResponse:
        row = UxFeedback(
            session_id=payload.session_id,
            actor=actor,
            page_key=payload.page_key,
            path=payload.path,
            form_name=payload.form_name,
            feedback_type=payload.feedback_type.value,
            note_text=payload.note_text,
            context_json=_dump_ux_json(payload.context_json),
            voice_note_status=payload.voice_note_status.value,
            voice_note_asset_ref=payload.voice_note_asset_ref,
        )
        self.db.add(row)
        self.db.flush()
        event_type = (
            UxEventType.MANUAL_OVERRIDE.value
            if payload.feedback_type == UxFeedbackType.MANUAL_WORKAROUND
            else UxEventType.FEEDBACK_SUBMITTED.value
        )
        self.db.add(
            UxEvent(
                session_id=payload.session_id,
                actor=actor,
                page_key=payload.page_key,
                path=payload.path,
                referrer_path=None,
                event_type=event_type,
                form_name=payload.form_name,
                target_key=None,
                field_name=None,
                duration_ms=None,
                count_value=1,
                metadata_json=_dump_ux_json({"feedback_type": payload.feedback_type.value, **payload.context_json}),
            )
        )
        self.db.commit()
        self.db.refresh(row)
        return _ux_feedback_response(row)

    def summarize_ux_friction(self, *, lookback_days: int = 14) -> UxFrictionSummaryResponse:
        lookback_days = min(max(lookback_days, 1), 90)
        since = _utcnow() - timedelta(days=lookback_days)
        events = list(
            self.db.scalars(
                select(UxEvent).where(UxEvent.created_at >= since).order_by(UxEvent.created_at.asc())
            )
        )
        feedback = list(
            self.db.scalars(
                select(UxFeedback).where(UxFeedback.created_at >= since).order_by(UxFeedback.created_at.desc())
            )
        )

        page_stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "page_key": "",
                "path": "",
                "visits": 0,
                "duration_total": 0,
                "duration_samples": 0,
                "revisit_count": 0,
                "navigation_loop_count": 0,
                "validation_failures": 0,
                "abandoned_forms": 0,
                "repeated_clicks": 0,
                "high_churn_fields": 0,
                "manual_overrides": 0,
                "explicit_feedback_count": 0,
                "max_field_churn": 0,
                "feedback_types": Counter(),
                "validation_forms": Counter(),
            }
        )
        page_views_by_session: dict[str, list[UxEvent]] = defaultdict(list)
        page_visit_counts: dict[tuple[str, str], int] = defaultdict(int)
        tracked_sessions = {
            row.session_id for row in events if row.session_id
        } | {row.session_id for row in feedback if row.session_id}

        for row in events:
            stats = page_stats[row.page_key]
            stats["page_key"] = row.page_key
            stats["path"] = row.path
            event_count = row.count_value or 1
            if row.event_type == UxEventType.PAGE_VIEW.value:
                stats["visits"] += 1
                page_views_by_session[row.session_id].append(row)
                page_visit_counts[(row.session_id, row.page_key)] += 1
            elif row.event_type == UxEventType.PAGE_EXIT.value and row.duration_ms is not None:
                stats["duration_total"] += row.duration_ms
                stats["duration_samples"] += 1
            elif row.event_type == UxEventType.VALIDATION_FAILURE.value:
                stats["validation_failures"] += event_count
                if row.form_name:
                    stats["validation_forms"][row.form_name] += event_count
            elif row.event_type == UxEventType.FORM_ABANDON.value:
                stats["abandoned_forms"] += event_count
            elif row.event_type == UxEventType.REPEATED_CLICK.value:
                stats["repeated_clicks"] += event_count
            elif row.event_type == UxEventType.FIELD_CHURN.value:
                stats["high_churn_fields"] += 1
                stats["max_field_churn"] = max(stats["max_field_churn"], event_count)
            elif row.event_type == UxEventType.MANUAL_OVERRIDE.value:
                stats["manual_overrides"] += event_count

        for (session_id, page_key), visits in page_visit_counts.items():
            if visits > 1:
                page_stats[page_key]["revisit_count"] += visits - 1

        for session_events in page_views_by_session.values():
            keys = [row.page_key for row in session_events]
            for index in range(2, len(keys)):
                if keys[index] == keys[index - 2] and keys[index] != keys[index - 1]:
                    page_stats[keys[index]]["navigation_loop_count"] += 1

        for row in feedback:
            stats = page_stats[row.page_key]
            stats["page_key"] = row.page_key
            stats["path"] = row.path
            stats["explicit_feedback_count"] += 1
            stats["feedback_types"][row.feedback_type] += 1
            if row.feedback_type == UxFeedbackType.MANUAL_WORKAROUND.value:
                stats["manual_overrides"] += 1

        top_pages: list[UxPageFrictionSummary] = []
        findings: list[UxFrictionFinding] = []
        recommendations: list[UxRecommendation] = []
        recommendation_keys: set[tuple[str, str]] = set()

        def add_recommendation(
            *,
            code: str,
            page_key: str,
            path: str,
            title: str,
            rationale: str,
            proposed_action: str,
        ) -> None:
            dedupe_key = (code, page_key)
            if dedupe_key in recommendation_keys:
                return
            recommendation_keys.add(dedupe_key)
            recommendations.append(
                UxRecommendation(
                    code=code,
                    page_key=page_key,
                    path=path,
                    title=title,
                    rationale=rationale,
                    proposed_action=proposed_action,
                )
            )

        for stats in page_stats.values():
            avg_time = None
            if stats["duration_samples"]:
                avg_time = round(stats["duration_total"] / stats["duration_samples"])
            top_pages.append(
                UxPageFrictionSummary(
                    page_key=stats["page_key"],
                    path=stats["path"],
                    visits=stats["visits"],
                    avg_time_on_page_ms=avg_time,
                    revisit_count=stats["revisit_count"],
                    navigation_loop_count=stats["navigation_loop_count"],
                    validation_failures=stats["validation_failures"],
                    abandoned_forms=stats["abandoned_forms"],
                    repeated_clicks=stats["repeated_clicks"],
                    high_churn_fields=stats["high_churn_fields"],
                    manual_overrides=stats["manual_overrides"],
                    explicit_feedback_count=stats["explicit_feedback_count"],
                )
            )
            page_key = stats["page_key"]
            path = stats["path"]

            if stats["validation_failures"] >= 3:
                findings.append(
                    UxFrictionFinding(
                        code="repeated_validation_failures",
                        severity="HIGH",
                        page_key=page_key,
                        path=path,
                        metric_name="validation_failures",
                        metric_value=stats["validation_failures"],
                        threshold=3,
                        summary=f"{page_key} generated repeated validation failures across the same workflow window.",
                    )
                )
                top_form = stats["validation_forms"].most_common(1)[0][0] if stats["validation_forms"] else "this form"
                add_recommendation(
                    code="improve_form_guidance",
                    page_key=page_key,
                    path=path,
                    title="Tighten form guidance and defaults",
                    rationale=f"{stats['validation_failures']} validation failures were recorded on {top_form}.",
                    proposed_action="Add inline examples, clearer required-field hints, or safer default values before changing workflow logic.",
                )

            if stats["abandoned_forms"] >= 2:
                findings.append(
                    UxFrictionFinding(
                        code="abandoned_form_flow",
                        severity="MEDIUM",
                        page_key=page_key,
                        path=path,
                        metric_name="abandoned_forms",
                        metric_value=stats["abandoned_forms"],
                        threshold=2,
                        summary=f"{page_key} shows repeated form abandonment after operators started editing.",
                    )
                )
                add_recommendation(
                    code="simplify_form_flow",
                    page_key=page_key,
                    path=path,
                    title="Simplify or stage the form flow",
                    rationale=f"{stats['abandoned_forms']} abandoned forms suggest the page is asking for too much before commitment.",
                    proposed_action="Break the form into smaller steps or reduce non-essential fields on the first pass.",
                )

            if stats["max_field_churn"] >= 5:
                findings.append(
                    UxFrictionFinding(
                        code="field_edit_churn",
                        severity="MEDIUM",
                        page_key=page_key,
                        path=path,
                        metric_name="max_field_churn",
                        metric_value=stats["max_field_churn"],
                        threshold=5,
                        summary=f"{page_key} includes a field that operators repeatedly revise before leaving the page.",
                    )
                )
                add_recommendation(
                    code="normalize_high_churn_fields",
                    page_key=page_key,
                    path=path,
                    title="Standardize the highest-churn fields",
                    rationale=f"The highest observed edit churn reached {stats['max_field_churn']} edits on one field.",
                    proposed_action="Convert ambiguous free-text inputs to controlled options or add helper copy before collecting the value.",
                )

            if stats["repeated_clicks"] >= 3:
                findings.append(
                    UxFrictionFinding(
                        code="repeated_click_clusters",
                        severity="MEDIUM",
                        page_key=page_key,
                        path=path,
                        metric_name="repeated_clicks",
                        metric_value=stats["repeated_clicks"],
                        threshold=3,
                        summary=f"{page_key} triggered repeated clicks, which usually means the operator is unsure whether the UI responded.",
                    )
                )
                add_recommendation(
                    code="clarify_interaction_feedback",
                    page_key=page_key,
                    path=path,
                    title="Clarify interaction feedback",
                    rationale=f"{stats['repeated_clicks']} repeated click signals suggest the UI is not confirming state changes clearly.",
                    proposed_action="Add a more explicit success/loading state or make the primary action outcome more visible.",
                )

            if stats["navigation_loop_count"] >= 2 or stats["revisit_count"] >= 4:
                metric_name = "navigation_loop_count" if stats["navigation_loop_count"] >= 2 else "revisit_count"
                metric_value = stats["navigation_loop_count"] if stats["navigation_loop_count"] >= 2 else stats["revisit_count"]
                threshold = 2 if stats["navigation_loop_count"] >= 2 else 4
                findings.append(
                    UxFrictionFinding(
                        code="navigation_revisit_pattern",
                        severity="MEDIUM",
                        page_key=page_key,
                        path=path,
                        metric_name=metric_name,
                        metric_value=metric_value,
                        threshold=threshold,
                        summary=f"{page_key} is being revisited in a loop-like pattern, which suggests missing shortcuts or context.",
                    )
                )
                add_recommendation(
                    code="add_cross_links_or_summary",
                    page_key=page_key,
                    path=path,
                    title="Reduce navigation loops",
                    rationale=f"Operators revisited this page {stats['revisit_count']} times and hit {stats['navigation_loop_count']} loop patterns.",
                    proposed_action="Add direct links, inline summaries, or cross-screen context so operators do not have to bounce between pages.",
                )

            if avg_time and avg_time >= 180_000 and stats["visits"] >= 3:
                findings.append(
                    UxFrictionFinding(
                        code="long_dwell_time",
                        severity="LOW",
                        page_key=page_key,
                        path=path,
                        metric_name="avg_time_on_page_ms",
                        metric_value=avg_time,
                        threshold=180_000,
                        summary=f"{page_key} has a long average dwell time, which may indicate heavy cognitive load or reference use.",
                    )
                )
                add_recommendation(
                    code="add_decision_support",
                    page_key=page_key,
                    path=path,
                    title="Add decision support on this page",
                    rationale=f"The average time on page is {round(avg_time / 1000)} seconds across multiple visits.",
                    proposed_action="Add concise helper text, defaults, or summaries so operators can finish the task without pausing to reconstruct context.",
                )

            if stats["feedback_types"][UxFeedbackType.CONFUSING.value] >= 1:
                findings.append(
                    UxFrictionFinding(
                        code="explicit_confusing_feedback",
                        severity="HIGH",
                        page_key=page_key,
                        path=path,
                        metric_name="confusing_feedback",
                        metric_value=stats["feedback_types"][UxFeedbackType.CONFUSING.value],
                        threshold=1,
                        summary=f"Operators explicitly marked {page_key} as confusing.",
                    )
                )
                add_recommendation(
                    code="clarify_confusing_workflow",
                    page_key=page_key,
                    path=path,
                    title="Clarify this workflow before expanding it",
                    rationale="At least one operator explicitly marked this step as confusing.",
                    proposed_action="Review labels, sequence, and help text with the operator before adding more adjacent features.",
                )

            if stats["feedback_types"][UxFeedbackType.TOOK_TOO_LONG.value] >= 1:
                findings.append(
                    UxFrictionFinding(
                        code="explicit_time_feedback",
                        severity="MEDIUM",
                        page_key=page_key,
                        path=path,
                        metric_name="too_long_feedback",
                        metric_value=stats["feedback_types"][UxFeedbackType.TOOK_TOO_LONG.value],
                        threshold=1,
                        summary=f"Operators explicitly said {page_key} took too long.",
                    )
                )
                add_recommendation(
                    code="reduce_time_to_complete",
                    page_key=page_key,
                    path=path,
                    title="Reduce time-to-complete",
                    rationale="An operator explicitly reported that this workflow took too long.",
                    proposed_action="Trim non-essential inputs or prefill known context before asking the operator to finish the step.",
                )

            if stats["feedback_types"][UxFeedbackType.MANUAL_WORKAROUND.value] >= 1 or stats["manual_overrides"] >= 1:
                findings.append(
                    UxFrictionFinding(
                        code="manual_workaround_detected",
                        severity="HIGH",
                        page_key=page_key,
                        path=path,
                        metric_name="manual_overrides",
                        metric_value=stats["manual_overrides"],
                        threshold=1,
                        summary=f"Operators reported doing part of {page_key} manually outside the intended workflow.",
                    )
                )
                add_recommendation(
                    code="formalize_manual_workaround",
                    page_key=page_key,
                    path=path,
                    title="Decide whether to formalize the manual workaround",
                    rationale="Manual-workaround feedback is the strongest signal that the workflow is missing a necessary path.",
                    proposed_action="Review the exact manual step with approval before adding it to the productized workflow.",
                )

        top_pages.sort(
            key=lambda item: (
                item.validation_failures
                + item.abandoned_forms
                + item.manual_overrides
                + item.explicit_feedback_count
                + item.navigation_loop_count,
                item.visits,
            ),
            reverse=True,
        )
        severity_rank = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        findings.sort(key=lambda item: (severity_rank.get(item.severity, 0), item.metric_value), reverse=True)
        recent_feedback = [_ux_feedback_response(row) for row in feedback[:8]]

        return UxFrictionSummaryResponse(
            generated_at=_utcnow(),
            lookback_days=lookback_days,
            total_events=len(events),
            total_feedback=len(feedback),
            tracked_sessions=len(tracked_sessions),
            top_pages=top_pages[:8],
            findings=findings[:12],
            recommendations=recommendations[:12],
            recent_feedback=recent_feedback,
        )

    def _dashboard_follow_up_summary(self, contractor: Contractor) -> DashboardContractorFollowUpSummary:
        latest_touchpoint = self.db.scalars(
            select(ContractorTouchpoint)
            .where(ContractorTouchpoint.contractor_id == contractor.id)
            .order_by(ContractorTouchpoint.touchpoint_at.desc(), ContractorTouchpoint.created_at.desc())
        ).first()
        return DashboardContractorFollowUpSummary(
            contractor_id=contractor.id,
            contractor_name=contractor.name,
            prospect_stage=contractor.prospect_stage,
            next_follow_up_date=contractor.next_follow_up_date,
            last_touch_at=contractor.last_touch_at,
            last_touchpoint_summary=latest_touchpoint.summary if latest_touchpoint else None,
            next_step=latest_touchpoint.next_step if latest_touchpoint else None,
        )

    def _contract_value_factor(self, contract: ContractRecord) -> float:
        value = contract.estimated_annual_value or contract.estimated_total_value or 0.0
        if value >= 5_000_000:
            return 100.0
        if value >= 1_000_000:
            return 80.0
        if value >= 250_000:
            return 60.0
        return 40.0

    def _timeline_urgency_factor(self, contract: ContractRecord, expected_rfp_date: date | None) -> float:
        target_date = expected_rfp_date or contract.rebid_window_start or contract.expiration_date
        if not target_date:
            return 60.0
        delta = (target_date - date.today()).days
        if delta <= 30:
            return 100.0
        if delta <= 90:
            return 80.0
        if delta <= 180:
            return 60.0
        return 40.0

    def create_pursuit_from_contract(
        self,
        contract_id: str,
        payload: CreatePursuitFromContractRequest,
    ) -> Opportunity:
        contract = self.db.get(ContractRecord, contract_id)
        if not contract:
            raise ValueError("Contract not found.")
        organization = self.db.get(Organization, contract.organization_id)
        if not organization:
            raise ValueError("Organization not found for contract.")
        profile = self._default_profile(ProfileType.OPPORTUNITY.value)
        criteria_by_code = {criterion.code: criterion.weight for criterion in profile.criteria}

        factor_scores = {
            "contract_value": self._contract_value_factor(contract),
            "strategic_fit": _normalize_factor(payload.strategic_fit),
            "incumbent_vulnerability": _normalize_factor(payload.incumbent_vulnerability),
            "rebid_probability": _normalize_factor(payload.rebid_probability),
            "relationship_access": _normalize_factor(payload.relationship_access),
            "contractor_fit": _normalize_factor(payload.contractor_fit),
            "operational_complexity": _normalize_factor(payload.operational_complexity),
            "margin_potential": _normalize_factor(payload.margin_potential),
            "pre_rfp_influence": _normalize_factor(payload.pre_rfp_influence),
            "timeline_urgency": self._timeline_urgency_factor(contract, payload.expected_rfp_date),
        }
        total_weight = sum(criteria_by_code.values()) or 1
        weighted_total = 0.0
        breakdown: dict[str, float] = {}
        for code, raw_score in factor_scores.items():
            weight = criteria_by_code.get(code, 0)
            component = round(raw_score * weight / total_weight, 2)
            breakdown[code] = component
            weighted_total += component
        qualification_score = round(weighted_total, 2)
        estimated_value = contract.estimated_annual_value or contract.estimated_total_value or 100000.0
        target_date = payload.expected_rfp_date or contract.rebid_window_start or contract.expiration_date or date.today()
        lead_time_days = max(1, (target_date - date.today()).days)
        tier = classify_tier(qualification_score, estimated_value)
        recommendation = classify_recommendation(qualification_score)
        opportunity = Opportunity(
            name=payload.title or contract.title,
            client=organization.name,
            estimated_contract_value=estimated_value,
            lead_time_days=lead_time_days,
            incumbent_status=bool(contract.incumbent_vendor),
            strategic_alignment=payload.strategic_fit,
            estimated_probability_win=max(0, min(100, round(qualification_score))),
            qualification_score=qualification_score,
            tier=tier.value,
            pursuit_recommendation=recommendation.value,
            stage=OpportunityStage.INTAKE.value,
            pursuit_stage=payload.pursuit_stage.value,
            proposal_stage=OpportunityStage.INTAKE.value,
            buying_organization_id=organization.id,
            primary_contract_id=contract.id,
            primary_facility_id=payload.primary_facility_id,
            confidence_level=payload.confidence_level.value,
            expected_rfp_date=payload.expected_rfp_date,
            provenance_summary=payload.provenance_summary,
            provenance_last_verified_at=_utcnow(),
            score_breakdown_json=json.dumps(breakdown),
            weighted_pipeline_value=weighted_pipeline_value(estimated_value, qualification_score),
        )
        sync_pursuit_fields(opportunity, payload.pursuit_stage.value)
        self.db.add(opportunity)
        self.db.flush()

        capture_content = build_bootstrap_capture_plan_content(opportunity)
        self.db.add(
            CapturePlan(
                opportunity_id=opportunity.id,
                version=1,
                summary=capture_content["summary"],
                client_priorities=capture_content["client_priorities"],
                competitive_landscape=capture_content["competitive_landscape"],
                win_themes_draft=capture_content["win_themes_draft"],
                solution_positioning=capture_content["solution_positioning"],
                timeline=capture_content["timeline"],
            )
        )
        self.db.add(
            ProposalWorkflowSummary(
                opportunity_id=opportunity.id,
                pricing_status="NOT_STARTED",
                compliance_status="NOT_STARTED",
                review_gate_status="NOT_STARTED",
                submission_milestone="Awaiting active RFP",
            )
        )
        log_audit_event(
            self.db,
            opportunity_id=opportunity.id,
            actor=payload.actor,
            action="pursuit_created_from_contract",
            after_state_json=json.dumps(
                {
                    "contract_id": contract.id,
                    "organization_id": organization.id,
                    "pursuit_stage": opportunity.pursuit_stage,
                    "score_breakdown": breakdown,
                }
            ),
        )
        self.db.commit()
        self.db.refresh(opportunity)
        return opportunity

    def _target_state_for_opportunity(self, opportunity: Opportunity) -> str | None:
        if opportunity.primary_facility_id:
            facility = self.db.get(Facility, opportunity.primary_facility_id)
            if facility and facility.state:
                return facility.state.upper()
        if opportunity.buying_organization_id:
            organization = self.db.get(Organization, opportunity.buying_organization_id)
            if organization and organization.state:
                return organization.state.upper()
        return None

    def _target_vertical(self, opportunity: Opportunity) -> str | None:
        facility_type = None
        if opportunity.primary_facility_id:
            facility = self.db.get(Facility, opportunity.primary_facility_id)
            facility_type = facility.facility_type if facility else None
        organization_type = None
        if opportunity.buying_organization_id:
            organization = self.db.get(Organization, opportunity.buying_organization_id)
            organization_type = organization.organization_type if organization else None
        return _match_vertical_target(organization_type, facility_type)

    def _scale_score(self, contractor: Contractor, annual_value: float) -> float:
        desired_band = "LOCAL"
        if annual_value >= 2_000_000:
            desired_band = "NATIONAL"
        elif annual_value >= 500_000:
            desired_band = "REGIONAL"
        if contractor.scale_band.upper() == desired_band:
            return 100.0
        if {contractor.scale_band.upper(), desired_band} <= {"REGIONAL", "NATIONAL"}:
            return 70.0
        if {contractor.scale_band.upper(), desired_band} <= {"LOCAL", "REGIONAL"}:
            return 70.0
        return 45.0

    def refresh_matches(self, opportunity_id: str) -> list[OpportunityMatch]:
        opportunity = self.db.get(Opportunity, opportunity_id)
        if not opportunity:
            raise ValueError("Opportunity not found.")
        profile = self._default_profile(ProfileType.CONTRACTOR_FIT.value)
        criteria_by_code = {criterion.code: criterion.weight for criterion in profile.criteria}
        contractors = self.list_contractors()
        target_state = self._target_state_for_opportunity(opportunity)
        target_vertical = self._target_vertical(opportunity)
        annual_value = opportunity.estimated_contract_value
        total_weight = sum(criteria_by_code.values()) or 1
        existing_matches = {
            match.contractor_id: match
            for match in self.db.scalars(
                select(OpportunityMatch).where(OpportunityMatch.opportunity_id == opportunity_id)
            ).all()
        }
        created_or_updated: list[OpportunityMatch] = []
        top_score: float | None = None
        for contractor in contractors:
            geography_tokens = _text_tokens(contractor.service_geographies)
            geography_score = 60.0
            if target_state:
                if target_state.lower() in geography_tokens or contractor.headquarters_state == target_state:
                    geography_score = 100.0
                elif geography_tokens:
                    geography_score = 35.0
            vertical_score = 60.0
            if target_vertical == "AIRPORT":
                vertical_score = 100.0 if contractor.airport_experience else 40.0
            elif target_vertical == "HEALTHCARE":
                vertical_score = 100.0 if contractor.healthcare_experience else 40.0
            elif target_vertical == "EDUCATION":
                vertical_score = 100.0 if contractor.education_experience else 40.0
            elif target_vertical == "MUNICIPAL":
                vertical_score = 100.0 if contractor.municipal_experience else 40.0
            elif contractor.vertical_experience:
                vertical_score = 75.0
            factors = {
                "geography": (geography_score, "Aligned to the pursuit geography." if geography_score >= 80 else "Limited visible geography overlap."),
                "scale": (self._scale_score(contractor, annual_value), "Scale band fits the estimated contract size."),
                "vertical_experience": (vertical_score, "Vertical experience aligns to buyer environment." if vertical_score >= 80 else "Vertical depth is limited or generalized."),
                "relationship_access": (_normalize_factor(contractor.relationship_strength), "Relationship access based on current operator-entered strength."),
                "labor_model_fit": (70.0 if contractor.labor_profile else 55.0, "Labor model signal is present." if contractor.labor_profile else "Labor model fit is neutral until clarified."),
                "certification_diversity_fit": (90.0 if contractor.diversity_certs else 55.0, "Certification/diversity profile is documented." if contractor.diversity_certs else "Certification fit is neutral until documented."),
            }
            breakdown: list[dict[str, Any]] = []
            total = 0.0
            for code, (score, reason) in factors.items():
                weight = criteria_by_code.get(code, 0)
                weighted_score = round(score * weight / total_weight, 2)
                total += weighted_score
                breakdown.append({"code": code, "score": weighted_score, "reason": reason})
            match_score = round(total, 2)
            record = existing_matches.get(contractor.id)
            if not record:
                record = OpportunityMatch(
                    opportunity_id=opportunity_id,
                    contractor_id=contractor.id,
                    match_score=match_score,
                    explanation_json=json.dumps(breakdown),
                )
                self.db.add(record)
            else:
                record.match_score = match_score
                record.explanation_json = json.dumps(breakdown)
            created_or_updated.append(record)
            if top_score is None or match_score > top_score:
                top_score = match_score
        opportunity.bidder_fit_score = top_score
        self.db.commit()
        created_or_updated.sort(key=lambda row: row.match_score, reverse=True)
        return created_or_updated

    def list_matches(self, opportunity_id: str) -> list[OpportunityMatch]:
        stmt = (
            select(OpportunityMatch)
            .where(OpportunityMatch.opportunity_id == opportunity_id)
            .order_by(OpportunityMatch.match_score.desc(), OpportunityMatch.updated_at.desc())
        )
        return list(self.db.scalars(stmt))

    def list_contacts(
        self,
        opportunity_id: str,
        *,
        contact_side: ContactSide | None = None,
        source_type: ContactSourceType | None = None,
        confidence_level: ConfidenceLevel | None = None,
    ) -> list[Contact]:
        stmt = select(Contact).where(Contact.opportunity_id == opportunity_id)
        if contact_side:
            stmt = stmt.where(Contact.contact_side == contact_side.value)
        if source_type:
            stmt = stmt.where(Contact.source_type == source_type.value)
        if confidence_level:
            stmt = stmt.where(Contact.confidence_level == confidence_level.value)
        stmt = stmt.order_by(Contact.created_at.desc())
        return list(self.db.scalars(stmt))

    def add_contact(self, opportunity_id: str, payload: ContactCreate) -> Contact:
        values = payload.model_dump()
        values["confidence_level"] = payload.confidence_level.value
        contact = Contact(opportunity_id=opportunity_id, **values)
        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)
        return contact

    def list_intelligence_notes(
        self,
        opportunity_id: str,
        *,
        note_type: IntelligenceNoteType | None = None,
        source_class: SourceClass | None = None,
        confidence_level: ConfidenceLevel | None = None,
    ) -> list[IntelligenceNote]:
        stmt = select(IntelligenceNote).where(IntelligenceNote.opportunity_id == opportunity_id)
        if note_type:
            stmt = stmt.where(IntelligenceNote.note_type == note_type.value)
        if source_class:
            stmt = stmt.where(IntelligenceNote.source_class == source_class.value)
        if confidence_level:
            stmt = stmt.where(IntelligenceNote.confidence_level == confidence_level.value)
        stmt = stmt.order_by(IntelligenceNote.recorded_at.desc())
        return list(self.db.scalars(stmt))

    def add_intelligence_note(self, opportunity_id: str, payload: Any) -> IntelligenceNote:
        note = IntelligenceNote(
            opportunity_id=opportunity_id,
            title=payload.title,
            note_type=payload.note_type,
            note_text=payload.note_text,
            source_class=payload.source_class.value,
            provenance=payload.provenance,
            confidence_level=payload.confidence_level.value,
            ethics_guidance_text=ETHICS_GUIDANCE,
        )
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return note

    def list_evidence(
        self,
        opportunity_id: str,
        *,
        source_class: SourceClass | None = None,
        confidence_level: ConfidenceLevel | None = None,
    ) -> list[EvidenceRecord]:
        stmt = select(EvidenceRecord).where(EvidenceRecord.opportunity_id == opportunity_id)
        if source_class:
            stmt = stmt.where(EvidenceRecord.source_class == source_class.value)
        if confidence_level:
            stmt = stmt.where(EvidenceRecord.confidence_level == confidence_level.value)
        stmt = stmt.order_by(EvidenceRecord.captured_at.desc())
        return list(self.db.scalars(stmt))

    def add_evidence(self, opportunity_id: str, payload: EvidenceRecordCreate) -> EvidenceRecord:
        evidence = EvidenceRecord(
            opportunity_id=opportunity_id,
            intelligence_note_id=payload.intelligence_note_id,
            contract_id=payload.contract_id,
            source_class=payload.source_class.value,
            provenance=payload.provenance,
            source_url=payload.source_url,
            summary=payload.summary,
            confidence_level=payload.confidence_level.value,
            ethics_guidance_text=ETHICS_GUIDANCE,
        )
        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)
        return evidence

    def list_capture_actions(
        self,
        opportunity_id: str,
        *,
        action_type: CaptureActionType | None = None,
        status: CaptureActionStatus | None = None,
    ) -> list[CaptureAction]:
        stmt = select(CaptureAction).where(CaptureAction.opportunity_id == opportunity_id)
        if action_type:
            stmt = stmt.where(CaptureAction.action_type == action_type.value)
        if status:
            stmt = stmt.where(CaptureAction.status == status.value)
        stmt = stmt.order_by(CaptureAction.due_date.asc().nulls_last(), CaptureAction.created_at.desc())
        return list(self.db.scalars(stmt))

    def add_capture_action(self, opportunity_id: str, payload: CaptureActionCreate) -> CaptureAction:
        action = CaptureAction(opportunity_id=opportunity_id, **payload.model_dump())
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        return action

    def get_commercial(self, opportunity_id: str) -> CommercialEngagement | None:
        stmt = select(CommercialEngagement).where(CommercialEngagement.opportunity_id == opportunity_id)
        return self.db.scalars(stmt).first()

    def upsert_commercial(self, opportunity_id: str, payload: CommercialCreate) -> CommercialEngagement:
        opportunity = self.db.get(Opportunity, opportunity_id)
        if not opportunity:
            raise ValueError("Opportunity not found.")
        commercial = self.get_commercial(opportunity_id)
        if not commercial:
            commercial = CommercialEngagement(opportunity_id=opportunity_id)
            self.db.add(commercial)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(commercial, key, value)
        if commercial.projected_payout_amount is None:
            if commercial.success_fee_type == "FIXED":
                commercial.projected_payout_amount = commercial.success_fee_value
            elif commercial.success_fee_type in {"PERCENT_ANNUAL", "PERCENT_TOTAL"}:
                commercial.projected_payout_amount = (commercial.success_fee_value or 0.0) * opportunity.estimated_contract_value / 100.0
        probability = opportunity.qualification_score / 100.0
        retainer = commercial.retainer_amount or 0.0
        projected = commercial.projected_payout_amount or 0.0
        commercial.weighted_expected_value = round(retainer + projected * probability, 2)
        self.db.commit()
        self.db.refresh(commercial)
        return commercial

    def dashboard_summary(self) -> DashboardSummaryResponse:
        today = date.today()
        upcoming_cutoff = today + timedelta(days=14)
        friction_summary = self.summarize_ux_friction()
        upcoming_contracts = self.list_contracts(rebid_within_days=180)[:8]
        opportunities = list(self.db.scalars(select(Opportunity).order_by(Opportunity.qualification_score.desc())))
        matches = list(
            self.db.scalars(
                select(OpportunityMatch).order_by(OpportunityMatch.match_score.desc(), OpportunityMatch.updated_at.desc())
            )
        )
        commercials = list(self.db.scalars(select(CommercialEngagement)))
        contractors_with_follow_up = list(
            self.db.scalars(
                select(Contractor)
                .where(Contractor.next_follow_up_date.is_not(None))
                .order_by(Contractor.next_follow_up_date.asc(), Contractor.name.asc())
            )
        )
        organizations_total = self.db.scalar(select(func.count()).select_from(Organization)) or 0
        facilities_total = self.db.scalar(select(func.count()).select_from(Facility)) or 0
        contracts_total = self.db.scalar(select(func.count()).select_from(ContractRecord)) or 0
        contractors_total = self.db.scalar(select(func.count()).select_from(Contractor)) or 0
        pursuits_total = self.db.scalar(select(func.count()).select_from(Opportunity)) or 0
        active_counts = Counter(opportunity.pursuit_stage for opportunity in opportunities)
        stage_metrics = Counter(opportunity.proposal_stage for opportunity in opportunities)
        total_pipeline = round(sum(opportunity.weighted_pipeline_value or 0.0 for opportunity in opportunities), 2)
        expected_revenue = round(sum(item.weighted_expected_value or 0.0 for item in commercials), 2)

        upcoming_rebids = []
        for contract in upcoming_contracts:
            organization = self.db.get(Organization, contract.organization_id)
            facilities = [
                self.db.get(Facility, row.facility_id)
                for row in self.db.scalars(select(ContractFacility).where(ContractFacility.contract_id == contract.id)).all()
            ]
            state = next((facility.state for facility in facilities if facility and facility.state), None)
            if not state and organization:
                state = organization.state
            upcoming_rebids.append(
                DashboardContractSummary(
                    contract_id=contract.id,
                    title=contract.title,
                    organization_name=organization.name if organization else "Unknown",
                    expiration_date=contract.expiration_date,
                    rebid_window_start=contract.rebid_window_start,
                    estimated_annual_value=contract.estimated_annual_value,
                    state=state,
                )
            )

        hottest_opportunities = []
        for opportunity in opportunities[:8]:
            organization = self.db.get(Organization, opportunity.buying_organization_id) if opportunity.buying_organization_id else None
            hottest_opportunities.append(
                DashboardOpportunitySummary(
                    opportunity_id=opportunity.id,
                    name=opportunity.name,
                    organization_name=organization.name if organization else opportunity.client,
                    pursuit_stage=opportunity.pursuit_stage,
                    qualification_score=opportunity.qualification_score,
                    estimated_contract_value=opportunity.estimated_contract_value,
                    weighted_pipeline_value=opportunity.weighted_pipeline_value,
                )
            )

        top_matches = []
        for match in matches[:8]:
            opportunity = self.db.get(Opportunity, match.opportunity_id)
            contractor = self.db.get(Contractor, match.contractor_id)
            if not opportunity or not contractor:
                continue
            top_matches.append(
                DashboardMatchSummary(
                    opportunity_id=opportunity.id,
                    opportunity_name=opportunity.name,
                    contractor_name=contractor.name,
                    match_score=match.match_score,
                )
            )

        overdue_follow_ups = [
            self._dashboard_follow_up_summary(contractor)
            for contractor in contractors_with_follow_up
            if contractor.next_follow_up_date and contractor.next_follow_up_date < today
        ][:8]
        upcoming_follow_ups = [
            self._dashboard_follow_up_summary(contractor)
            for contractor in contractors_with_follow_up
            if contractor.next_follow_up_date and today <= contractor.next_follow_up_date <= upcoming_cutoff
        ][:8]
        active_pursuit_readiness = self._dashboard_pursuit_readiness(opportunities)

        return DashboardSummaryResponse(
            generated_at=_utcnow(),
            organizations_total=organizations_total,
            facilities_total=facilities_total,
            contracts_total=contracts_total,
            contractors_total=contractors_total,
            pursuits_total=pursuits_total,
            upcoming_rebids=upcoming_rebids,
            hottest_opportunities=hottest_opportunities,
            top_matches=top_matches,
            overdue_contractor_follow_ups=overdue_follow_ups,
            upcoming_contractor_follow_ups=upcoming_follow_ups,
            live_pursuit_readiness=active_pursuit_readiness,
            active_pursuit_counts=dict(active_counts),
            total_weighted_pipeline_value=total_pipeline,
            expected_consulting_revenue=expected_revenue,
            stage_conversion_metrics=dict(stage_metrics),
            friction_summary=friction_summary,
        )

    def _dashboard_pursuit_readiness(
        self,
        opportunities: list[Opportunity],
    ) -> list[DashboardPursuitReadinessSummary]:
        active_opportunities = [
            opportunity
            for opportunity in opportunities
            if opportunity.pursuit_stage not in {"AWARD", "LOST", "DORMANT"}
        ][:8]
        if not active_opportunities:
            return []

        active_ids = [opportunity.id for opportunity in active_opportunities]
        contacts_by_opportunity: dict[str, list[Contact]] = defaultdict(list)
        notes_by_opportunity: Counter[str] = Counter()
        evidence_by_opportunity: Counter[str] = Counter()
        actions_by_opportunity: dict[str, list[CaptureAction]] = defaultdict(list)
        commercials_by_opportunity = {
            item.opportunity_id: item
            for item in self.db.scalars(
                select(CommercialEngagement).where(CommercialEngagement.opportunity_id.in_(active_ids))
            )
        }
        organizations = {
            item.id: item
            for item in self.db.scalars(
                select(Organization).where(
                    Organization.id.in_([opportunity.buying_organization_id for opportunity in active_opportunities if opportunity.buying_organization_id])
                )
            )
        }
        contractors = {
            item.id: item
            for item in self.db.scalars(select(Contractor).where(Contractor.id.in_([commercial.contractor_id for commercial in commercials_by_opportunity.values() if commercial.contractor_id])))
        }

        for contact in self.db.scalars(select(Contact).where(Contact.opportunity_id.in_(active_ids))):
            contacts_by_opportunity[contact.opportunity_id].append(contact)
        for note in self.db.scalars(select(IntelligenceNote).where(IntelligenceNote.opportunity_id.in_(active_ids))):
            notes_by_opportunity[note.opportunity_id] += 1
        for evidence in self.db.scalars(select(EvidenceRecord).where(EvidenceRecord.opportunity_id.in_(active_ids))):
            evidence_by_opportunity[evidence.opportunity_id] += 1
        for action in self.db.scalars(select(CaptureAction).where(CaptureAction.opportunity_id.in_(active_ids))):
            actions_by_opportunity[action.opportunity_id].append(action)

        summaries: list[DashboardPursuitReadinessSummary] = []
        readiness_total = 6
        for opportunity in active_opportunities:
            contacts = contacts_by_opportunity[opportunity.id]
            buyer_contacts_count = sum(1 for item in contacts if item.contact_side == "BUYER")
            contractor_contacts_count = sum(1 for item in contacts if item.contact_side == "CONTRACTOR")
            direct_conversation_contacts_count = sum(
                1 for item in contacts if item.source_type == "DIRECT_CONVERSATION"
            )
            intelligence_notes_count = notes_by_opportunity[opportunity.id]
            evidence_records_count = evidence_by_opportunity[opportunity.id]
            open_capture_actions_count = sum(
                1 for item in actions_by_opportunity[opportunity.id] if item.status != "COMPLETE"
            )
            commercial = commercials_by_opportunity.get(opportunity.id)
            contractor = contractors.get(commercial.contractor_id) if commercial and commercial.contractor_id else None
            advised_contractor_name = contractor.name if contractor else None

            missing_items: list[str] = []
            if buyer_contacts_count == 0:
                missing_items.append("Buyer contact")
            if contractor_contacts_count == 0:
                missing_items.append("Contractor contact")
            if intelligence_notes_count == 0:
                missing_items.append("Intelligence note")
            if evidence_records_count == 0:
                missing_items.append("Evidence")
            if open_capture_actions_count == 0:
                missing_items.append("Next action")
            if not advised_contractor_name:
                missing_items.append("Advised contractor")

            summaries.append(
                DashboardPursuitReadinessSummary(
                    opportunity_id=opportunity.id,
                    opportunity_name=opportunity.name,
                    organization_name=organizations.get(opportunity.buying_organization_id).name
                    if opportunity.buying_organization_id and opportunity.buying_organization_id in organizations
                    else opportunity.client,
                    pursuit_stage=opportunity.pursuit_stage,
                    advised_contractor_name=advised_contractor_name,
                    buyer_contacts_count=buyer_contacts_count,
                    contractor_contacts_count=contractor_contacts_count,
                    direct_conversation_contacts_count=direct_conversation_contacts_count,
                    intelligence_notes_count=intelligence_notes_count,
                    evidence_records_count=evidence_records_count,
                    open_capture_actions_count=open_capture_actions_count,
                    pilot_ready=not missing_items,
                    readiness_score=readiness_total - len(missing_items),
                    readiness_total=readiness_total,
                    missing_items=missing_items,
                )
            )
        return summaries

    def seed_demo_data(self) -> None:
        if self.db.scalar(select(func.count()).select_from(Organization)):
            return
        airport = Organization(
            name="South Jersey Regional Airport",
            organization_type="AIRPORT",
            city="Egg Harbor Township",
            state="NJ",
            procurement_url="https://example.org/procurement",
            notes="Synthetic demo account for janitorial radar testing.",
        )
        hospital = Organization(
            name="Mercer Health Network",
            organization_type="HOSPITAL",
            city="Trenton",
            state="NJ",
            notes="Synthetic demo account for janitorial healthcare pursuits.",
        )
        self.db.add_all([airport, hospital])
        self.db.flush()
        terminal = Facility(
            organization_id=airport.id,
            name="Terminal and Landside Portfolio",
            facility_kind="PORTFOLIO",
            facility_type="AIRPORT_TERMINAL",
            city="Egg Harbor Township",
            state="NJ",
            service_complexity="HIGH",
            square_footage=780000,
        )
        medical = Facility(
            organization_id=hospital.id,
            name="Central Hospital Campus",
            facility_kind="FACILITY",
            facility_type="HOSPITAL",
            city="Trenton",
            state="NJ",
            service_complexity="HIGH",
            square_footage=540000,
        )
        self.db.add_all([terminal, medical])
        self.db.flush()
        airport_contract = ContractRecord(
            organization_id=airport.id,
            title="Terminal Janitorial and Day Porter Services",
            incumbent_vendor="Incumbent Facility Group",
            estimated_annual_value=3_200_000,
            estimated_total_value=16_000_000,
            expiration_date=date(date.today().year, 11, 30),
            rebid_window_start=date(date.today().year, 8, 1),
            rebid_window_end=date(date.today().year, 10, 1),
            procurement_source_url="https://example.org/airport-radar",
            source_type="PUBLIC",
            source_notes="Derived from public contract board minutes.",
        )
        hospital_contract = ContractRecord(
            organization_id=hospital.id,
            title="Healthcare EVS and Support Services",
            incumbent_vendor="Sterling Support Services",
            estimated_annual_value=1_450_000,
            estimated_total_value=7_250_000,
            expiration_date=date(date.today().year, 9, 15),
            rebid_window_start=date(date.today().year, 6, 1),
            rebid_window_end=date(date.today().year, 8, 1),
            procurement_source_url="https://example.org/hospital-radar",
            source_type="PUBLIC",
            source_notes="Derived from public procurement archive.",
        )
        self.db.add_all([airport_contract, hospital_contract])
        self.db.flush()
        self.db.add_all(
            [
                ContractFacility(contract_id=airport_contract.id, facility_id=terminal.id),
                ContractFacility(contract_id=hospital_contract.id, facility_id=medical.id),
            ]
        )
        self.db.add_all(
            [
                Contractor(
                    name="Garden State Facility Services",
                    service_geographies="NJ PA DE",
                    headquarters_city="Cherry Hill",
                    headquarters_state="NJ",
                    vertical_experience="airport municipal education",
                    labor_profile="W2 self-perform",
                    union_profile="mixed",
                    diversity_certs="MWBE",
                    airport_experience=True,
                    municipal_experience=True,
                    scale_band="REGIONAL",
                    relationship_strength=4,
                    prospect_stage="OUTREACH",
                    next_follow_up_date=date.today(),
                    relationship_notes="Known local airport operations relationship.",
                ),
                Contractor(
                    name="Northeast Health Environmental Services",
                    service_geographies="NJ NY PA",
                    headquarters_city="Princeton",
                    headquarters_state="NJ",
                    vertical_experience="healthcare acute care education",
                    labor_profile="W2 self-perform",
                    union_profile="non-union",
                    healthcare_experience=True,
                    education_experience=True,
                    scale_band="REGIONAL",
                    relationship_strength=3,
                    prospect_stage="DISCOVERY",
                    next_follow_up_date=date.today(),
                ),
            ]
        )
        self.db.commit()
