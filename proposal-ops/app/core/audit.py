from sqlalchemy.orm import Session

from app.modules.opportunity_intake.models import AuditEvent


def log_audit_event(
    db: Session,
    *,
    opportunity_id: str | None,
    actor: str,
    action: str,
    before_state_json: str | None = None,
    after_state_json: str | None = None,
) -> AuditEvent:
    event = AuditEvent(
        opportunity_id=opportunity_id,
        actor=actor,
        action=action,
        before_state_json=before_state_json,
        after_state_json=after_state_json,
    )
    db.add(event)
    db.flush()
    return event

