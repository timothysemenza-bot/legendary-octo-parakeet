const STAGE_SEQUENCE = [
  "SIGNAL_CAPTURE",
  "ENGAGEMENT_TRIAGE",
  "TIMELINE_SEED",
  "ACTION_SEED",
  "APPROVAL_WAIT",
  "FOUNDER_BRIEF",
  "FOLLOW_THROUGH",
  "KNOWLEDGE_PROMOTION",
  "CLOSED"
];

const REQUIRED_GATES = {
  SIGNAL_CAPTURE: [],
  ENGAGEMENT_TRIAGE: [],
  TIMELINE_SEED: [],
  ACTION_SEED: [],
  APPROVAL_WAIT: ["GATE_APPROVAL_DECISION"],
  FOUNDER_BRIEF: [],
  FOLLOW_THROUGH: [],
  KNOWLEDGE_PROMOTION: [],
  CLOSED: []
};

function requiredGatesForStage(stage) {
  return REQUIRED_GATES[stage] || [];
}

function stageIndex(stage) {
  return STAGE_SEQUENCE.indexOf(stage);
}

function nextStageFor(stage) {
  const idx = stageIndex(stage);
  return idx >= 0 && idx < STAGE_SEQUENCE.length - 1 ? STAGE_SEQUENCE[idx + 1] : stage;
}

function previousStageFor(stage) {
  const idx = stageIndex(stage);
  return idx > 0 ? STAGE_SEQUENCE[idx - 1] : stage;
}

function canProgressToStage(targetStage, gateDecisions) {
  const required = requiredGatesForStage(targetStage);
  return required.every(function (gate) {
    return gateDecisions && gateDecisions[gate] === "APPROVED";
  });
}

function evaluateEngagementTransition(currentStage, decision) {
  if (decision === "APPROVED") {
    const nextStage = nextStageFor(currentStage);
    return {
      allowed: true,
      next_stage: nextStage,
      status: nextStage === "CLOSED" ? "COMPLETED" : "IN_PROGRESS",
      reason: "Gate approved"
    };
  }

  if (decision === "REWORK_REQUIRED") {
    return {
      allowed: true,
      next_stage: currentStage,
      status: "WAITING_APPROVAL",
      reason: "Rework required in current stage"
    };
  }

  if (currentStage === "APPROVAL_WAIT") {
    return {
      allowed: true,
      next_stage: "ENGAGEMENT_TRIAGE",
      status: "IN_PROGRESS",
      reason: "Approval rejected; reopening engagement for triage review"
    };
  }

  return {
    allowed: true,
    next_stage: previousStageFor(currentStage),
    status: currentStage === previousStageFor(currentStage) ? "BLOCKED" : "IN_PROGRESS",
    reason: "Rejected and returned to prior stage"
  };
}

function isDuplicateSignal(processedSignalIds, signal) {
  if (!processedSignalIds || !signal || !signal.signal_id) {
    return false;
  }

  return processedSignalIds.includes(signal.signal_id);
}

module.exports = {
  STAGE_SEQUENCE,
  requiredGatesForStage,
  canProgressToStage,
  evaluateEngagementTransition,
  isDuplicateSignal
};
