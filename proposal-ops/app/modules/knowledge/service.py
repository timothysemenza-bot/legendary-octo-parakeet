import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.modules.knowledge.models import KnowledgePromotion, LessonsLearnedRecord
from app.modules.knowledge.schemas import (
    KnowledgePromotionDecisionRequest,
    KnowledgeReadinessResponse,
    LessonsRecordApproveRequest,
    LessonsRecordCreateRequest,
    LessonsRecordResponse,
    KnowledgePromotionResponse,
)


def _record_to_response(record: LessonsLearnedRecord, promotions: list[KnowledgePromotion]) -> LessonsRecordResponse:
    return LessonsRecordResponse(
        id=record.id,
        opportunity_id=record.opportunity_id,
        outcome=record.outcome,
        root_causes=json.loads(record.root_causes_json or "[]"),
        actions=json.loads(record.actions_json or "[]"),
        status=record.status,
        created_by=record.created_by,
        approved_by=record.approved_by,
        approved_at=record.approved_at,
        created_at=record.created_at,
        updated_at=record.updated_at,
        promotions=[KnowledgePromotionResponse.model_validate(p, from_attributes=True) for p in promotions],
    )


class KnowledgeService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_records(self, opportunity_id: str) -> list[LessonsRecordResponse]:
        stmt = (
            select(LessonsLearnedRecord)
            .where(LessonsLearnedRecord.opportunity_id == opportunity_id)
            .order_by(LessonsLearnedRecord.created_at.desc())
        )
        records = list(self.db.scalars(stmt))
        results: list[LessonsRecordResponse] = []
        for record in records:
            promos = self.list_promotions(record.id)
            results.append(_record_to_response(record, promos))
        return results

    def get_record(self, opportunity_id: str, record_id: str) -> LessonsRecordResponse | None:
        record = self.db.get(LessonsLearnedRecord, record_id)
        if not record or record.opportunity_id != opportunity_id:
            return None
        return _record_to_response(record, self.list_promotions(record.id))

    def create_record(self, opportunity_id: str, payload: LessonsRecordCreateRequest) -> LessonsRecordResponse:
        record = LessonsLearnedRecord(
            opportunity_id=opportunity_id,
            outcome=payload.outcome,
            root_causes_json=json.dumps(payload.root_causes),
            actions_json=json.dumps(payload.actions),
            status="DRAFT",
            created_by=payload.created_by,
        )
        self.db.add(record)
        self.db.flush()

        for promo in payload.promotions:
            self.db.add(
                KnowledgePromotion(
                    lessons_record_id=record.id,
                    asset_title=promo.asset_title,
                    asset_type=promo.asset_type,
                    rationale=promo.rationale,
                    promotion_status="PENDING",
                    created_by=payload.created_by,
                )
            )
        self.db.flush()
        promotions = self.list_promotions(record.id)
        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=payload.created_by,
            action="lessons_record_created",
            after_state_json=json.dumps(
                {
                    "lessons_record_id": record.id,
                    "outcome": record.outcome,
                    "promotion_count": len(promotions),
                }
            ),
        )
        self.db.commit()
        return _record_to_response(record, promotions)

    def approve_record(
        self, opportunity_id: str, record_id: str, payload: LessonsRecordApproveRequest
    ) -> LessonsRecordResponse | None:
        record = self.db.get(LessonsLearnedRecord, record_id)
        if not record or record.opportunity_id != opportunity_id:
            return None
        record.status = "APPROVED"
        record.approved_by = payload.actor
        record.approved_at = datetime.now()
        self.db.flush()
        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=payload.actor,
            action="lessons_record_approved",
            after_state_json=json.dumps({"lessons_record_id": record.id}),
        )
        self.db.commit()
        return _record_to_response(record, self.list_promotions(record.id))

    def list_promotions(self, record_id: str) -> list[KnowledgePromotion]:
        stmt = (
            select(KnowledgePromotion)
            .where(KnowledgePromotion.lessons_record_id == record_id)
            .order_by(KnowledgePromotion.created_at.asc())
        )
        return list(self.db.scalars(stmt))

    def decide_promotion(
        self, promotion_id: str, payload: KnowledgePromotionDecisionRequest
    ) -> KnowledgePromotionResponse | None:
        promo = self.db.get(KnowledgePromotion, promotion_id)
        if not promo:
            return None
        promo.promotion_status = payload.decision
        promo.decided_by = payload.actor
        promo.decided_at = datetime.now()
        self.db.flush()
        record = self.db.get(LessonsLearnedRecord, promo.lessons_record_id)
        log_audit_event(
            self.db,
            opportunity_id=record.opportunity_id if record else None,
            actor=payload.actor,
            action="knowledge_promotion_decided",
            after_state_json=json.dumps(
                {
                    "promotion_id": promo.id,
                    "decision": payload.decision,
                    "lessons_record_id": promo.lessons_record_id,
                }
            ),
        )
        self.db.commit()
        return KnowledgePromotionResponse.model_validate(promo, from_attributes=True)

    def readiness(self, opportunity_id: str) -> KnowledgeReadinessResponse:
        records = self.list_records(opportunity_id)
        blockers: list[str] = []
        if not records:
            blockers.append("No lessons learned record exists.")
            return KnowledgeReadinessResponse(opportunity_id=opportunity_id, gate_g_ready=False, blockers=blockers)

        approved = [r for r in records if r.status == "APPROVED"]
        if not approved:
            blockers.append("No approved lessons learned record.")
            return KnowledgeReadinessResponse(opportunity_id=opportunity_id, gate_g_ready=False, blockers=blockers)

        latest = approved[0]
        pending_promotions = [p for p in latest.promotions if p.promotion_status == "PENDING"]
        if pending_promotions:
            blockers.append(f"{len(pending_promotions)} knowledge promotions are still PENDING.")

        return KnowledgeReadinessResponse(
            opportunity_id=opportunity_id,
            gate_g_ready=len(blockers) == 0,
            blockers=blockers,
        )

