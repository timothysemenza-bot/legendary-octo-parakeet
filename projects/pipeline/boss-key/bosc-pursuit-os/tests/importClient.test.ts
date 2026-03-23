import eastBayOpportunityJson from "../inputs/east-bay-library-opportunity.json";
import { afterEach, describe, expect, it, vi } from "vitest";
import { parseOpportunity } from "../src/domain/opportunity";
import {
  composeImportMessage,
  importOpportunityForApp,
} from "../src/services/importClient";

const eastBaySourceText = `
Traverse Area District Library
Custodial Services at East Bay Branch
1989 Three Mile Road in Traverse City, MI 49686.
Services must be performed Monday and Thursday while the library is closed.
estimated square footage: 1,200
3 to 5 References
Competitive fees
24/7 emergency response
paper products, hand soap, hand sanitizer, and trash liners
`;
const eastBayOpportunity = parseOpportunity(eastBayOpportunityJson);

describe("import client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("formats import notices from server import results", () => {
    const message = composeImportMessage({
      opportunity: eastBayOpportunity,
      extractionMethod: "model",
      summary: "Built a model-based opportunity draft from 1 source file.",
      warnings: ["Review estimated annual value before kickoff."],
      assumptions: [],
      evidence: [],
    });

    expect(message).toContain("Built a model-based opportunity draft");
    expect(message).toContain("estimated annual value");
  });

  it("uses the model-backed import API when it is available", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          opportunity: eastBayOpportunity,
          extractionMethod: "model",
          summary: "Built a model-based opportunity draft from 1 source file.",
          warnings: ["Review estimated annual value before kickoff."],
          assumptions: ["Estimated annual value from source scope."],
          evidence: [],
        }),
        {
          status: 200,
          headers: {
            "Content-Type": "application/json",
          },
        },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    const payload = await importOpportunityForApp([
      new File([eastBaySourceText], "east-bay-rfp.txt", {
        type: "text/plain",
      }),
    ]);

    expect(fetchMock).toHaveBeenCalledOnce();
    expect(payload.kind).toBe("opportunity");
    if (payload.kind === "opportunity") {
      expect(payload.opportunity.buyerName).toBe("Traverse Area District Library");
      expect(payload.importResult.extractionMethod).toBe("model");
      expect(payload.message).toContain("model-based opportunity draft");
    }
  });

  it("falls back to the local importer when the API route is unavailable", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ error: "Not found" }), {
        status: 404,
        headers: {
          "Content-Type": "application/json",
        },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const payload = await importOpportunityForApp([
      new File([eastBaySourceText], "east-bay-rfp.txt", {
        type: "text/plain",
      }),
    ]);

    expect(payload.kind).toBe("opportunity");
    if (payload.kind === "opportunity") {
      expect(payload.opportunity.opportunityName).toContain("East Bay Branch");
      expect(payload.importResult.extractionMethod).toBe("heuristic");
      expect(payload.message).toContain("local heuristic importer");
    }
  });
});
