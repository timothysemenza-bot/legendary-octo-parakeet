from __future__ import annotations

import argparse
import csv
import sys
from datetime import date, datetime, time
from pathlib import Path


PROPOSAL_OPS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROPOSAL_OPS_ROOT.parent
if str(PROPOSAL_OPS_ROOT) not in sys.path:
    sys.path.insert(0, str(PROPOSAL_OPS_ROOT))

from sqlalchemy import select  # noqa: E402

from app.core.db import SessionLocal  # noqa: E402
from app.modules.janitorial_os.models import (  # noqa: E402
    CommercialEngagement,
    Contact,
    Contractor,
    ContractorTouchpoint,
    GrowthMarketEvidence,
    GrowthRelationshipProfile,
)
from app.modules.opportunity_intake.models import Opportunity  # noqa: E402
from app.modules.opportunity_intake.schemas import OpportunityIntakeRequest, PursuitStage  # noqa: E402
from app.modules.opportunity_intake.service import (  # noqa: E402
    OpportunityIntakeService,
    sync_pursuit_fields,
    weighted_pipeline_value,
)


RELATIONSHIP_FIELDS = [
    "relationship_id",
    "created_date",
    "company_name",
    "contact_name",
    "role",
    "linkedin_profile_url",
    "linkedin_company_url",
    "relationship_stage",
    "warm_signal",
    "fit_confirmed",
    "pain_point",
    "desired_outcome",
    "offer_hypothesis",
    "urgency_level",
    "scope_breadth",
    "stakeholder_complexity",
    "research_load",
    "delivery_intensity",
    "last_touch_date",
    "last_interaction_summary",
    "next_best_touch_type",
    "next_best_touch_path",
    "meeting_needed",
    "meeting_status",
    "proposal_status",
    "ptw_status",
    "ptw_stage",
    "ptw_recommendation",
    "ptw_record_id",
    "owner_decision",
    "review_status",
    "ready_state",
    "notes",
]

MEMORY_FIELDS = [
    "memory_id",
    "relationship_id",
    "event_date",
    "channel",
    "event_type",
    "signal_strength",
    "message_summary",
    "pain_point",
    "desired_outcome",
    "offer_hypothesis",
    "notes",
]

KNOWLEDGE_FIELDS = [
    "knowledge_id",
    "relationship_id",
    "company_name",
    "entity_type",
    "entity_name",
    "source_type",
    "source_reference",
    "source_date",
    "source_reliability",
    "confidence",
    "customer_objective",
    "customer_need",
    "customer_value_drivers",
    "buyer_priorities",
    "evaluation_priorities",
    "buying_behavior",
    "delivery_context",
    "timing_context",
    "budget_signal",
    "budget_band",
    "competitor_name",
    "incumbent_status",
    "alternative_option",
    "big4_technical",
    "big4_management",
    "big4_past_performance",
    "big4_cost_price",
    "differentiation_hypothesis",
    "evidence_summary",
    "assumptions",
    "ethical_use_check",
    "last_validated_date",
    "notes",
]

PROPOSAL_FIELDS = [
    "proposal_id",
    "relationship_id",
    "ptw_id",
    "created_date",
    "company_name",
    "contact_name",
    "offer_name",
    "recommended_entry_offer",
    "expansion_offer",
    "ptw_stage",
    "price_to_compete_usd",
    "recommended_price_usd",
    "price_to_win_usd",
    "minimum_acceptable_price_usd",
    "maximum_price_usd",
    "ptw_confidence",
    "pursue_recommendation",
    "pricing_basis",
    "pricing_anchor",
    "pricing_rationale",
    "ptw_brief_path",
    "owner_confirmation_required",
    "discovery_summary",
    "scope_summary",
    "assumptions",
    "exclusions",
    "recommended_agenda",
    "pricing_status",
    "proposal_path",
    "owner_decision",
    "review_status",
    "status",
    "notes",
]

