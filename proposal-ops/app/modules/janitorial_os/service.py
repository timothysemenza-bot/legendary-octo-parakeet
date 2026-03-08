import csv
import json
from collections import Counter
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
)
from app.modules.janitorial_os.schemas import (
    CaptureActionCreate,
    CommercialCreate,
    ContactCreate,
    ContractImportResult,
    ContractRecordCreate,
    ContractRecordResponse,
    ContractRecordUpdate,
    ContractorTouchpointCreate,
    CreatePursuitFromContractRequest,
    DashboardContractSummary,
    DashboardContractorFollowUpSummary,
    DashboardMatchSummary,
    DashboardOpportunitySummary,
    DashboardSummaryResponse,
    EvidenceRecordCreate,
    ProfileType,
    ScoringProfileUpdateRequest,
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

    def list_contacts(self, opportunity_id: str) -> list[Contact]:
        stmt = select(Contact).where(Contact.opportunity_id == opportunity_id).order_by(Contact.created_at.desc())
        return list(self.db.scalars(stmt))

    def add_contact(self, opportunity_id: str, payload: ContactCreate) -> Contact:
        values = payload.model_dump()
        values["confidence_level"] = payload.confidence_level.value
        contact = Contact(opportunity_id=opportunity_id, **values)
        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)
        return contact

    def list_intelligence_notes(self, opportunity_id: str) -> list[IntelligenceNote]:
        stmt = select(IntelligenceNote).where(IntelligenceNote.opportunity_id == opportunity_id).order_by(
            IntelligenceNote.recorded_at.desc()
        )
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

    def list_evidence(self, opportunity_id: str) -> list[EvidenceRecord]:
        stmt = select(EvidenceRecord).where(EvidenceRecord.opportunity_id == opportunity_id).order_by(
            EvidenceRecord.captured_at.desc()
        )
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

    def list_capture_actions(self, opportunity_id: str) -> list[CaptureAction]:
        stmt = select(CaptureAction).where(CaptureAction.opportunity_id == opportunity_id).order_by(
            CaptureAction.due_date.asc().nulls_last(), CaptureAction.created_at.desc()
        )
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
        for key, value in payload.model_dump().items():
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
            active_pursuit_counts=dict(active_counts),
            total_weighted_pipeline_value=total_pipeline,
            expected_consulting_revenue=expected_revenue,
            stage_conversion_metrics=dict(stage_metrics),
        )

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
