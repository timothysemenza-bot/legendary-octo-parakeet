import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.modules.review_manager.models import ReviewComment, ReviewCycle
from app.modules.review_manager.schemas import (
    ReviewCommentCreateRequest,
    ReviewCommentResolveRequest,
    ReviewCycleCloseRequest,
    ReviewCycleCreateRequest,
    ReviewReadinessResponse,
)


class ReviewManagerService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_cycles(self, opportunity_id: str) -> list[ReviewCycle]:
        stmt = (
            select(ReviewCycle)
            .where(ReviewCycle.opportunity_id == opportunity_id)
            .order_by(ReviewCycle.started_at.desc())
        )
        return list(self.db.scalars(stmt))

    def create_cycle(self, opportunity_id: str, payload: ReviewCycleCreateRequest) -> ReviewCycle:
        cycle = ReviewCycle(
            opportunity_id=opportunity_id,
            review_type=payload.review_type,
            round_number=payload.round_number,
            status="OPEN",
        )
        self.db.add(cycle)
        self.db.flush()
        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=payload.actor,
            action="review_cycle_created",
            after_state_json=json.dumps(
                {
                    "review_cycle_id": cycle.id,
                    "review_type": cycle.review_type,
                    "round_number": cycle.round_number,
                }
            ),
        )
        self.db.commit()
        return cycle

    def close_cycle(self, opportunity_id: str, cycle_id: str, payload: ReviewCycleCloseRequest) -> ReviewCycle | None:
        cycle = self.db.get(ReviewCycle, cycle_id)
        if not cycle or cycle.opportunity_id != opportunity_id:
            return None
        cycle.status = "CLOSED"
        cycle.closed_at = datetime.now()
        self.db.flush()
        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=payload.actor,
            action="review_cycle_closed",
            after_state_json=json.dumps({"review_cycle_id": cycle.id, "review_type": cycle.review_type}),
        )
        self.db.commit()
        return cycle

    def list_comments(self, cycle_id: str) -> list[ReviewComment]:
        stmt = (
            select(ReviewComment)
            .where(ReviewComment.review_cycle_id == cycle_id)
            .order_by(ReviewComment.created_at.desc())
        )
        return list(self.db.scalars(stmt))

    def create_comment(self, cycle_id: str, payload: ReviewCommentCreateRequest) -> ReviewComment | None:
        cycle = self.db.get(ReviewCycle, cycle_id)
        if not cycle:
            return None
        comment = ReviewComment(
            review_cycle_id=cycle_id,
            requirement_id=payload.requirement_id,
            section_code=payload.section_code,
            severity=payload.severity,
            comment_text=payload.comment_text,
            owner=payload.owner,
            created_by=payload.created_by,
            resolution_status="OPEN",
        )
        self.db.add(comment)
        self.db.flush()
        log_audit_event(
            self.db,
            opportunity_id=cycle.opportunity_id,
            actor=payload.created_by,
            action="review_comment_created",
            after_state_json=json.dumps(
                {
                    "review_cycle_id": cycle_id,
                    "comment_id": comment.id,
                    "severity": comment.severity,
                }
            ),
        )
        self.db.commit()
        return comment

    def resolve_comment(self, comment_id: str, payload: ReviewCommentResolveRequest) -> ReviewComment | None:
        comment = self.db.get(ReviewComment, comment_id)
        if not comment:
            return None
        comment.resolution_status = "RESOLVED"
        comment.resolved_at = datetime.now()
        self.db.flush()
        cycle = self.db.get(ReviewCycle, comment.review_cycle_id)
        log_audit_event(
            self.db,
            opportunity_id=cycle.opportunity_id if cycle else None,
            actor=payload.actor,
            action="review_comment_resolved",
            after_state_json=json.dumps({"comment_id": comment.id}),
        )
        self.db.commit()
        return comment

    def review_readiness(self, opportunity_id: str) -> ReviewReadinessResponse:
        cycles = self.list_cycles(opportunity_id)
        cycle_by_type = {}
        for cycle in cycles:
            if cycle.review_type not in cycle_by_type:
                cycle_by_type[cycle.review_type] = cycle

        gate_d_blockers: list[str] = []
        pink = cycle_by_type.get("PINK")
        if not pink:
            gate_d_blockers.append("No PINK review cycle exists.")
        elif pink.status != "CLOSED":
            gate_d_blockers.append("PINK review cycle is not CLOSED.")
        else:
            pink_comments = self.list_comments(pink.id)
            unresolved_high = [
                c for c in pink_comments if c.resolution_status != "RESOLVED" and c.severity in {"HIGH", "CRITICAL"}
            ]
            if unresolved_high:
                gate_d_blockers.append(
                    f"{len(unresolved_high)} HIGH/CRITICAL comments unresolved in PINK review."
                )

        gate_e_blockers: list[str] = []
        red = cycle_by_type.get("RED")
        gold = cycle_by_type.get("GOLD")
        selected = red or gold
        if not selected:
            gate_e_blockers.append("No RED or GOLD review cycle exists.")
        elif selected.status != "CLOSED":
            gate_e_blockers.append(f"{selected.review_type} review cycle is not CLOSED.")
        else:
            selected_comments = self.list_comments(selected.id)
            unresolved = [c for c in selected_comments if c.resolution_status != "RESOLVED"]
            if unresolved:
                gate_e_blockers.append(
                    f"{len(unresolved)} comments unresolved in {selected.review_type} review."
                )

        return ReviewReadinessResponse(
            opportunity_id=opportunity_id,
            gate_d_ready=len(gate_d_blockers) == 0,
            gate_d_blockers=gate_d_blockers,
            gate_e_ready=len(gate_e_blockers) == 0,
            gate_e_blockers=gate_e_blockers,
        )
