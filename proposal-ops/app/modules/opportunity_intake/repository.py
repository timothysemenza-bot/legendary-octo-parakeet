from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.opportunity_intake.models import (
    AuditEvent,
    CapturePlan,
    GateDecisionRecord,
    Opportunity,
)


class OpportunityRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add_opportunity(self, opportunity: Opportunity) -> Opportunity:
        self.db.add(opportunity)
        self.db.flush()
        return opportunity

    def add_capture_plan(self, capture_plan: CapturePlan) -> CapturePlan:
        self.db.add(capture_plan)
        self.db.flush()
        return capture_plan

    def add_gate_decision(self, record: GateDecisionRecord) -> GateDecisionRecord:
        self.db.add(record)
        self.db.flush()
        return record

    def add_audit_event(self, event: AuditEvent) -> AuditEvent:
        self.db.add(event)
        self.db.flush()
        return event

    def list_opportunities(self) -> list[Opportunity]:
        stmt = select(Opportunity).order_by(Opportunity.created_at.desc())
        return list(self.db.scalars(stmt))

    def get_opportunity(self, opportunity_id: str) -> Opportunity | None:
        return self.db.get(Opportunity, opportunity_id)

    def get_latest_capture_plan(self, opportunity_id: str) -> CapturePlan | None:
        stmt = (
            select(CapturePlan)
            .where(CapturePlan.opportunity_id == opportunity_id)
            .order_by(CapturePlan.created_at.desc())
        )
        return self.db.scalars(stmt).first()

    def list_gate_decisions(self, opportunity_id: str) -> list[GateDecisionRecord]:
        stmt = (
            select(GateDecisionRecord)
            .where(GateDecisionRecord.opportunity_id == opportunity_id)
            .order_by(GateDecisionRecord.created_at.desc())
        )
        return list(self.db.scalars(stmt))

    def list_audit_events(self, opportunity_id: str) -> list[AuditEvent]:
        stmt = (
            select(AuditEvent)
            .where(AuditEvent.opportunity_id == opportunity_id)
            .order_by(AuditEvent.created_at.desc())
        )
        return list(self.db.scalars(stmt))

