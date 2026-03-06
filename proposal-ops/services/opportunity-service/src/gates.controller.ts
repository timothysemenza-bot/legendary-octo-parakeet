import type { GateCode, GateDecisionRequest, GateDecisionResponse } from "./contracts";
import { evaluateGateTransition } from "../../../packages/workflow-definitions/state-machine";

const GATE_STAGE_MAP: Record<GateCode, Parameters<typeof evaluateGateTransition>[0]> = {
  GATE_A: "QUALIFICATION",
  GATE_B: "STRATEGY",
  GATE_C: "COMPLIANCE",
  GATE_D: "REVIEW",
  GATE_E: "REVIEW",
  GATE_F: "SUBMISSION",
  GATE_G: "ARCHIVE"
};

export class GatesController {
  decide(opportunityId: string, gateCode: GateCode, body: GateDecisionRequest): GateDecisionResponse {
    const stage = GATE_STAGE_MAP[gateCode];
    const transition = evaluateGateTransition(stage, body.decision);

    return {
      gate_decision_id: `gtd_${Date.now()}`,
      opportunity_id: opportunityId,
      gate_code: gateCode,
      decision: body.decision,
      resulting_stage: transition.next_stage,
      status: transition.status
    };
  }
}
