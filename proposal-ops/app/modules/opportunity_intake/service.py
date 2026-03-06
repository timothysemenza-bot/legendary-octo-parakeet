import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.core.policy import is_role_authorized_for_gate
from app.core.workflow import (
    GateCode,
    GateDecision,
    OpportunityStage,
    active_gate_for_stage,
    can_enter_stage,
    evaluate_gate_transition,
    normalize_gate_code,
)
from app.modules.compliance_matrix.service import ComplianceMatrixService
from app.modules.identity.service import IdentityService
from app.modules.opportunity_intake.models import CapturePlan, GateDecisionRecord, Opportunity
from app.modules.opportunity_intake.repository import OpportunityRepository
from app.modules.opportunity_intake.scoring import (
    classify_recommendation,
    classify_tier,
    compute_intake_score,
)
from app.modules.review_manager.service import ReviewManagerService
from app.modules.submission_checklist.service import SubmissionChecklistService
from app.modules.knowledge.service import KnowledgeService
from app.modules.opportunity_intake.schemas import (
    GateDecisionRequest,
    OpportunityDetailResponse,
    OpportunityIntakeRequest,
    OpportunityIntakeResult,
    ScoreBreakdown,
    GateInboxItemResponse,
    StageTransitionRequest,
    StageTransitionResponse,
)


def _generate_capture_plan_template(opportunity: Opportunity) -> CapturePlan:
    return CapturePlan(
        opportunity_id=opportunity.id,
        version=1,
        summary=f"{opportunity.name} pursuit for {opportunity.client}.",
        client_priorities="Identify buyer priorities, constraints, and decision criteria.",
        competitive_landscape="Map incumbent position, likely competitors, and differentiation gaps.",
        win_themes_draft="Theme 1: reduced risk; Theme 2: proven performance; Theme 3: rapid mobilization.",
        solution_positioning="Position solution benefits before features with evidence-backed claims.",
        timeline="T-45 kickoff, T-30 content lock, T-14 red review, T-7 gold review, T-1 final packaging.",
    )


