from collections import Counter
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.workflow import GateCode, GateDecision, OpportunityStage
from app.modules.opportunity_intake.models import GateDecisionRecord, Opportunity
from app.modules.opportunity_intake.service import OpportunityIntakeService
from app.modules.ops_reporting.schemas import (
    BlockerAgingMetric,
    DefectRatesMetric,
    GateLatencyMetric,
    OpsMetricsResponse,
    ReworkVelocityMetric,
)
from app.modules.review_manager.models import ReviewComment


class OpsReportingService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _gate_latency_metrics(self) -> list[GateLatencyMetric]:
        stmt = select(GateDecisionRecord).order_by(
            GateDecisionRecord.opportunity_id.asc(),
            GateDecisionRecord.gate_code.asc(),
            GateDecisionRecord.created_at.asc(),
        )
        records = list(self.db.scalars(stmt))
        by_key: dict[tuple[str, str], list[GateDecisionRecord]] = {}
        for r in records:
            by_key.setdefault((r.opportunity_id, r.gate_code), []).append(r)

        by_gate: dict[str, list[float]] = {g.value: [] for g in GateCode}
        for (_, gate_code), decisions in by_key.items():
            first = decisions[0]
            approved = next((d for d in decisions if d.decision == GateDecision.APPROVED.value), None)
            if approved:
                delta = approved.created_at - first.created_at
                by_gate[gate_code].append(delta.total_seconds() / 3600.0)

        metrics: list[GateLatencyMetric] = []
        for gate in GateCode:
            values = by_gate[gate.value]
            avg = round(sum(values) / len(values), 2) if values else 0.0
            metrics.append(
                GateLatencyMetric(
                    gate_code=gate.value,
                    approvals=len(values),
                    avg_hours_to_approval=avg,
                )
            )
        return metrics

    def _rework_velocity(self) -> ReworkVelocityMetric:
        stmt = select(GateDecisionRecord).order_by(
            GateDecisionRecord.opportunity_id.asc(),
            GateDecisionRecord.gate_code.asc(),
            GateDecisionRecord.created_at.asc(),
        )
        records = list(self.db.scalars(stmt))
        by_key: dict[tuple[str, str], list[GateDecisionRecord]] = {}
        for r in records:
            by_key.setdefault((r.opportunity_id, r.gate_code), []).append(r)

        rework_events = 0
        resolved = 0
        unresolved = 0
        resolve_hours: list[float] = []
        for (_, _), decisions in by_key.items():
            for decision in decisions:
                if decision.decision != GateDecision.REWORK_REQUIRED.value:
                    continue
                rework_events += 1
                later_approved = next(
                    (d for d in decisions if d.created_at > decision.created_at and d.decision == GateDecision.APPROVED.value),
                    None,
                )
                if later_approved:
                    resolved += 1
                    delta = later_approved.created_at - decision.created_at
                    resolve_hours.append(delta.total_seconds() / 3600.0)
                else:
                    unresolved += 1

        resolution_rate = round((resolved / rework_events) * 100.0, 2) if rework_events else 0.0
        avg_hours = round(sum(resolve_hours) / len(resolve_hours), 2) if resolve_hours else 0.0
        return ReworkVelocityMetric(
            rework_events=rework_events,
            resolved_reworks=resolved,
            unresolved_reworks=unresolved,
            resolution_rate=resolution_rate,
            avg_hours_to_resolve=avg_hours,
        )

    def _defect_rates(self) -> DefectRatesMetric:
        comments = list(self.db.scalars(select(ReviewComment)))
        total = len(comments)
        open_comments = sum(1 for c in comments if c.resolution_status != "RESOLVED")
        high_open = sum(
            1
            for c in comments
            if c.resolution_status != "RESOLVED" and c.severity in {"HIGH", "CRITICAL"}
        )
        by_severity = Counter(c.severity for c in comments)
        return DefectRatesMetric(
            total_comments=total,
            open_comments=open_comments,
            high_or_critical_open=high_open,
            by_severity=dict(by_severity),
        )

    def _blocker_aging(self) -> BlockerAgingMetric:
        inbox = OpportunityIntakeService(self.db).list_gate_inbox()
        pending = len(inbox)
        breached = sum(1 for i in inbox if i.sla_breached)
        with_blockers = sum(1 for i in inbox if i.blockers)
        blocker_counter: Counter[str] = Counter()
        for item in inbox:
            blocker_counter.update(item.blockers)
        top_blockers = [{"blocker": name, "count": count} for name, count in blocker_counter.most_common(5)]
        return BlockerAgingMetric(
            pending_gate_items=pending,
            breached_sla_items=breached,
            items_with_blockers=with_blockers,
            top_blockers=top_blockers,
        )

    def metrics(self) -> OpsMetricsResponse:
        opportunities = list(self.db.scalars(select(Opportunity)))
        open_stages = {
            OpportunityStage.INTAKE.value,
            OpportunityStage.QUALIFICATION.value,
            OpportunityStage.STRATEGY.value,
            OpportunityStage.COMPLIANCE.value,
            OpportunityStage.CONTENT_PLANNING.value,
            OpportunityStage.DRAFTING.value,
            OpportunityStage.REVIEW.value,
            OpportunityStage.SUBMISSION.value,
        }
        open_count = sum(1 for o in opportunities if o.stage in open_stages)
        return OpsMetricsResponse(
            generated_at=datetime.now(),
            opportunities_total=len(opportunities),
            open_opportunities=open_count,
            gate_latency=self._gate_latency_metrics(),
            rework_velocity=self._rework_velocity(),
            defect_rates=self._defect_rates(),
            blocker_aging=self._blocker_aging(),
        )

