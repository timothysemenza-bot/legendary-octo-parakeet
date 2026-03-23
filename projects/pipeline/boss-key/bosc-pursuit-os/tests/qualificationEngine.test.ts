import demoOpportunityJson from "../inputs/ridgeview-demo-opportunity.json";
import { describe, expect, it } from "vitest";
import {
  applyQualificationDecision,
} from "../src/domain/qualification";
import { parseOpportunity } from "../src/domain/opportunity";
import { qualifyOpportunity } from "../src/engine/qualificationEngine";

const demoOpportunity = parseOpportunity(demoOpportunityJson);

describe("qualifyOpportunity", () => {
  it("recommends pursue for the seeded demo opportunity", () => {
    const result = qualifyOpportunity(demoOpportunity);

    expect(result.recommendedStatus).toBe("pursue");
    expect(result.status).toBe("pursue");
    expect(result.score).toBeGreaterThanOrEqual(72);
    expect(result.scoreBreakdown).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          code: "strategic-fit",
          label: "Strategic fit",
        }),
      ]),
    );
    expect(result.recommendedActions.length).toBeGreaterThan(0);
  });

  it("returns no-bid when the margin floor fails outside preferred coverage", () => {
    const opportunity = structuredClone(demoOpportunity);
    opportunity.geography.inPreferredRegion = false;
    opportunity.contract.annualValueEstimate = 180000;
    opportunity.contract.targetGrossMarginPercent = 11;

    const result = qualifyOpportunity(opportunity);

    expect(result.recommendedStatus).toBe("no-bid");
    expect(result.status).toBe("no-bid");
    expect(result.riskFlags.map((flag) => flag.code)).toContain("margin-floor");
    expect(result.riskFlags.map((flag) => flag.code)).toContain("coverage-region");
  });

  it("applies an operator override without erasing the engine recommendation", () => {
    const engineResult = qualifyOpportunity(demoOpportunity);

    const overridden = applyQualificationDecision(engineResult, {
      mode: "override",
      selectedStatus: "no-bid",
      note: "Hold until the commercial model is reset.",
      decidedAt: "2026-03-23T16:00:00.000Z",
    });

    expect(overridden.recommendedStatus).toBe(engineResult.recommendedStatus);
    expect(overridden.status).toBe("no-bid");
    expect(overridden.score).toBe(engineResult.score);
  });
});
