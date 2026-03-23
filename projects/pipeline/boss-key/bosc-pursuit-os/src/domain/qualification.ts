export const PURSUIT_RECOMMENDATIONS = [
  "pursue",
  "review",
  "no-bid",
] as const;
export const QUALIFICATION_DECISION_MODES = [
  "pending",
  "follow-engine",
  "override",
] as const;

export type PursuitRecommendation = (typeof PURSUIT_RECOMMENDATIONS)[number];
export type RiskSeverity = "low" | "medium" | "high";
export type QualificationDecisionMode =
  (typeof QUALIFICATION_DECISION_MODES)[number];

export interface RiskFlag {
  code: string;
  title: string;
  severity: RiskSeverity;
  detail: string;
}

export interface QualificationScoreBreakdownItem {
  code: string;
  label: string;
  points: number;
  detail: string;
}

export interface QualificationDecision {
  mode: QualificationDecisionMode;
  selectedStatus: PursuitRecommendation | null;
  note: string;
  decidedAt: string | null;
}

export interface QualificationResult {
  score: number;
  recommendedStatus: PursuitRecommendation;
  status: PursuitRecommendation;
  scoreBreakdown: QualificationScoreBreakdownItem[];
  rationale: string[];
  riskFlags: RiskFlag[];
  recommendedActions: string[];
  assumptions: string[];
}

export function createDefaultQualificationDecision(): QualificationDecision {
  return {
    mode: "pending",
    selectedStatus: null,
    note: "",
    decidedAt: null,
  };
}

export function hasRecordedQualificationDecision(
  decision: QualificationDecision | null | undefined,
): boolean {
  return Boolean(decision && decision.mode !== "pending");
}

export function applyQualificationDecision(
  result: QualificationResult,
  decision: QualificationDecision | null | undefined,
): QualificationResult {
  const status =
    decision?.mode === "override" && decision.selectedStatus
      ? decision.selectedStatus
      : result.recommendedStatus;

  return {
    ...result,
    status,
  };
}

