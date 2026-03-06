import type { GateCode, GateSignal, Stage, WorkflowContext } from "./workflow-types";
import { evaluateGateTransition } from "../../../packages/workflow-definitions/state-machine";

const STAGE_GATE: Partial<Record<Stage, GateCode[]>> = {
  QUALIFICATION: ["GATE_A"],
  STRATEGY: ["GATE_B"],
  COMPLIANCE: ["GATE_C"],
  REVIEW: ["GATE_D", "GATE_E"],
  SUBMISSION: ["GATE_F"],
  ARCHIVE: ["GATE_G"]
};

// Temporal workflow skeleton:
// - Execute stage activities
// - Wait for required human gate signals
// - Route APPROVED/REWORK_REQUIRED/REJECTED
export async function runProposalWorkflow(
  ctx: WorkflowContext,
  waitForGateSignal: (gate: GateCode) => Promise<GateSignal>
): Promise<WorkflowContext> {
  let current = { ...ctx };
  let done = false;

  while (!done) {
    const requiredGates = STAGE_GATE[current.current_stage] || [];
    for (const gate of requiredGates) {
      const signal = await waitForGateSignal(gate);
      const transition = evaluateGateTransition(current.current_stage, signal.decision);
      current = { ...current, current_stage: transition.next_stage };
    }

    if (current.current_stage === "ARCHIVE") {
      done = true;
      continue;
    }

    // For stages without explicit gates, move linearly.
    if (!requiredGates.length) {
      const transition = evaluateGateTransition(current.current_stage, "APPROVED");
      current = { ...current, current_stage: transition.next_stage };
    }
  }

  return current;
}
