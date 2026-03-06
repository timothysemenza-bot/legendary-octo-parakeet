const REQUIRED_GATES = {
  QUALIFICATION: ["GATE_A"],
  STRATEGY: ["GATE_B"],
  COMPLIANCE: ["GATE_C"],
  REVIEW: ["GATE_D", "GATE_E"],
  SUBMISSION: ["GATE_F"],
  ARCHIVE: ["GATE_G"]
};

function requiredGatesForStage(stage) {
  return REQUIRED_GATES[stage] || [];
}

function canProgressToStage(targetStage, gateDecisions) {
  if (targetStage === "DRAFTING") {
    return gateDecisions.GATE_C === "APPROVED";
  }

  if (targetStage === "SUBMISSION") {
    return gateDecisions.GATE_D === "APPROVED" && gateDecisions.GATE_E === "APPROVED";
  }

  if (targetStage === "ARCHIVE") {
    return gateDecisions.GATE_F === "APPROVED";
  }

  return true;
}

module.exports = {
  requiredGatesForStage,
  canProgressToStage
};
