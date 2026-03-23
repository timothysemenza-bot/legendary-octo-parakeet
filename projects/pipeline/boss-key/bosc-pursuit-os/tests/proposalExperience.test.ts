import demoOpportunityJson from "../inputs/ridgeview-demo-opportunity.json";
import { describe, expect, it } from "vitest";
import { parseOpportunity } from "../src/domain/opportunity";
import { buildProposalExperience } from "../src/engine/proposalComposer";

const demoOpportunity = parseOpportunity(demoOpportunityJson);

describe("proposal experience narrative", () => {
  it("builds a 2026-style brief and decision feed without exposing internal qualification language in the buyer framing", () => {
    const experience = buildProposalExperience(demoOpportunity);

    expect(experience.brief90.title).toBe("90-second brief");
    expect(experience.brief90.signalChips).toEqual(
      expect.arrayContaining(["4 sites", "28-day transition"]),
    );
    expect(experience.decisionFeed.map((card) => card.id)).toEqual(
      expect.arrayContaining([
        "buyer-friction",
        "operating-chain",
        "launch-sequence",
        "proof-stack",
      ]),
    );
    expect(experience.overview.buyerFraming).not.toContain("Advance");
    expect(experience.overview.summary).not.toContain("/100");
    expect(experience.overview.recommendation).toMatch(
      /Advance|Do not advance/,
    );
  });
});
