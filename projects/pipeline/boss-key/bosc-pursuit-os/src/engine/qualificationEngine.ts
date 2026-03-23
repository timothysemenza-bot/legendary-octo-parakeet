import type { Opportunity } from "../domain/opportunity";
import type {
  PursuitRecommendation,
  QualificationResult,
  RiskFlag,
  QualificationScoreBreakdownItem,
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
  const scoreBreakdown: QualificationScoreBreakdownItem[] = [];
  const recommendedActions: string[] = [];
  const assumptions: string[] = [
    "Qualification assumes Boss Key prefers self-performed janitorial and facilities scopes in preferred regional coverage zones.",
  ];

  const strategicFitDelta =
    strategicFitPoints[opportunity.pursuitContext.strategicFit];
  score += strategicFitDelta;
  scoreBreakdown.push({
    code: "strategic-fit",
    label: "Strategic fit",
    points: strategicFitDelta,
    detail: `Buyer and scope alignment is ${opportunity.pursuitContext.strategicFit} against Boss Key's target services profile.`,
  });
  rationale.push(
    `Strategic fit is ${opportunity.pursuitContext.strategicFit}, which shifts the score toward Boss Key's target services profile.`,
  );

  const relationshipDelta =
    relationshipPoints[opportunity.pursuitContext.relationshipStrength];
  score += relationshipDelta;
  scoreBreakdown.push({
    code: "relationship-strength",
    label: "Relationship strength",
    points: relationshipDelta,
    detail: `Relationship strength is ${opportunity.pursuitContext.relationshipStrength}, shaping buyer access and sales-cycle confidence.`,
  });
  rationale.push(
    `Relationship strength is ${opportunity.pursuitContext.relationshipStrength}, affecting sales cycle confidence and buyer access.`,
  );

  const pricingPressureDelta =
    pricingPressurePoints[opportunity.pursuitContext.pricingPressure];
  score += pricingPressureDelta;
  scoreBreakdown.push({
    code: "pricing-pressure",
    label: "Pricing pressure",
    points: pricingPressureDelta,
    detail: `Pricing pressure is ${opportunity.pursuitContext.pricingPressure}, affecting room to defend margin and story-led differentiation.`,
  });
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
    scoreBreakdown.push({
      code: "coverage-region",
      label: "Coverage region",
      points: 12,
      detail: "Opportunity sits inside a preferred operating region.",
    });
    rationale.push("Opportunity sits inside a preferred coverage region.");
  } else {
    score -= 18;
    scoreBreakdown.push({
      code: "coverage-region",
      label: "Coverage region",
      points: -18,
      detail:
        "Opportunity sits outside the preferred operating region and increases staffing complexity.",
    });
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
    scoreBreakdown.push({
      code: "annual-value",
      label: "Annual value",
      points: 10,
      detail: "Annual value is large enough to justify pursuit effort and transition attention.",
    });
    rationale.push("Annual value is large enough to justify pursuit effort.");
  } else if (opportunity.contract.annualValueEstimate < 250000) {
    score -= 10;
    scoreBreakdown.push({
      code: "annual-value",
      label: "Annual value",
      points: -10,
      detail:
        "Contract value is light relative to mobilization effort and executive attention.",
    });
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
    scoreBreakdown.push({
      code: "target-margin",
      label: "Target margin",
      points: 10,
      detail:
        "Margin target supports a differentiated, self-performed operating model.",
    });
    rationale.push("Target margin supports a differentiated, self-performed operating model.");
  } else if (opportunity.contract.targetGrossMarginPercent >= 14) {
    score += 2;
    scoreBreakdown.push({
      code: "target-margin",
      label: "Target margin",
      points: 2,
      detail: "Margin is workable but tight for launch support and visible management control.",
    });
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
    scoreBreakdown.push({
      code: "target-margin",
      label: "Target margin",
      points: -18,
      detail:
        "Margin target is below the floor needed for sustainable service delivery.",
    });
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
    scoreBreakdown.push({
      code: "transition-window",
      label: "Transition window",
      points: -12,
      detail:
        "Transition timing is compressed and increases mobilization risk.",
    });
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
    scoreBreakdown.push({
      code: "transition-window",
      label: "Transition window",
      points: 5,
      detail: "Transition window is long enough for a structured mobilization plan.",
    });
    rationale.push("Transition window is long enough for a structured mobilization plan.");
  }

  if (opportunity.siteProfile.unionEnvironment) {
    score -= 10;
    scoreBreakdown.push({
      code: "union-environment",
      label: "Union environment",
      points: -10,
      detail:
        "Union conditions introduce labor-strategy complexity and can limit staffing flexibility.",
    });
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
    scoreBreakdown.push({
      code: "self-performed-preference",
      label: "Self-performed preference",
      points: 6,
      detail: "Buyer preference for self-performed delivery matches Boss Key's operating thesis.",
    });
    rationale.push("Buyer preference for self-performed delivery aligns with Boss Key's operating thesis.");
  }

  if (opportunity.siteProfile.weekendCoverageRequired) {
    score -= 4;
    scoreBreakdown.push({
      code: "weekend-coverage",
      label: "Weekend coverage",
      points: -4,
      detail: "Weekend support expands staffing coverage assumptions and operating cost.",
    });
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
    recommendedStatus: status,
    status,
    scoreBreakdown,
    rationale,
    riskFlags,
    recommendedActions: actionSet,
    assumptions,
  };
}

