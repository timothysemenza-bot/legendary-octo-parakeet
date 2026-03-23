import demoOpportunityJson from "../inputs/ridgeview-demo-opportunity.json";
import { describe, expect, it } from "vitest";
import { parseOpportunity } from "../src/domain/opportunity";
import { assembleSolution } from "../src/engine/solutionAssembler";

const demoOpportunity = parseOpportunity(demoOpportunityJson);

describe("assembleSolution", () => {
  it("selects the expected modules for the demo janitorial portfolio", () => {
    const result = assembleSolution(demoOpportunity);
    const moduleIds = result.modules.map((module) => module.id);

    expect(moduleIds).toEqual(
      expect.arrayContaining([
        "core-recurring-service",
        "mobilization-cell",
        "qa-reporting",
        "day-porter-coverage",
        "floor-specialty",
        "consumables-control",
        "sustainability-ops",
      ]),
    );
    expect(result.staffing.dayPorterFte).toBeGreaterThan(0);
    expect(result.proofExamples.length).toBeGreaterThan(0);
    expect(result.proofExamples[0].buyerHotButtons.length).toBeGreaterThan(0);
    expect(result.proofExamples[0].bestUse.length).toBeGreaterThan(0);
  });

  it("omits optional modules when the opportunity does not call for them", () => {
    const opportunity = structuredClone(demoOpportunity);
    opportunity.siteProfile.dayPorterRequired = false;
    opportunity.requirements.requiredServices = ["nightly-cleaning"];
    opportunity.requirements.sustainabilityExpectation = false;

    const result = assembleSolution(opportunity);
    const moduleIds = result.modules.map((module) => module.id);

    expect(moduleIds).not.toContain("day-porter-coverage");
    expect(moduleIds).not.toContain("floor-specialty");
    expect(moduleIds).not.toContain("consumables-control");
    expect(moduleIds).not.toContain("sustainability-ops");
    expect(result.staffing.dayPorterFte).toBe(0);
  });

  it("prioritizes proof aligned to the active janitorial hot buttons", () => {
    const result = assembleSolution(demoOpportunity);
    const proofTitles = result.proofExamples.map((item) => item.title);

    expect(proofTitles).toEqual(
      expect.arrayContaining([
        "Corporate campus mobilization",
        "Budget rebaseline without visible slippage",
        "Executive-floor response program",
        "Floor care recovery sprint",
      ]),
    );
  });
});
