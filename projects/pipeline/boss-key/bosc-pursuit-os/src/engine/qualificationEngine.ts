import type { Opportunity } from "../domain/opportunity";
import type {
  PursuitRecommendation,
  QualificationResult,
  RiskFlag,
} from "../domain/qualification";

const strategicFitPoints = {
  high: 20,
  medium: 10,
  low: -15,
} as const;

const relationshipPoints = {
  high: 15,
  medium: 7,
  low: -10,
} as const;

const pricingPressurePoints = {
  low: 6,
  medium: 0,
  high: -12,
} as const;

function clampScore(score: number): number {
  return Math.max(0, Math.min(100, score));
}

export function qualifyOpportunity(opportunity: Opportunity): QualificationResult {
  let score = 50;
  const rationale: string[] = [];
  const riskFlags: RiskFlag[] = [];
  const recommendedActions: string[] = [];
  const assumptions: string[] = [
    "Qualification assumes Boss Key prefers self-performed janitorial and facilities scopes in preferred regional coverage zones.",
  ];

  score += strategicFitPoints[opportunity.pursuitContext.strategicFit];
  rationale.push(
    `Strategic fit is ${opportunity.pursuitContext.strategicFit}, which shifts the score toward Boss Key's target services profile.`,
  );

  score += relationshipPoints[opportunity.pursuitContext.relationshipStrength];
  rationale.push(
    `Relationship strength is ${opportunity.pursuitContext.relationshipStrength}, affecting sales cycle confidence and buyer access.`,
  );

  score += pricingPressurePoints[opportunity.pursuitContext.pricingPressure];
  if (opportunity.pursuitContext.pricingPressure === "high") {
    riskFlags.push({
      code: "pricing-pressure",
      title: "Heavy pricing pressure",
      severity: "medium",
      detail:
        "Buyer context suggests a price-led decision, which can compress margin and reduce room for differentiation.",
    });
    recommendedActions.push(
      "Confirm whether the buyer will evaluate on operating outcomes and transition confidence rather than rate alone.",
    );
  }

  if (opportunity.geography.inPreferredRegion) {
    score += 12;
    rationale.push("Opportunity sits inside a preferred coverage region.");
  } else {
    score -= 18;
    riskFlags.push({
      code: "coverage-region",
      title: "Outside preferred region",
      severity: "high",
      detail:
        "Opportunity is outside the preferred operating region, increasing staffing and management complexity.",
    });
    recommendedActions.push(
      "Validate whether trusted local coverage can be stood up without diluting self-performed delivery.",
    );
  }

  if (opportunity.contract.annualValueEstimate >= 500000) {
    score += 10;
    rationale.push("Annual value is large enough to justify pursuit effort.");
  } else if (opportunity.contract.annualValueEstimate < 250000) {
    score -= 10;
    riskFlags.push({
      code: "small-deal",
      title: "Limited contract value",
      severity: "medium",
      detail:
        "Opportunity value may be too small to absorb mobilization effort and executive attention.",
    });
  }

  if (opportunity.contract.targetGrossMarginPercent >= 18) {
    score += 10;
    rationale.push("Target margin supports a differentiated, self-performed operating model.");
  } else if (opportunity.contract.targetGrossMarginPercent >= 14) {
    score += 2;
    riskFlags.push({
      code: "tight-margin",
      title: "Margin is workable but tight",
      severity: "medium",
      detail:
        "Current target margin leaves less room for visible support labor and launch stabilization.",
    });
    recommendedActions.push(
      "Stress-test staffing assumptions before finalizing pursue posture.",
    );
  } else {
    score -= 18;
    riskFlags.push({
      code: "margin-floor",
      title: "Margin floor not met",
      severity: "high",
      detail:
        "Target margin is below the floor needed for sustainable service delivery and transition quality.",
    });
    recommendedActions.push(
      "Do not advance without a commercial reset or explicit decision to accept lower economics.",
    );
  }

  if (opportunity.contract.transitionDays < 21) {
    score -= 12;
    riskFlags.push({
      code: "compressed-transition",
      title: "Compressed transition window",
      severity: "medium",
      detail:
        "Short transition timing increases labor mobilization risk and weakens launch control.",
    });
    recommendedActions.push(
      "Ask for a staged launch plan or earlier access to incumbent site data and staffing requirements.",
    );
  } else {
    score += 5;
    rationale.push("Transition window is long enough for a structured mobilization plan.");
  }

  if (opportunity.siteProfile.unionEnvironment) {
    score -= 10;
    riskFlags.push({
      code: "union-complexity",
      title: "Union labor environment",
      severity: "medium",
      detail:
        "Union conditions may require specialized labor strategy and can limit staffing flexibility.",
    });
    recommendedActions.push(
      "Confirm labor obligations and transition constraints before locking the labor model.",
    );
  }

  if (opportunity.requirements.selfPerformedPreference) {
    score += 6;
    rationale.push("Buyer preference for self-performed delivery aligns with Boss Key's operating thesis.");
  }

  if (opportunity.siteProfile.weekendCoverageRequired) {
    score -= 4;
    assumptions.push("Weekend support is included in the operating model and pricing assumptions.");
  }

  if (opportunity.requirements.referencesRequired >= 3) {
    assumptions.push(
      `At least ${opportunity.requirements.referencesRequired} relevant references will be needed to support proof and de-risk transition.`,
    );
  }

  const finalScore = clampScore(score);
  const highRiskPresent = riskFlags.some((flag) => flag.severity === "high");

  let status: PursuitRecommendation = "review";
  if (
    opportunity.contract.targetGrossMarginPercent < 12 ||
    (!opportunity.geography.inPreferredRegion &&
      opportunity.contract.annualValueEstimate < 250000)
  ) {
    status = "no-bid";
  } else if (finalScore >= 72 && !highRiskPresent) {
    status = "pursue";
  }

  const actionSet =
    recommendedActions.length > 0
      ? recommendedActions
      : ["Confirm buyer priorities and proceed with the current pursuit plan."];

  return {
    score: finalScore,
    status,
    rationale,
    riskFlags,
    recommendedActions: actionSet,
    assumptions,
  };
}