DEFAULT_OFFER_VALUES = {
    "opportunity foresight sprint": 5500.0,
    "procurement intelligence retainer": 6000.0,
    "capture strategy engagement": 9500.0,
    "proposal execution support": 12500.0,
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _text(value: object | None) -> str:
    return "" if value is None else str(value).strip()


def _lower(value: object | None) -> str:
    return _text(value).lower()


def _parse_date(value: str | None) -> date | None:
    text = _text(value)
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _parse_datetime(value: str | None) -> datetime | None:
    text = _text(value)
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    parsed_date = _parse_date(text)
    if parsed_date is None:
        return None
    return datetime.combine(parsed_date, time(hour=12))


def _date_string(value: date | None) -> str:
    return "" if value is None else value.isoformat()


def _datetime_string(value: datetime | None) -> str:
    return "" if value is None else value.strftime("%Y-%m-%d %H:%M")


def _int_string(value: object | None) -> str:
    if value in (None, ""):
        return ""
    try:
        return str(int(float(str(value))))
    except (TypeError, ValueError):
        return ""


def _float(value: object | None) -> float:
    text = _text(value).replace("$", "").replace(",", "")
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def _confidence_level_from_row(row: dict[str, str]) -> str:
    if _lower(row.get("fit_confirmed")) == "yes" and _lower(row.get("warm_signal")) in {"reply", "meeting", "warm"}:
        return "HIGH"
    if _lower(row.get("fit_confirmed")) == "yes":
        return "MEDIUM"
    return "LOW"


def _contractor_stage_from_relationship(stage: str) -> str:
    normalized = _lower(stage)
    if normalized == "queued":
        return "TARGET"
    if normalized in {"connection-pending", "connected"}:
        return "OUTREACH"
    if normalized == "engaged":
        return "DISCOVERY"
    if normalized == "qualified-pre-consult":
        return "QUALIFIED"
    if normalized.startswith("meeting") or normalized.startswith("proposal") or normalized == "closed-won":
        return "ENGAGED"
    if normalized == "closed-lost":
        return "DECLINED"
    return "OUTREACH"


def _pursuit_stage_from_relationship(stage: str) -> str:
    normalized = _lower(stage)
    if normalized in {"queued", "connection-pending"}:
        return PursuitStage.INTELLIGENCE.value
    if normalized in {"connected", "engaged"}:
        return PursuitStage.EARLY_QUALIFICATION.value
    if normalized in {
        "qualified-pre-consult",
        "meeting-proposed",
        "meeting-booked",
        "proposal-drafted",
        "proposal-approved",
        "closed-won",
    }:
        return PursuitStage.PRE_RFP_CAPTURE.value
    if normalized == "closed-lost":
        return PursuitStage.LOST.value
    return PursuitStage.EARLY_QUALIFICATION.value


def _lead_time_days(urgency_level: str) -> int:
    normalized = _lower(urgency_level)
    if normalized == "high":
        return 14
    if normalized == "low":
        return 60
    return 30


def _probability_win(stage: str, warm_signal: str) -> int:
    normalized_stage = _lower(stage)
    normalized_signal = _lower(warm_signal)
    if normalized_stage == "qualified-pre-consult" and normalized_signal == "reply":
        return 72
    if normalized_stage.startswith("proposal"):
        return 80
    if normalized_stage.startswith("meeting"):
        return 68
    if normalized_stage == "engaged":
        return 58
    if normalized_stage == "connected":
        return 46
    return 35


def _strategic_alignment(row: dict[str, str]) -> int:
    if _lower(row.get("fit_confirmed")) == "yes" and _lower(row.get("relationship_stage")) in {
        "qualified-pre-consult",
        "meeting-proposed",
        "meeting-booked",
        "proposal-drafted",
        "proposal-approved",
    }:
        return 5
    if _lower(row.get("fit_confirmed")) == "yes":
        return 4
    return 3


def _needs_opportunity(row: dict[str, str], proposal_row: dict[str, str] | None) -> bool:
    stage = _lower(row.get("relationship_stage"))
    if stage in {
        "qualified-pre-consult",
        "meeting-proposed",
        "meeting-booked",
        "proposal-drafted",
        "proposal-approved",
        "closed-won",
        "closed-lost",
    }:
        return True
    if _lower(row.get("fit_confirmed")) == "yes" and _lower(row.get("meeting_needed")) == "yes":
        return True
    if proposal_row and any(
        _text(proposal_row.get(field))
        for field in ("recommended_price_usd", "price_to_win_usd", "price_to_compete_usd", "offer_name")
    ):
        return True
    return False


def _estimated_value(row: dict[str, str], proposal_row: dict[str, str] | None) -> float:
    if proposal_row:
        for field in ("recommended_price_usd", "price_to_win_usd", "price_to_compete_usd"):
            value = _float(proposal_row.get(field))
            if value > 0:
                return value
    offer = _lower(row.get("offer_hypothesis"))
    return DEFAULT_OFFER_VALUES.get(offer, 5500.0)


def _touchpoint_type(channel: str, event_type: str) -> str:
    normalized_channel = _lower(channel)
    normalized_event = _lower(event_type)
    if normalized_channel == "phone":
        return "CALL"
    if normalized_channel == "meeting":
        return "MEETING"
    if normalized_event == "accepted-connection":
        return "INTRO"
    if normalized_event in {"reply", "follow-up"}:
        return "FOLLOW_UP"
    if normalized_channel == "email":
        return "EMAIL"
    return "NOTE"


def _memory_channel(touchpoint_type: str) -> str:
    normalized = _lower(touchpoint_type)
    if normalized == "call":
        return "phone"
    if normalized == "meeting":
        return "meeting"
    if normalized in {"intro", "follow_up"}:
        return "linkedin"
    if normalized == "email":
        return "email"
    return "linkedin"


def _memory_event_type(touchpoint_type: str) -> str:
    normalized = _lower(touchpoint_type)
    if normalized == "intro":
        return "accepted-connection"
    if normalized == "meeting":
        return "meeting"
    if normalized == "call":
        return "reply"
    if normalized == "follow_up":
        return "reply"
    return "note"


def _signal_strength(profile: GrowthRelationshipProfile, touchpoint: ContractorTouchpoint) -> str:
    if _lower(profile.warm_signal) in {"reply", "meeting"} or _lower(touchpoint.touchpoint_type) == "meeting":
        return "warm"
    if _lower(profile.warm_signal) == "accepted-connection":
        return "warm"
    return "medium"


def _touchpoint_key(touchpoint: ContractorTouchpoint) -> tuple[str, str, str]:
    return (
        touchpoint.contractor_id,
        _datetime_string(touchpoint.touchpoint_at),
        _text(touchpoint.summary),
    )


def _profile_row_from_model(profile: GrowthRelationshipProfile) -> dict[str, str]:
    return {
        "relationship_id": profile.relationship_id,
        "created_date": _date_string(profile.created_date),
        "company_name": _text(profile.company_name),
        "contact_name": _text(profile.contact_name),
        "role": _text(profile.role),
        "linkedin_profile_url": _text(profile.linkedin_profile_url),
        "linkedin_company_url": _text(profile.linkedin_company_url),
        "relationship_stage": _text(profile.relationship_stage),
        "warm_signal": _text(profile.warm_signal),
        "fit_confirmed": _text(profile.fit_confirmed),
        "pain_point": _text(profile.pain_point),
        "desired_outcome": _text(profile.desired_outcome),
        "offer_hypothesis": _text(profile.offer_hypothesis),
        "urgency_level": _text(profile.urgency_level),
        "scope_breadth": _text(profile.scope_breadth),
        "stakeholder_complexity": _text(profile.stakeholder_complexity),
        "research_load": _text(profile.research_load),
        "delivery_intensity": _text(profile.delivery_intensity),
        "last_touch_date": _date_string(profile.last_touch_date),
        "last_interaction_summary": _text(profile.last_interaction_summary),
        "next_best_touch_type": _text(profile.next_best_touch_type),
        "next_best_touch_path": _text(profile.next_best_touch_path),
        "meeting_needed": _text(profile.meeting_needed),
        "meeting_status": _text(profile.meeting_status),
        "proposal_status": _text(profile.proposal_status),
        "ptw_status": _text(profile.ptw_status),
        "ptw_stage": _text(profile.ptw_stage),
        "ptw_recommendation": _text(profile.ptw_recommendation),
        "ptw_record_id": _text(profile.ptw_record_id),
        "owner_decision": _text(profile.owner_decision),
        "review_status": _text(profile.review_status),
        "ready_state": _text(profile.ready_state),
        "notes": _text(profile.notes),
    }


def _knowledge_row_from_model(row: GrowthMarketEvidence) -> dict[str, str]:
    return {
        "knowledge_id": row.knowledge_id,
        "relationship_id": _text(row.relationship_id),
        "company_name": _text(row.company_name),
        "entity_type": _text(row.entity_type),
        "entity_name": _text(row.entity_name),
        "source_type": _text(row.source_type),
        "source_reference": _text(row.source_reference),
        "source_date": _date_string(row.source_date),
        "source_reliability": _text(row.source_reliability),
        "confidence": _int_string(row.confidence),
        "customer_objective": _text(row.customer_objective),
        "customer_need": _text(row.customer_need),
        "customer_value_drivers": _text(row.customer_value_drivers),
        "buyer_priorities": _text(row.buyer_priorities),
        "evaluation_priorities": _text(row.evaluation_priorities),
        "buying_behavior": _text(row.buying_behavior),
        "delivery_context": _text(row.delivery_context),
        "timing_context": _text(row.timing_context),
        "budget_signal": _text(row.budget_signal),
        "budget_band": _text(row.budget_band),
        "competitor_name": _text(row.competitor_name),
        "incumbent_status": _text(row.incumbent_status),
        "alternative_option": _text(row.alternative_option),
        "big4_technical": _text(row.big4_technical),
        "big4_management": _text(row.big4_management),
        "big4_past_performance": _text(row.big4_past_performance),
        "big4_cost_price": _text(row.big4_cost_price),
        "differentiation_hypothesis": _text(row.differentiation_hypothesis),
        "evidence_summary": _text(row.evidence_summary),
        "assumptions": _text(row.assumptions),
        "ethical_use_check": _text(row.ethical_use_check),
        "last_validated_date": _date_string(row.last_validated_date),
        "notes": _text(row.notes),
    }


def _proposal_by_relationship(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        relationship_id = _text(row.get("relationship_id"))
        if relationship_id:
            result[relationship_id] = row
    return result


def _upsert_contractor(session, row: dict[str, str]) -> Contractor:
    company_name = _text(row.get("company_name"))
    contractor = session.scalars(select(Contractor).where(Contractor.name == company_name)).first()
    if contractor is None:
        contractor = Contractor(name=company_name)
        session.add(contractor)
        session.flush()
    contractor.prospect_stage = _contractor_stage_from_relationship(row.get("relationship_stage", ""))
    contractor.relationship_strength = 4 if _lower(row.get("warm_signal")) in {"reply", "meeting"} else 3
    contractor.relationship_notes = (
        f"Pain point: {_text(row.get('pain_point'))}\n"
        f"Desired outcome: {_text(row.get('desired_outcome'))}\n"
        f"Latest interaction: {_text(row.get('last_interaction_summary'))}"
    ).strip()
    contractor.strategic_fit_notes = (
        f"Offer hypothesis: {_text(row.get('offer_hypothesis'))}\n"
        f"Fit confirmed: {_text(row.get('fit_confirmed'))}\n"
        f"Warm signal: {_text(row.get('warm_signal'))}"
    ).strip()
    last_touch = _parse_date(row.get("last_touch_date"))
    if last_touch is not None:
        contractor.last_touch_at = datetime.combine(last_touch, time(hour=12))
    return contractor


def _ensure_opportunity(session, row: dict[str, str], contractor: Contractor, proposal_row: dict[str, str] | None) -> Opportunity | None:
    relationship_id = _text(row.get("relationship_id"))
    profile = session.get(GrowthRelationshipProfile, relationship_id)
    opportunity = None
    if profile and profile.current_opportunity_id:
        opportunity = session.get(Opportunity, profile.current_opportunity_id)

    if opportunity is None and not _needs_opportunity(row, proposal_row):
        return None

    explicit_stage = _pursuit_stage_from_relationship(row.get("relationship_stage", ""))
    estimated_value = _estimated_value(row, proposal_row)
    lead_time_days = _lead_time_days(row.get("urgency_level", ""))
    strategic_alignment = _strategic_alignment(row)
    probability = _probability_win(row.get("relationship_stage", ""), row.get("warm_signal", ""))
    confidence_level = _confidence_level_from_row(row)

    if opportunity is None:
        payload = OpportunityIntakeRequest(
            name=f"{contractor.name} Advisory Pursuit",
            client=contractor.name,
            estimated_contract_value=estimated_value,
            lead_time_days=lead_time_days,
            incumbent_status=False,
            strategic_alignment=strategic_alignment,
            estimated_probability_win=probability,
            actor="bosskey-growth-sync",
        )
        opportunity = OpportunityIntakeService(session).create_bootstrapped_pursuit(
            payload,
            explicit_pursuit_stage=explicit_stage,
            confidence_level=confidence_level,
            provenance_summary=f"Boss Key Growth OS advisory pursuit for relationship {relationship_id}.",
            commit=False,
        )
    else:
        opportunity.name = f"{contractor.name} Advisory Pursuit"
        opportunity.client = contractor.name
        opportunity.estimated_contract_value = estimated_value
        opportunity.lead_time_days = lead_time_days
        opportunity.strategic_alignment = strategic_alignment
        opportunity.estimated_probability_win = probability
        opportunity.confidence_level = confidence_level
        opportunity.provenance_summary = f"Boss Key Growth OS advisory pursuit for relationship {relationship_id}."
        sync_pursuit_fields(opportunity, explicit_stage)
    opportunity.weighted_pipeline_value = weighted_pipeline_value(
        opportunity.estimated_contract_value,
        opportunity.qualification_score,
    )
    return opportunity


def _upsert_contact(session, row: dict[str, str], contractor: Contractor, opportunity: Opportunity | None) -> None:
    contact_name = _text(row.get("contact_name"))
    if not contact_name:
        return
    stmt = select(Contact).where(Contact.contractor_id == contractor.id, Contact.full_name == contact_name)
    contact = session.scalars(stmt).first()
    if contact is None:
        contact = Contact(
            contractor_id=contractor.id,
            full_name=contact_name,
        )
        session.add(contact)
    contact.opportunity_id = opportunity.id if opportunity else contact.opportunity_id
    contact.role_title = _text(row.get("role")) or contact.role_title
    contact.contact_side = "CONTRACTOR"
    contact.source_type = "DIRECT_CONVERSATION" if _text(row.get("warm_signal")) else "PUBLIC"
    contact.confidence_level = _confidence_level_from_row(row)
    contact.notes = (
        f"LinkedIn profile: {_text(row.get('linkedin_profile_url'))}\n"
        f"Pain point: {_text(row.get('pain_point'))}\n"
        f"Desired outcome: {_text(row.get('desired_outcome'))}"
    ).strip()


def _upsert_profile(session, row: dict[str, str], contractor: Contractor, opportunity: Opportunity | None) -> GrowthRelationshipProfile:
    relationship_id = _text(row.get("relationship_id"))
    profile = session.get(GrowthRelationshipProfile, relationship_id)
    if profile is None:
        profile = GrowthRelationshipProfile(relationship_id=relationship_id, contractor_id=contractor.id, company_name=contractor.name)
        session.add(profile)
    profile.contractor_id = contractor.id
    profile.current_opportunity_id = opportunity.id if opportunity else profile.current_opportunity_id
    profile.created_date = _parse_date(row.get("created_date"))
    profile.company_name = contractor.name
    profile.contact_name = _text(row.get("contact_name")) or None
    profile.role = _text(row.get("role")) or None
    profile.linkedin_profile_url = _text(row.get("linkedin_profile_url")) or None
    profile.linkedin_company_url = _text(row.get("linkedin_company_url")) or None
    profile.relationship_stage = _text(row.get("relationship_stage")) or "queued"
    profile.warm_signal = _text(row.get("warm_signal")) or None
    profile.fit_confirmed = _text(row.get("fit_confirmed")) or "no"
    profile.pain_point = _text(row.get("pain_point")) or None
    profile.desired_outcome = _text(row.get("desired_outcome")) or None
    profile.offer_hypothesis = _text(row.get("offer_hypothesis")) or None
    profile.urgency_level = _text(row.get("urgency_level")) or None
    profile.scope_breadth = _text(row.get("scope_breadth")) or None
    profile.stakeholder_complexity = _text(row.get("stakeholder_complexity")) or None
    profile.research_load = _text(row.get("research_load")) or None
    profile.delivery_intensity = _text(row.get("delivery_intensity")) or None
    profile.last_touch_date = _parse_date(row.get("last_touch_date"))
    profile.last_interaction_summary = _text(row.get("last_interaction_summary")) or None
    profile.next_best_touch_type = _text(row.get("next_best_touch_type")) or None
    profile.next_best_touch_path = _text(row.get("next_best_touch_path")) or None
    profile.meeting_needed = _text(row.get("meeting_needed")) or "no"
    profile.meeting_status = _text(row.get("meeting_status")) or None
    profile.proposal_status = _text(row.get("proposal_status")) or None
    profile.ptw_status = _text(row.get("ptw_status")) or None
    profile.ptw_stage = _text(row.get("ptw_stage")) or None
    profile.ptw_recommendation = _text(row.get("ptw_recommendation")) or None
    profile.ptw_record_id = _text(row.get("ptw_record_id")) or None
    profile.owner_decision = _text(row.get("owner_decision")) or "hold"
    profile.review_status = _text(row.get("review_status")) or "pending-review"
    profile.ready_state = _text(row.get("ready_state")) or "draft-pending-review"
    profile.notes = _text(row.get("notes")) or None
    return profile


def _upsert_commercial(session, contractor: Contractor, opportunity: Opportunity | None, proposal_row: dict[str, str] | None) -> None:
    if opportunity is None:
        return
    commercial = session.scalars(
        select(CommercialEngagement).where(CommercialEngagement.opportunity_id == opportunity.id)
    ).first()
    if commercial is None:
        commercial = CommercialEngagement(opportunity_id=opportunity.id)
        session.add(commercial)
    commercial.contractor_id = contractor.id
    if proposal_row:
        recommended_price = _float(proposal_row.get("recommended_price_usd")) or _float(proposal_row.get("price_to_win_usd"))
        if recommended_price > 0:
            commercial.retainer_amount = recommended_price
        commercial.notes = _text(proposal_row.get("pricing_rationale")) or commercial.notes
    if commercial.retainer_amount is None:
        commercial.retainer_amount = opportunity.estimated_contract_value
    commercial.weighted_expected_value = round(
        (commercial.retainer_amount or 0.0) * (opportunity.qualification_score / 100.0),
        2,
    )


def _import_touchpoints(session, relationship_rows: list[dict[str, str]], memory_rows: list[dict[str, str]]) -> None:
    rows_by_relationship = {row["relationship_id"]: row for row in relationship_rows if _text(row.get("relationship_id"))}
    contractors_by_relationship: dict[str, Contractor] = {}
    for relationship in relationship_rows:
        contractor = session.scalars(select(Contractor).where(Contractor.name == _text(relationship.get("company_name")))).first()
        if contractor is not None:
            contractors_by_relationship[_text(relationship.get("relationship_id"))] = contractor

    existing = {
        _touchpoint_key(touchpoint): touchpoint
        for touchpoint in session.scalars(select(ContractorTouchpoint)).all()
    }

    for memory in memory_rows:
        relationship_id = _text(memory.get("relationship_id"))
        contractor = contractors_by_relationship.get(relationship_id)
        relationship = rows_by_relationship.get(relationship_id)
        if contractor is None or relationship is None:
            continue
        touchpoint_at = _parse_datetime(memory.get("event_date"))
        if touchpoint_at is None:
            continue
        summary = _text(memory.get("message_summary"))
        key = (contractor.id, _datetime_string(touchpoint_at), summary)
        if key in existing:
            continue
        touchpoint = ContractorTouchpoint(
            contractor_id=contractor.id,
            contact_name=_text(relationship.get("contact_name")) or None,
            touchpoint_type=_touchpoint_type(memory.get("channel", ""), memory.get("event_type", "")),
            touchpoint_at=touchpoint_at,
            summary=summary,
            next_step=_text(memory.get("notes")) or None,
        )
        session.add(touchpoint)
        existing[key] = touchpoint


def _ensure_last_interaction_touchpoints(session, relationship_rows: list[dict[str, str]]) -> None:
    contractors = {
        contractor.name: contractor
        for contractor in session.scalars(select(Contractor)).all()
    }
    existing = {
        _touchpoint_key(touchpoint): touchpoint
        for touchpoint in session.scalars(select(ContractorTouchpoint)).all()
    }
    for row in relationship_rows:
        summary = _text(row.get("last_interaction_summary"))
        last_touch_date = _parse_date(row.get("last_touch_date"))
        contractor = contractors.get(_text(row.get("company_name")))
        if not contractor or not summary or last_touch_date is None:
            continue
        touchpoint_at = datetime.combine(last_touch_date, time(hour=12))
        key = (contractor.id, _datetime_string(touchpoint_at), summary)
        if key in existing:
            continue
        session.add(
            ContractorTouchpoint(
                contractor_id=contractor.id,
                contact_name=_text(row.get("contact_name")) or None,
                touchpoint_type=_touchpoint_type("linkedin", row.get("warm_signal", "")),
                touchpoint_at=touchpoint_at,
                summary=summary,
                next_step=_text(row.get("next_best_touch_type")) or None,
            )
        )
        existing[key] = True


def _import_relationships(
    session,
    relationship_rows: list[dict[str, str]],
    proposal_rows: list[dict[str, str]],
) -> None:
    proposals_by_relationship = _proposal_by_relationship(proposal_rows)
    for row in relationship_rows:
        relationship_id = _text(row.get("relationship_id"))
        if not relationship_id:
            continue
        contractor = _upsert_contractor(session, row)
        proposal_row = proposals_by_relationship.get(relationship_id)
        opportunity = _ensure_opportunity(session, row, contractor, proposal_row)
        _upsert_contact(session, row, contractor, opportunity)
        _upsert_profile(session, row, contractor, opportunity)
        _upsert_commercial(session, contractor, opportunity, proposal_row)


def _import_knowledge(session, knowledge_rows: list[dict[str, str]]) -> None:
    profile_by_relationship = {
        profile.relationship_id: profile
        for profile in session.scalars(select(GrowthRelationshipProfile)).all()
    }
    contractor_by_name = {
        contractor.name: contractor
        for contractor in session.scalars(select(Contractor)).all()
    }
    for row in knowledge_rows:
        knowledge_id = _text(row.get("knowledge_id"))
        if not knowledge_id:
            continue
        evidence = session.get(GrowthMarketEvidence, knowledge_id)
        if evidence is None:
            evidence = GrowthMarketEvidence(knowledge_id=knowledge_id)
            session.add(evidence)
        profile = profile_by_relationship.get(_text(row.get("relationship_id")))
        contractor = contractor_by_name.get(_text(row.get("company_name")))
        evidence.relationship_id = profile.relationship_id if profile else (_text(row.get("relationship_id")) or None)
        evidence.contractor_id = profile.contractor_id if profile else (contractor.id if contractor else None)
        evidence.opportunity_id = (
            profile.current_opportunity_id if profile and profile.current_opportunity_id else None
        )
        evidence.company_name = _text(row.get("company_name")) or None
        evidence.entity_type = _text(row.get("entity_type")) or None
        evidence.entity_name = _text(row.get("entity_name")) or None
        evidence.source_type = _text(row.get("source_type")) or None
        evidence.source_reference = _text(row.get("source_reference")) or None
        evidence.source_date = _parse_date(row.get("source_date"))
        evidence.source_reliability = _text(row.get("source_reliability")) or None
        evidence.confidence = int(_float(row.get("confidence"))) if _text(row.get("confidence")) else None
        evidence.customer_objective = _text(row.get("customer_objective")) or None
        evidence.customer_need = _text(row.get("customer_need")) or None
        evidence.customer_value_drivers = _text(row.get("customer_value_drivers")) or None
        evidence.buyer_priorities = _text(row.get("buyer_priorities")) or None
        evidence.evaluation_priorities = _text(row.get("evaluation_priorities")) or None
        evidence.buying_behavior = _text(row.get("buying_behavior")) or None
        evidence.delivery_context = _text(row.get("delivery_context")) or None
        evidence.timing_context = _text(row.get("timing_context")) or None
        evidence.budget_signal = _text(row.get("budget_signal")) or None
        evidence.budget_band = _text(row.get("budget_band")) or None
        evidence.competitor_name = _text(row.get("competitor_name")) or None
        evidence.incumbent_status = _text(row.get("incumbent_status")) or None
        evidence.alternative_option = _text(row.get("alternative_option")) or None
        evidence.big4_technical = _text(row.get("big4_technical")) or None
        evidence.big4_management = _text(row.get("big4_management")) or None
        evidence.big4_past_performance = _text(row.get("big4_past_performance")) or None
        evidence.big4_cost_price = _text(row.get("big4_cost_price")) or None
        evidence.differentiation_hypothesis = _text(row.get("differentiation_hypothesis")) or None
        evidence.evidence_summary = _text(row.get("evidence_summary")) or None
        evidence.assumptions = _text(row.get("assumptions")) or None
        evidence.ethical_use_check = _text(row.get("ethical_use_check")) or "yes"
        evidence.last_validated_date = _parse_date(row.get("last_validated_date"))
        evidence.notes = _text(row.get("notes")) or None


def bootstrap_from_csv(
    *,
    relationship_path: Path,
    memory_path: Path,
    knowledge_path: Path,
    proposal_path: Path,
) -> None:
    relationship_rows = _read_csv(relationship_path)
    memory_rows = _read_csv(memory_path)
    knowledge_rows = _read_csv(knowledge_path)
    proposal_rows = _read_csv(proposal_path)
    with SessionLocal() as session:
        _import_relationships(session, relationship_rows, proposal_rows)
        session.flush()
        _import_touchpoints(session, relationship_rows, memory_rows)
        _ensure_last_interaction_touchpoints(session, relationship_rows)
        _import_knowledge(session, knowledge_rows)
        session.commit()


def persist_review_state(
    *,
    relationship_path: Path,
    knowledge_path: Path,
    proposal_path: Path,
) -> None:
    relationship_rows = _read_csv(relationship_path)
    knowledge_rows = _read_csv(knowledge_path)
    proposal_rows = _read_csv(proposal_path)
    with SessionLocal() as session:
        _import_relationships(session, relationship_rows, proposal_rows)
        session.flush()
        _import_knowledge(session, knowledge_rows)
        session.commit()


def hydrate_queues(
    *,
    relationship_path: Path,
    memory_path: Path,
    knowledge_path: Path,
) -> None:
    with SessionLocal() as session:
        profiles = list(
            session.scalars(
                select(GrowthRelationshipProfile).order_by(
                    GrowthRelationshipProfile.company_name.asc(),
                    GrowthRelationshipProfile.created_at.asc(),
                )
            )
        )
        profile_rows = [_profile_row_from_model(profile) for profile in profiles]

        relationship_by_contractor = {profile.contractor_id: profile for profile in profiles}
        touchpoints = list(
            session.scalars(
                select(ContractorTouchpoint).order_by(
                    ContractorTouchpoint.touchpoint_at.desc(),
                    ContractorTouchpoint.created_at.desc(),
                )
            )
        )
        memory_rows: list[dict[str, str]] = []
        for touchpoint in touchpoints:
            profile = relationship_by_contractor.get(touchpoint.contractor_id)
            if profile is None:
                continue
            memory_rows.append(
                {
                    "memory_id": f"mem-{touchpoint.id}",
                    "relationship_id": profile.relationship_id,
                    "event_date": _date_string(touchpoint.touchpoint_at.date()),
                    "channel": _memory_channel(touchpoint.touchpoint_type),
                    "event_type": _memory_event_type(touchpoint.touchpoint_type),
                    "signal_strength": _signal_strength(profile, touchpoint),
                    "message_summary": _text(touchpoint.summary),
                    "pain_point": _text(profile.pain_point),
                    "desired_outcome": _text(profile.desired_outcome),
                    "offer_hypothesis": _text(profile.offer_hypothesis),
                    "notes": _text(touchpoint.next_step),
                }
            )

        evidence_rows = list(
            session.scalars(
                select(GrowthMarketEvidence).order_by(
                    GrowthMarketEvidence.source_date.desc().nullslast(),
                    GrowthMarketEvidence.updated_at.desc(),
                )
            )
        )
        knowledge_rows = [_knowledge_row_from_model(row) for row in evidence_rows]

    _write_csv(relationship_path, RELATIONSHIP_FIELDS, profile_rows)
    _write_csv(memory_path, MEMORY_FIELDS, memory_rows)
    _write_csv(knowledge_path, KNOWLEDGE_FIELDS, knowledge_rows)


def _path_arg(raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync Boss Key growth queue projections with proposal-ops.")
    parser.add_argument(
        "--mode",
        choices=["bootstrap", "hydrate-queues", "persist-review-state"],
        required=True,
    )
    parser.add_argument(
        "--relationship-file",
        default="marketing-agents/data/boss_key_relationship_queue.csv",
    )
    parser.add_argument(
        "--conversation-file",
        default="marketing-agents/data/boss_key_conversation_memory.csv",
    )
    parser.add_argument(
        "--knowledge-file",
        default="marketing-agents/data/boss_key_competitive_kb.csv",
    )
    parser.add_argument(
        "--proposal-file",
        default="marketing-agents/data/boss_key_preconsult_proposals.csv",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    relationship_path = _path_arg(args.relationship_file)
    conversation_path = _path_arg(args.conversation_file)
    knowledge_path = _path_arg(args.knowledge_file)
    proposal_path = _path_arg(args.proposal_file)

    if args.mode == "bootstrap":
        bootstrap_from_csv(
            relationship_path=relationship_path,
            memory_path=conversation_path,
            knowledge_path=knowledge_path,
            proposal_path=proposal_path,
        )
        hydrate_queues(
            relationship_path=relationship_path,
            memory_path=conversation_path,
            knowledge_path=knowledge_path,
        )
    elif args.mode == "persist-review-state":
        persist_review_state(
            relationship_path=relationship_path,
            knowledge_path=knowledge_path,
            proposal_path=proposal_path,
        )
    else:
        hydrate_queues(
            relationship_path=relationship_path,
            memory_path=conversation_path,
            knowledge_path=knowledge_path,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
