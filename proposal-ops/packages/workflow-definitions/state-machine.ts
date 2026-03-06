export const STAGE_SEQUENCE = [
  "INTAKE",
  "QUALIFICATION",
  "STRATEGY",
  "COMPLIANCE",
  "CONTENT_PLANNING",
  "DRAFTING",
  "REVIEW",
  "SUBMISSION",
  "ARCHIVE"
] as const;

export type Stage = (typeof STAGE_SEQUENCE)[number];
export type GateCode = "GATE_A" | "GATE_B" | "GATE_C" | "GATE_D" | "GATE_E" | "GATE_F" | "GATE_G";
export type GateDecisionValue = "APPROVED" | "REJECTED" | "REWORK_REQUIRED";

export const STAGE_GATE_MAP: Record<Stage, GateCode[]> = {
  INTAKE: [],
  QUALIFICATION: ["GATE_A"],
  STRATEGY: ["GATE_B"],
  COMPLIANCE: ["GATE_C"],
  CONTENT_PLANNING: [],
  DRAFTING: [],
  REVIEW: ["GATE_D", "GATE_E"],
  SUBMISSION: ["GATE_F"],
  ARCHIVE: ["GATE_G"]
};

export interface TransitionResult {
  allowed: boolean;
  next_stage: Stage;
  status: "IN_PROGRESS" | "BLOCKED";
  reason: string;
}

export function evaluateGateTransition(stage: Stage, decision: GateDecisionValue): TransitionResult {
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

export function canEnterDrafting(gateCDecision: GateDecisionValue | null): boolean {
  return gateCDecision === "APPROVED";
}

export function canAuthorizeSubmission(gateFDecision: GateDecisionValue | null): boolean {
  return gateFDecision === "APPROVED";
}
