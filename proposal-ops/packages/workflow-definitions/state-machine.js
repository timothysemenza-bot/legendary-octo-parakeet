const STAGE_SEQUENCE = [
  "INTAKE",
  "QUALIFICATION",
  "STRATEGY",
  "COMPLIANCE",
  "CONTENT_PLANNING",
  "DRAFTING",
  "REVIEW",
  "SUBMISSION",
  "ARCHIVE"
];

function evaluateGateTransition(stage, decision) {
  const index = STAGE_SEQUENCE.indexOf(stage);
  const previous = index > 0 ? STAGE_SEQUENCE[index - 1] : stage;
  const next = index < STAGE_SEQUENCE.length - 1 ? STAGE_SEQUENCE[index + 1] : stage;

  if (decision === "APPROVED") {
    return { allowed: true, next_stage: next, status: "IN_PROGRESS", reason: "Gate approved" };
  }

  if (decision === "REWORK_REQUIRED") {
    return { allowed: true, next_stage: stage, status: "IN_PROGRESS", reason: "Rework required in current stage" };
  }

  return { allowed: true, next_stage: previous, status: "BLOCKED", reason: "Rejected and returned to prior stage" };
}

function canEnterDrafting(gateCDecision) {
  return gateCDecision === "APPROVED";
}

function canAuthorizeSubmission(gateFDecision) {
  return gateFDecision === "APPROVED";
}

module.exports = {
  STAGE_SEQUENCE,
  evaluateGateTransition,
  canEnterDrafting,
  canAuthorizeSubmission
};
