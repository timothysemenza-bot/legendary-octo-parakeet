import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.modules.capture_plan.schemas import CapturePlanUpdateRequest
from app.modules.opportunity_intake.models import CapturePlan, Opportunity


class CapturePlanService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_opportunity(self, opportunity_id: str) -> Opportunity | None:
        return self.db.get(Opportunity, opportunity_id)

    def get_latest(self, opportunity_id: str) -> CapturePlan | None:
        stmt = (
            select(CapturePlan)
            .where(CapturePlan.opportunity_id == opportunity_id)
            .order_by(CapturePlan.version.desc(), CapturePlan.created_at.desc())
        )
        return self.db.scalars(stmt).first()

    def list_versions(self, opportunity_id: str) -> list[CapturePlan]:
        stmt = (
            select(CapturePlan)
            .where(CapturePlan.opportunity_id == opportunity_id)
            .order_by(CapturePlan.version.desc(), CapturePlan.created_at.desc())
        )
        return list(self.db.scalars(stmt))

    def create_version(self, opportunity_id: str, payload: CapturePlanUpdateRequest) -> CapturePlan:
        opportunity = self._get_opportunity(opportunity_id)
        if not opportunity:
            raise ValueError("Opportunity not found")

        latest = self.get_latest(opportunity_id)
        next_version = 1 if latest is None else latest.version + 1
        created = CapturePlan(
            opportunity_id=opportunity_id,
            version=next_version,
            summary=payload.summary,
            client_priorities=payload.client_priorities,
            competitive_landscape=payload.competitive_landscape,
            win_themes_draft=payload.win_themes_draft,
            solution_positioning=payload.solution_positioning,
            timeline=payload.timeline,
        )
        self.db.add(created)
        self.db.flush()
        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=payload.actor,
            action="capture_plan_version_created",
            before_state_json=json.dumps(
                {"previous_capture_plan_id": latest.id if latest else None, "previous_version": latest.version if latest else None}
            ),
            after_state_json=json.dumps({"capture_plan_id": created.id, "version": created.version}),
        )
        self.db.commit()
        self.db.refresh(created)
        return created
