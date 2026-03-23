import demoOpportunityJson from "../inputs/ridgeview-demo-opportunity.json";
import { describe, expect, it } from "vitest";
import { parseOpportunity } from "../src/domain/opportunity";
import { qualifyOpportunity } from "../src/engine/qualificationEngine";

const demoOpportunity = parseOpportunity(demoOpportunityJson);

describe("qualifyOpportunity", () => {
  it("recommends pursue for the seeded demo opportunity", () => {
    const result = qualifyOpportunity(demoOpportunity);

    expect(result.status).toBe("pursue");
    expect(result.score).toBeGreaterThanOrEqual(72);
    expect(result.recommendedActions.length).toBeGreaterThan(0);
  });

  it("returns no-bid when the margin floor fails outside preferred coverage", () => {
    const opportunity = structuredClone(demoOpportunity);
    opportunity.geography.inPreferredRegion = false;
    opportunity.contract.annualValueEstimate = 180000;
    opportunity.contract.targetGrossMarginPercent = 11;

    const result = qualifyOpportunity(opportunity);

    expect(result.status).toBe("no-bid");
    expect(result.riskFlags.map((flag) => flag.code)).toContain("margin-floor");
    expect(result.riskFlags.map((flag) => flag.code)).toContain("coverage-region");
  });
});
