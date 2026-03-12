import json
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.modules.janitorial_os.models import CommercialEngagement, Contractor, Organization
from app.modules.opportunity_intake.schemas import OpportunityIntakeRequest, PursuitStage
from app.modules.opportunity_intake.service import OpportunityIntakeService
from app.modules.opportunity_intelligence.models import (
    OpportunityHypothesis,
    SignalEvent,
    SignalSource,
)
from app.modules.opportunity_intelligence.schemas import (
    HypothesisStage,
    HypothesisConversionCreate,
    HypothesisConversionResponse,
    OpportunityHypothesisCreate,
    OpportunityHypothesisResponse,
    OpportunityIntelligenceSummaryResponse,
    SignalEventCreate,
    SignalEventResponse,
    SignalSourceCreate,
    SignalSourceResponse,
)


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class OpportunityIntelligenceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _source_response(self, row: SignalSource) -> SignalSourceResponse:
        return SignalSourceResponse.model_validate(row, from_attributes=True)

    def _signal_response(self, row: SignalEvent) -> SignalEventResponse:
        return SignalEventResponse(
            id=row.id,
            source_id=row.source_id,
            source_name=row.source.name if row.source else None,
            title=row.title,
            signal_type=row.signal_type,
            signal_date=row.signal_date,
            jurisdiction=row.jurisdiction,
            agency_name=row.agency_name,
            program_name=row.program_name,
            summary=row.summary,
            confidence_level=row.confidence_level,
            source_url=row.source_url,
            source_reference=row.source_reference,
            recommended_action=row.recommended_action,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _hypothesis_response(self, row: OpportunityHypothesis) -> OpportunityHypothesisResponse:
        return OpportunityHypothesisResponse(
            id=row.id,
            title=row.title,
            sector=row.sector,
            geography=row.geography,
            buying_organization=row.buying_organization,
            buying_organization_id=row.buying_organization_id,
            buying_organization_name=self._organization_name(row.buying_organization_id) or row.buying_organization,
            service_line=row.service_line,
            stage=row.stage,
            confidence_level=row.confidence_level,
            expected_release_start=row.expected_release_start,
            expected_release_end=row.expected_release_end,
            summary=row.summary,
            recommended_action=row.recommended_action,
            primary_signal_event_id=row.primary_signal_event_id,
            primary_signal_event_title=row.primary_signal_event.title if row.primary_signal_event else None,
            recommended_contractor_id=row.recommended_contractor_id,
            recommended_contractor_name=row.recommended_contractor.name if row.recommended_contractor else None,
            converted_opportunity_id=row.converted_opportunity_id,
            converted_opportunity_name=row.converted_opportunity.name if row.converted_opportunity else None,
            converted_at=row.converted_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _organization_name(self, organization_id: str | None) -> str | None:
        if not organization_id:
            return None
        organization = self.db.get(Organization, organization_id)
        return organization.name if organization else None

    def get_opportunity_hypothesis(self, hypothesis_id: str) -> OpportunityHypothesis | None:
        return self.db.get(OpportunityHypothesis, hypothesis_id)

    def list_signal_sources(self) -> list[SignalSource]:
        stmt = select(SignalSource).order_by(SignalSource.name.asc())
        return list(self.db.scalars(stmt))

    def create_signal_source(self, payload: SignalSourceCreate) -> SignalSource:
        duplicate = self.db.scalars(select(SignalSource).where(SignalSource.name == payload.name)).first()
        if duplicate:
            raise ValueError("Signal source name already exists.")
        row = SignalSource(**payload.model_dump())
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_signal_events(self) -> list[SignalEvent]:
        stmt = select(SignalEvent).order_by(SignalEvent.signal_date.desc(), SignalEvent.created_at.desc())
        return list(self.db.scalars(stmt))

    def create_signal_event(self, payload: SignalEventCreate) -> SignalEvent:
        source = self.db.get(SignalSource, payload.source_id)
        if not source:
            raise ValueError("source_id is not valid.")
        row = SignalEvent(**payload.model_dump())
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_opportunity_hypotheses(self) -> list[OpportunityHypothesis]:
        stmt = select(OpportunityHypothesis).order_by(
            OpportunityHypothesis.expected_release_start.asc().nulls_last(),
            OpportunityHypothesis.created_at.desc(),
        )
        return list(self.db.scalars(stmt))

    def create_opportunity_hypothesis(self, payload: OpportunityHypothesisCreate) -> OpportunityHypothesis:
        if payload.primary_signal_event_id and not self.db.get(SignalEvent, payload.primary_signal_event_id):
            raise ValueError("primary_signal_event_id is not valid.")
        if payload.recommended_contractor_id and not self.db.get(Contractor, payload.recommended_contractor_id):
            raise ValueError("recommended_contractor_id is not valid.")
        values = payload.model_dump()
        if payload.buying_organization_id:
            organization = self.db.get(Organization, payload.buying_organization_id)
            if not organization:
                raise ValueError("buying_organization_id is not valid.")
            values["buying_organization"] = organization.name
        row = OpportunityHypothesis(**values)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def _default_probability_from_confidence(self, confidence_level: str) -> int:
        if confidence_level == "HIGH":
            return 70
        if confidence_level == "LOW":
            return 35
        return 50

    def _default_lead_time_days(self, hypothesis: OpportunityHypothesis) -> int | None:
        target_date = hypothesis.expected_release_start or hypothesis.expected_release_end
        if not target_date:
            return None
        return max(1, (target_date - date.today()).days)

    def _resolve_buying_organization(self, *, organization_id: str | None, client_name: str | None) -> tuple[str | None, str | None]:
        if organization_id:
            organization = self.db.get(Organization, organization_id)
            if not organization:
                raise ValueError("buying_organization_id is not valid.")
            return organization.id, organization.name
        if not client_name:
            return None, None
        organization = self.db.scalars(select(Organization).where(Organization.name == client_name)).first()
        if organization:
            return organization.id, organization.name
        return None, client_name

    def _provenance_summary(self, hypothesis: OpportunityHypothesis) -> str:
        signal = hypothesis.primary_signal_event
        fragments = [f"Originated from opportunity hypothesis: {hypothesis.title}."]
        if signal:
            fragments.append(f"Primary signal: {signal.title}.")
        fragments.append(hypothesis.summary)
        if hypothesis.recommended_action:
            fragments.append(f"Recommended action: {hypothesis.recommended_action}")
        return " ".join(fragment.strip() for fragment in fragments if fragment).strip()

    def _seed_recommended_contractor(
        self,
        *,
        opportunity_id: str,
        contractor_id: str,
        actor: str,
    ) -> Contractor:
        contractor = self.db.get(Contractor, contractor_id)
        if not contractor:
            raise ValueError("contractor_id is not valid.")

        commercial = self.db.scalars(
            select(CommercialEngagement).where(CommercialEngagement.opportunity_id == opportunity_id)
        ).first()
        if not commercial:
            commercial = CommercialEngagement(opportunity_id=opportunity_id)
            self.db.add(commercial)
        commercial.contractor_id = contractor.id
        self.db.flush()

        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=actor,
            action="contractor_linked_to_opportunity",
            after_state_json=json.dumps(
                {
                    "contractor_id": contractor.id,
                    "commercial_id": commercial.id,
                }
            ),
        )
        return contractor

    def convert_hypothesis_to_pursuit(
        self,
        hypothesis_id: str,
        payload: HypothesisConversionCreate,
    ) -> HypothesisConversionResponse:
        hypothesis = self.db.get(OpportunityHypothesis, hypothesis_id)
        if not hypothesis:
            raise LookupError("Opportunity hypothesis not found.")
        if hypothesis.converted_opportunity_id:
            raise ValueError("Opportunity hypothesis has already been converted to a pursuit.")

        buying_organization_id, client_name = self._resolve_buying_organization(
            organization_id=hypothesis.buying_organization_id,
            client_name=payload.client_name or hypothesis.buying_organization,
        )
        if not client_name:
            raise ValueError("client_name is required when the hypothesis does not yet include a buying organization.")

        lead_time_days = payload.lead_time_days or self._default_lead_time_days(hypothesis)
        if not lead_time_days:
            raise ValueError("lead_time_days is required when the hypothesis does not include an expected release window.")

        estimated_probability_win = (
            payload.estimated_probability_win
            if payload.estimated_probability_win is not None
            else self._default_probability_from_confidence(hypothesis.confidence_level)
        )
        expected_rfp_date = payload.expected_rfp_date or hypothesis.expected_release_start

        intake_service = OpportunityIntakeService(self.db)
        opportunity = intake_service.create_bootstrapped_pursuit(
            OpportunityIntakeRequest(
                name=payload.name or hypothesis.title,
                client=client_name,
                estimated_contract_value=payload.estimated_contract_value,
                lead_time_days=lead_time_days,
                incumbent_status=payload.incumbent_status,
                strategic_alignment=payload.strategic_alignment,
                estimated_probability_win=estimated_probability_win,
                actor=payload.actor,
            ),
            explicit_pursuit_stage=payload.pursuit_stage.value,
            buying_organization_id=buying_organization_id,
            confidence_level=hypothesis.confidence_level,
            expected_rfp_date=expected_rfp_date,
            provenance_summary=self._provenance_summary(hypothesis),
            provenance_last_verified_at=_utcnow(),
            commit=False,
        )
        selected_contractor_id = payload.contractor_id or hypothesis.recommended_contractor_id
        seeded_contractor = None
        if selected_contractor_id:
            seeded_contractor = self._seed_recommended_contractor(
                opportunity_id=opportunity.id,
                contractor_id=selected_contractor_id,
                actor=payload.actor,
            )

        hypothesis.stage = HypothesisStage.CONVERTED.value
        hypothesis.converted_opportunity_id = opportunity.id
        hypothesis.converted_at = _utcnow()
        self.db.flush()

        log_audit_event(
            self.db,
            opportunity_id=opportunity.id,
            actor=payload.actor,
            action="pursuit_created_from_hypothesis",
            after_state_json=json.dumps(
                {
                    "hypothesis_id": hypothesis.id,
                    "hypothesis_title": hypothesis.title,
                    "pursuit_stage": opportunity.pursuit_stage,
                    "client": client_name,
                    "contractor_id": seeded_contractor.id if seeded_contractor else None,
                }
            ),
        )
        self.db.commit()
        self.db.refresh(hypothesis)
        self.db.refresh(opportunity)
        detail = intake_service.get_detail(opportunity.id)
        if not detail:
            raise LookupError("Converted pursuit could not be loaded after creation.")
        return HypothesisConversionResponse(
            hypothesis=self._hypothesis_response(hypothesis),
            opportunity=detail,
        )

    def summary(self) -> OpportunityIntelligenceSummaryResponse:
        recent_events = self.list_signal_events()[:8]
        hypotheses = self.list_opportunity_hypotheses()
        active_hypotheses = [
            row for row in hypotheses if row.stage not in {HypothesisStage.CONVERTED.value, HypothesisStage.CLOSED.value}
        ]
        return OpportunityIntelligenceSummaryResponse(
            generated_at=_utcnow(),
            signal_sources_total=self.db.scalar(select(func.count()).select_from(SignalSource)) or 0,
            signal_events_total=self.db.scalar(select(func.count()).select_from(SignalEvent)) or 0,
            open_hypotheses_total=len(active_hypotheses),
            recent_signal_events=[self._signal_response(row) for row in recent_events],
            active_hypotheses=[self._hypothesis_response(row) for row in active_hypotheses[:8]],
        )

    def seed_demo_data(self) -> None:
        if self.db.scalar(select(func.count()).select_from(SignalSource)):
            return

        source = SignalSource(
            name="New Jersey Municipal Budget Watch",
            source_type="BUDGET",
            region="Mid-Atlantic",
            owner_scope="State and Local",
            source_url="https://example.org/nj-budget-watch",
            notes="Synthetic policy and budget feed for demo use.",
        )
        self.db.add(source)
        self.db.flush()

        event = SignalEvent(
            source_id=source.id,
            title="Airport authority budget expands landside operations funding",
            signal_type="FUNDING",
            signal_date=date.today() - timedelta(days=10),
            jurisdiction="NJ",
            agency_name="South Jersey Regional Airport",
            program_name="Operations and Facilities",
            summary="Budget packet increases landside operations and facility support funding ahead of the next fiscal year.",
            confidence_level="HIGH",
            source_url="https://example.org/nj-budget-watch/airport",
            source_reference="FY budget packet section 4",
            recommended_action="Qualify likely janitorial and day porter rebid timing with the authority and incumbent posture.",
        )
        self.db.add(event)
        self.db.flush()

        hypothesis = OpportunityHypothesis(
            title="Airport landside janitorial rebid likely in next budget cycle",
            sector="Facilities Services",
            geography="New Jersey",
            buying_organization="South Jersey Regional Airport",
            service_line="Janitorial and Day Porter",
            stage="CAPTURE_READY",
            confidence_level="HIGH",
            expected_release_start=date.today() + timedelta(days=45),
            expected_release_end=date.today() + timedelta(days=120),
            summary="Budget expansion and contract timing suggest a near-term rebid window for landside janitorial services.",
            recommended_action="Begin incumbent assessment, stakeholder mapping, and contractor outreach before the pre-solicitation window.",
            primary_signal_event_id=event.id,
        )
        self.db.add(hypothesis)
        self.db.commit()