def _safe_json_parse(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _timeline_category(action: str) -> str:
    if action.startswith("gate_") or action.startswith("bid_decision"):
        return "GATE"
    if action.startswith("stage_transition"):
        return "STAGE"
    if action.startswith("review_"):
        return "REVIEW"
    if action.startswith("submission_"):
        return "SUBMISSION"
    if action.startswith("compliance_") or action.startswith("rfp_"):
        return "COMPLIANCE"
    if action.startswith("knowledge_"):
        return "KNOWLEDGE"
    return "SYSTEM"


def _timeline_summary(action: str, details: dict[str, Any]) -> str:
    if action == "stage_transition_recorded":
        return f"Stage transitioned to {details.get('stage', 'UNKNOWN')}."
    if action == "gate_decision_recorded":
        return f"{details.get('gate_code', 'GATE')} decision: {details.get('decision', 'UNKNOWN')}."
    if action == "bid_decision_recorded":
        return f"Bid decision recorded: {details.get('decision', 'UNKNOWN')}."
    if action == "review_cycle_created":
        return f"{details.get('review_type', 'REVIEW')} review cycle created."
    if action == "review_cycle_closed":
        return f"{details.get('review_type', 'REVIEW')} review cycle closed."
    if action == "review_comment_created":
        return f"Review comment added ({details.get('severity', 'UNKNOWN')})."
    if action == "review_comment_resolved":
        return "Review comment resolved."
    if action == "submission_checklist_item_updated":
        return f"Submission checklist item updated ({details.get('item_code', 'ITEM')})."
    if action == "submission_filename_validation_ran":
        return "Submission file naming validation executed."
    if action == "compliance_matrix_row_updated":
        return "Compliance matrix row updated."
    if action == "rfp_parsed":
        return "RFP parsed into structured requirements."
    return action.replace("_", " ").capitalize() + "."


class OpportunityIntakeService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = OpportunityRepository(db)

    def intake(self, payload: OpportunityIntakeRequest) -> OpportunityIntakeResult:
        score, breakdown = compute_intake_score(
            strategic_alignment=payload.strategic_alignment,
            probability_win=payload.estimated_probability_win,
            lead_time_days=payload.lead_time_days,
            contract_value=payload.estimated_contract_value,
            incumbent_status=payload.incumbent_status,
        )
        recommendation = classify_recommendation(score)
        tier = classify_tier(score, payload.estimated_contract_value)

        opportunity = Opportunity(
            name=payload.name,
            client=payload.client,
            estimated_contract_value=payload.estimated_contract_value,
            lead_time_days=payload.lead_time_days,
            incumbent_status=payload.incumbent_status,
            strategic_alignment=payload.strategic_alignment,
            estimated_probability_win=payload.estimated_probability_win,
            qualification_score=score,
            tier=tier.value,
            pursuit_recommendation=recommendation.value,
            stage=OpportunityStage.INTAKE.value,
        )
        self.repo.add_opportunity(opportunity)
        log_audit_event(
            self.db,
            opportunity_id=opportunity.id,
            actor=payload.actor,
            action="intake_submitted",
            after_state_json=payload.model_dump_json(),
        )

        log_audit_event(
            self.db,
            opportunity_id=opportunity.id,
            actor=payload.actor,
            action="intake_scored",
            after_state_json=json.dumps({"score": score, "tier": tier.value, "recommendation": recommendation.value}),
        )

        capture_plan = _generate_capture_plan_template(opportunity)
        self.repo.add_capture_plan(capture_plan)

        log_audit_event(
            self.db,
            opportunity_id=opportunity.id,
            actor=payload.actor,
            action="capture_plan_generated",
            after_state_json=json.dumps({"capture_plan_id": capture_plan.id, "version": capture_plan.version}),
        )

        self.db.commit()
        return OpportunityIntakeResult(
            id=opportunity.id,
            qualification_score=score,
            tier=tier,
            pursuit_recommendation=recommendation,
            capture_plan_id=capture_plan.id,
            score_breakdown=ScoreBreakdown(**breakdown),
        )

    def list_opportunities(self) -> list[Opportunity]:
        return self.repo.list_opportunities()

    def workflow_timeline(
        self, opportunity_id: str, *, category: str = "ALL", limit: int = 200
    ) -> list[dict[str, Any]]:
        events = self.repo.list_audit_events(opportunity_id)
        normalized_category = category.upper()
        rows: list[dict[str, Any]] = []
        for event in events[:limit]:
            details = _safe_json_parse(event.after_state_json)
            row_category = _timeline_category(event.action)
            if normalized_category != "ALL" and row_category != normalized_category:
                continue
            rows.append(
                {
                    "timestamp": event.created_at,
                    "actor": event.actor,
                    "action": event.action,
                    "category": row_category,
                    "summary": _timeline_summary(event.action, details),
                    "details": details,
                }
            )
        return rows

    def get_detail(self, opportunity_id: str) -> OpportunityDetailResponse | None:
        opportunity = self.repo.get_opportunity(opportunity_id)
        if not opportunity:
            return None
        capture_plan = self.repo.get_latest_capture_plan(opportunity_id)
        gate_decisions = self.repo.list_gate_decisions(opportunity_id)
        audit_events = self.repo.list_audit_events(opportunity_id)

        return OpportunityDetailResponse(
            id=opportunity.id,
            name=opportunity.name,
            client=opportunity.client,
            estimated_contract_value=opportunity.estimated_contract_value,
            lead_time_days=opportunity.lead_time_days,
            incumbent_status=opportunity.incumbent_status,
            strategic_alignment=opportunity.strategic_alignment,
            estimated_probability_win=opportunity.estimated_probability_win,
            qualification_score=opportunity.qualification_score,
            tier=opportunity.tier,
            pursuit_recommendation=opportunity.pursuit_recommendation,
            stage=opportunity.stage,
            created_at=opportunity.created_at,
            updated_at=opportunity.updated_at,
            capture_plan=capture_plan,
            gate_decisions=gate_decisions,
            audit_events=audit_events,
        )

    def add_gate_decision(self, opportunity_id: str, payload: GateDecisionRequest) -> GateDecisionRecord | None:
        opportunity = self.repo.get_opportunity(opportunity_id)
        if not opportunity:
            return None

        gate_code = normalize_gate_code(payload.gate_code)
        expected_gate_code = active_gate_for_stage(opportunity.stage)
        GateCode(gate_code)  # raises ValueError if unknown
        GateDecision(payload.decision)  # raises ValueError if unknown
        if gate_code != expected_gate_code:
            log_audit_event(
                self.db,
                opportunity_id=opportunity_id,
                actor=payload.decider,
                action="gate_policy_violation",
                after_state_json=json.dumps(
                    {
                        "gate_code": gate_code,
                        "expected_gate_code": expected_gate_code,
                        "stage": opportunity.stage,
                        "decision": payload.decision,
                        "reason": "Gate decision does not match active stage gate",
                    }
                ),
            )
            self.db.commit()
            raise ValueError(
                f"{gate_code} cannot be decided while opportunity is in {opportunity.stage}. Active gate is {expected_gate_code}."
            )

        if payload.decision == GateDecision.REWORK_REQUIRED.value and not payload.rework_instructions:
            raise ValueError("rework_instructions are required when decision is REWORK_REQUIRED.")

        resolved_decider = payload.decider
        resolved_decider_role = payload.decider_role
        resolved_decider_user_id = payload.decider_user_id

        if payload.decider_user_id:
            identity = IdentityService(self.db)
            user = identity.get_user(payload.decider_user_id)
            if not user or user.status != "ACTIVE":
                raise ValueError("decider_user_id is not an active user.")
            allowed_role = identity.resolve_authorized_role_for_gate(payload.decider_user_id, gate_code, opportunity_id)
            if not allowed_role:
                log_audit_event(
                    self.db,
                    opportunity_id=opportunity_id,
                    actor=payload.decider,
                    action="gate_policy_violation",
                    after_state_json=json.dumps(
                        {
                            "gate_code": gate_code,
                            "decision": payload.decision,
                            "decider_user_id": payload.decider_user_id,
                            "reason": "User lacks scoped authorized role for gate",
                        }
                    ),
                )
                self.db.commit()
                raise ValueError(f"User '{payload.decider_user_id}' is not authorized to act on {gate_code}.")
            resolved_decider = user.display_name
            resolved_decider_role = allowed_role
        elif not is_role_authorized_for_gate(gate_code, payload.decider_role):
            log_audit_event(
                self.db,
                opportunity_id=opportunity_id,
                actor=payload.decider,
                action="gate_policy_violation",
                after_state_json=json.dumps(
                    {
                        "gate_code": gate_code,
                        "decision": payload.decision,
                        "decider_role": payload.decider_role,
                        "reason": "Role is not authorized for gate action",
                    }
                ),
            )
            self.db.commit()
            raise ValueError(
                f"Role '{payload.decider_role}' is not authorized to act on {gate_code}."
            )

        # Gate C cannot be approved unless matrix quality is ready.
        if gate_code == GateCode.GATE_C.value and payload.decision == GateDecision.APPROVED.value:
            quality = ComplianceMatrixService(self.db).matrix_quality(opportunity_id)
            if not quality["gate_c_ready"]:
                raise ValueError(
                    f"Gate C cannot be approved: {'; '.join(quality['gate_c_blockers'])}"
                )
        if gate_code == GateCode.GATE_D.value and payload.decision == GateDecision.APPROVED.value:
            readiness = ReviewManagerService(self.db).review_readiness(opportunity_id)
            if not readiness.gate_d_ready:
                raise ValueError(f"Gate D cannot be approved: {'; '.join(readiness.gate_d_blockers)}")
        if gate_code == GateCode.GATE_E.value and payload.decision == GateDecision.APPROVED.value:
            readiness = ReviewManagerService(self.db).review_readiness(opportunity_id)
            if not readiness.gate_e_ready:
                raise ValueError(f"Gate E cannot be approved: {'; '.join(readiness.gate_e_blockers)}")
        if gate_code == GateCode.GATE_F.value and payload.decision == GateDecision.APPROVED.value:
            submission = SubmissionChecklistService(self.db).readiness(opportunity_id)
            if not submission.ready_for_gate_f:
                raise ValueError(f"Gate F cannot be approved: {'; '.join(submission.blockers)}")
        if gate_code == GateCode.GATE_G.value and payload.decision == GateDecision.APPROVED.value:
            knowledge = KnowledgeService(self.db).readiness(opportunity_id)
            if not knowledge.gate_g_ready:
                raise ValueError(f"Gate G cannot be approved: {'; '.join(knowledge.blockers)}")

        before_stage = opportunity.stage
        _, next_stage = evaluate_gate_transition(opportunity.stage, gate_code, payload.decision)
        decision_timestamp = datetime.now()
        approval_signature = None
        if payload.decider_user_id and payload.decision in {
            GateDecision.APPROVED.value,
            GateDecision.REJECTED.value,
            GateDecision.REWORK_REQUIRED.value,
        }:
            approval_signature = IdentityService(self.db).sign_gate_approval(
                user_id=payload.decider_user_id,
                opportunity_id=opportunity_id,
                gate_code=gate_code,
                decision=payload.decision,
                rationale=payload.rationale,
                timestamp=decision_timestamp,
            )

        record = GateDecisionRecord(
            opportunity_id=opportunity_id,
            gate_code=gate_code,
            decision=payload.decision,
            decider=resolved_decider,
            decider_user_id=resolved_decider_user_id,
            decider_role=resolved_decider_role,
            approval_signature=approval_signature,
            rationale=payload.rationale,
            rework_instructions=payload.rework_instructions,
            rework_owner=payload.rework_owner,
            rework_due_date=(
                datetime.combine(payload.rework_due_date, datetime.min.time())
                if payload.rework_due_date
                else None
            ),
        )
        self.repo.add_gate_decision(record)

        opportunity.stage = next_stage
        self.db.flush()

        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=payload.decider,
            action="gate_decision_recorded",
            before_state_json=json.dumps({"stage": before_stage}),
            after_state_json=json.dumps(
                {
                    "gate_code": gate_code,
                    "decision": payload.decision,
                    "decider_user_id": resolved_decider_user_id,
                    "decider_role": resolved_decider_role,
                    "approval_signature": approval_signature,
                    "stage": next_stage,
                    "rationale": payload.rationale,
                    "rework_instructions": payload.rework_instructions,
                    "rework_owner": payload.rework_owner,
                    "rework_due_date": payload.rework_due_date.isoformat() if payload.rework_due_date else None,
                }
            ),
        )
        if gate_code == GateCode.GATE_A.value:
            # Backward-compatible audit action for existing analytics/tests.
            log_audit_event(
                self.db,
                opportunity_id=opportunity_id,
                actor=payload.decider,
                action="bid_decision_recorded",
                after_state_json=payload.model_dump_json(),
            )
        self.db.commit()
        return record

    def preview_stage_transition(self, opportunity_id: str, payload: StageTransitionRequest) -> StageTransitionResponse | None:
        opportunity = self.repo.get_opportunity(opportunity_id)
        if not opportunity:
            return None

        transition_gate = active_gate_for_stage(opportunity.stage)
        blockers: list[str] = []
        if payload.actor_user_id:
            identity = IdentityService(self.db)
            user = identity.get_user(payload.actor_user_id)
            if not user or user.status != "ACTIVE":
                blockers.append("actor_user_id is not an active user.")
            else:
                allowed_role = identity.resolve_authorized_role_for_gate(
                    payload.actor_user_id, transition_gate, opportunity_id
                )
                if not allowed_role:
                    blockers.append(
                        f"User '{payload.actor_user_id}' is not authorized to transition from {opportunity.stage}."
                    )
        elif not is_role_authorized_for_gate(transition_gate, payload.actor_role):
            blockers.append(f"Role '{payload.actor_role}' is not authorized to transition from {opportunity.stage}.")

        gate_decisions = self.repo.list_gate_decisions(opportunity_id)
        latest_by_gate: dict[str, str] = {}
        for decision in gate_decisions:
            if decision.gate_code not in latest_by_gate:
                latest_by_gate[decision.gate_code] = decision.decision
        approved_gates = {gate for gate, decision in latest_by_gate.items() if decision == GateDecision.APPROVED.value}

        allowed, stage_blockers = can_enter_stage(opportunity.stage, payload.next_stage, approved_gates)
        blockers.extend(stage_blockers)
        _ = allowed  # clarity: included via blockers aggregation
        return StageTransitionResponse(
            opportunity_id=opportunity_id,
            from_stage=opportunity.stage,
            to_stage=payload.next_stage,
            blockers=blockers,
        )

    def transition_stage(self, opportunity_id: str, payload: StageTransitionRequest) -> StageTransitionResponse | None:
        preview = self.preview_stage_transition(opportunity_id, payload)
        if not preview:
            return None
        if preview.blockers:
            if any("not authorized" in b.lower() or "active user" in b.lower() for b in preview.blockers):
                opportunity = self.repo.get_opportunity(opportunity_id)
                if opportunity:
                    log_audit_event(
                        self.db,
                        opportunity_id=opportunity_id,
                        actor=payload.actor,
                        action="stage_transition_policy_violation",
                        after_state_json=json.dumps(
                            {
                                "from_stage": opportunity.stage,
                                "to_stage": payload.next_stage,
                                "reason": "; ".join(preview.blockers),
                            }
                        ),
                    )
                    self.db.commit()
            return preview

        opportunity = self.repo.get_opportunity(opportunity_id)
        if not opportunity:
            return None
        transition_gate = active_gate_for_stage(opportunity.stage)
        resolved_actor = payload.actor
        resolved_actor_role = payload.actor_role
        resolved_actor_user_id = payload.actor_user_id

        if payload.actor_user_id:
            identity = IdentityService(self.db)
            user = identity.get_user(payload.actor_user_id)
            if not user or user.status != "ACTIVE":
                return preview
            allowed_role = identity.resolve_authorized_role_for_gate(
                payload.actor_user_id, transition_gate, opportunity_id
            )
            if not allowed_role:
                return preview
            resolved_actor = user.display_name
            resolved_actor_role = allowed_role
        elif not is_role_authorized_for_gate(transition_gate, payload.actor_role):
            return preview

        before_stage = opportunity.stage
        opportunity.stage = payload.next_stage
        self.db.flush()
        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=resolved_actor,
            action="stage_transition_recorded",
            before_state_json=json.dumps({"stage": before_stage}),
            after_state_json=json.dumps(
                {
                    "stage": payload.next_stage,
                    "reason": payload.reason,
                    "actor_user_id": resolved_actor_user_id,
                    "actor_role": resolved_actor_role,
                    "transition_gate": transition_gate,
                }
            ),
        )
        self.db.commit()
        return StageTransitionResponse(
            opportunity_id=opportunity_id,
            from_stage=before_stage,
            to_stage=payload.next_stage,
            blockers=[],
        )

    def list_gate_inbox(self) -> list[GateInboxItemResponse]:
        opportunities = self.repo.list_opportunities()
        now = datetime.now()
        sla_days_by_gate = {
            GateCode.GATE_A.value: 2,
            GateCode.GATE_B.value: 3,
            GateCode.GATE_C.value: 5,
            GateCode.GATE_D.value: 5,
            GateCode.GATE_E.value: 3,
            GateCode.GATE_F.value: 2,
            GateCode.GATE_G.value: 7,
        }
        items: list[GateInboxItemResponse] = []

        for opp in opportunities:
            gate_code = active_gate_for_stage(opp.stage)
            decisions = self.repo.list_gate_decisions(opp.id)
            latest_for_gate = next((d for d in decisions if normalize_gate_code(d.gate_code) == gate_code), None)
            gate_status = latest_for_gate.decision if latest_for_gate else GateDecision.PENDING.value
            if gate_status == GateDecision.APPROVED.value:
                continue

            age_source = opp.updated_at or opp.created_at
            days_in_stage = max(0, (now - age_source).days)
            sla_days = sla_days_by_gate[gate_code]
            blockers: list[str] = []
            if gate_code == GateCode.GATE_C.value:
                quality = ComplianceMatrixService(self.db).matrix_quality(opp.id)
                blockers.extend(quality["gate_c_blockers"])
            if gate_code == GateCode.GATE_F.value:
                submission = SubmissionChecklistService(self.db).readiness(opp.id)
                blockers.extend(submission.blockers)
            if gate_code == GateCode.GATE_G.value:
                knowledge = KnowledgeService(self.db).readiness(opp.id)
                blockers.extend(knowledge.blockers)

            items.append(
                GateInboxItemResponse(
                    opportunity_id=opp.id,
                    opportunity_name=opp.name,
                    client=opp.client,
                    stage=opp.stage,
                    gate_code=gate_code,
                    gate_status=gate_status,
                    latest_decider=latest_for_gate.decider if latest_for_gate else None,
                    latest_decision_at=latest_for_gate.created_at if latest_for_gate else None,
                    days_in_stage=days_in_stage,
                    sla_days=sla_days,
                    sla_breached=days_in_stage > sla_days,
                    blockers=blockers,
                )
            )
        return items
