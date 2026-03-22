import type {
  EngagementGateCode,
  EngagementGateSignal,
  EngagementWorkflowContext,
  EngagementWorkflowStatus
} from "./engagement-workflow-types";
import {
  evaluateEngagementTransition,
  isDuplicateSignal,
  requiredGatesForStage
} from "./engagement-workflow-guards.js";

function ensureSignalContext(ctx: EngagementWorkflowContext) {
  return {
    ...ctx,
    status: ctx.status || ("IN_PROGRESS" as EngagementWorkflowStatus),
    processed_signal_ids: ctx.processed_signal_ids || []
  };
}

export async function runEngagementWorkflow(
  ctx: EngagementWorkflowContext,
  waitForGateSignal: (gate: EngagementGateCode) => Promise<EngagementGateSignal>
): Promise<EngagementWorkflowContext> {
  const current = ensureSignalContext(ctx);
  let context = { ...current };

  const maxIterations = 500;
  let safety = 0;

  while (context.current_stage !== "CLOSED" && safety < maxIterations) {
    safety += 1;
    const requiredGates = requiredGatesForStage(context.current_stage);

    if (!requiredGates.length) {
      const transition = evaluateEngagementTransition(context.current_stage, "APPROVED");
      context.current_stage = transition.next_stage;
      context.status = transition.status;
      continue;
    }

    const gate = requiredGates[0];
    const signal = await waitForGateSignal(gate);
    if (isDuplicateSignal(context.processed_signal_ids, signal)) {
      continue;
    }

    context.processed_signal_ids.push(signal.signal_id);
    const transition = evaluateEngagementTransition(context.current_stage, signal.decision);
    context.current_stage = transition.next_stage;
    context.status = transition.status;
  }

  return context;
}
