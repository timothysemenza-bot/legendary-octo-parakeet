export type PursuitRecommendation = "pursue" | "review" | "no-bid";
export type RiskSeverity = "low" | "medium" | "high";

export interface RiskFlag {
  code: string;
  title: string;
  severity: RiskSeverity;
  detail: string;
}

export interface QualificationResult {
  score: number;
  status: PursuitRecommendation;
  rationale: string[];
  riskFlags: RiskFlag[];
  recommendedActions: string[];
  assumptions: string[];
}

