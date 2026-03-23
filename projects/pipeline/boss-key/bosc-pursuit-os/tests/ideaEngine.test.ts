import demoOpportunityJson from "../inputs/ridgeview-demo-opportunity.json";
import { describe, expect, it } from "vitest";
import { parseOpportunity } from "../src/domain/opportunity";
import { createPursuitDraft } from "../src/domain/operatorWorkspace";
import { buildPursuitIdeaPack } from "../src/engine/ideaPackBuilder";
import { buildOperatorWorkspaceSnapshot } from "../src/engine/operatorWorkspace";

const demoOpportunity = parseOpportunity(demoOpportunityJson);

function buildIdeaPackFor(
  opportunity = demoOpportunity,
  configureDraft?: (draft: ReturnType<typeof createPursuitDraft>) => void,
) {
  const draft = createPursuitDraft(opportunity);

  configureDraft?.(draft);

  const snapshot = buildOperatorWorkspaceSnapshot(draft);

  return {
    snapshot,
    ideaPack: buildPursuitIdeaPack(snapshot),
  };
}

describe("pursuit idea engine", () => {
  it("builds a strategy pack with stronger hot buttons, ghosting angles, and summary variants", () => {
    const { ideaPack } = buildIdeaPackFor();

    expect(ideaPack.strategyMemo.headline).toContain("Ridgeview Property Group");
    expect(ideaPack.strategyMemo.unifyingConcept.length).toBeGreaterThan(5);
    expect(ideaPack.hotButtons.length).toBeGreaterThanOrEqual(4);
    expect(ideaPack.hotButtons.map((item) => item.key)).toEqual(
      expect.arrayContaining([
        "low-disruption-transition",
        "visible-daytime-support",
        "floor-care-recovery",
        "consumables-reliability",
      ]),
    );
    expect(ideaPack.winThemes.length).toBeGreaterThanOrEqual(3);
    expect(ideaPack.winThemes[0].themeStatement).toContain("Ridgeview Property Group");
    expect(ideaPack.winThemes.map((item) => item.title)).toContain(
      "Protect value before talking rate",
    );
    expect(ideaPack.buyerConcerns.length).toBeGreaterThanOrEqual(2);
    expect(ideaPack.competitorGhostAngles.length).toBeGreaterThanOrEqual(2);
    expect(ideaPack.proofMatches.length).toBeGreaterThanOrEqual(3);
    expect(ideaPack.executiveSummaryVariants.length).toBe(3);
    expect(ideaPack.executiveSummaryVariants[0].openingLine).toContain(
      "Ridgeview Property Group",
    );
    expect(ideaPack.validationQuestions.length).toBeGreaterThan(0);
  });

  it("carries current checkpoint context into the idea pack", () => {
    const { snapshot, ideaPack } = buildIdeaPackFor(demoOpportunity, (draft) => {
      draft.approvals[0] = {
        ...draft.approvals[0],
        status: "approved",
        approvedAt: "2026-03-22T20:00:00.000Z",
      };
      draft.operatorActions.push({
        id: "action-1",
        title: "Confirm launch staffing roster",
        owner: "Operations lead",
        dueLabel: "Before solution approval",
        closeCondition: "Named launch supervisors are assigned.",
        stageType: "approval",
        linkedStage: "solution",
        status: "open",
      });
    });

    expect(snapshot.nextCheckpoint.title).toBe("Content Plan Review");
    expect(ideaPack.strategyMemo.priorities).toEqual(
      expect.arrayContaining([
        expect.stringContaining("Content Plan Review"),
      ]),
    );
    expect(ideaPack.validationQuestions).toEqual(
      expect.arrayContaining([
        expect.stringContaining("Confirm launch staffing roster"),
      ]),
    );
  });

  it("matches proof to the strongest janitorial hot buttons", () => {
    const { ideaPack } = buildIdeaPackFor();

    expect(ideaPack.proofMatches[0].hotButton).toMatch(
      /Low-disruption transition|Visible daytime support|Floor care recovery|Self-performed accountability/,
    );
    expect(ideaPack.competitorGhostAngles.map((item) => item.title)).toEqual(
      expect.arrayContaining([
        "Ghost the seamless-start claim",
        "Ghost generic daytime coverage",
      ]),
    );
  });

  it("brings pricing objections into the story when the buyer is rate-sensitive", () => {
    const { ideaPack } = buildIdeaPackFor();

    expect(ideaPack.buyerConcerns.map((item) => item.concern)).toContain(
      "If your price is not the lowest, what am I really buying?",
    );
    expect(
      ideaPack.winThemes.find(
        (item) => item.id === "theme-visible-daytime-support",
      )?.themeStatement,
    ).toContain("named day-porter zones");
  });

  it("suppresses ghosting when the pursuit has no incumbent vulnerability", () => {
    const cleanOpportunity = parseOpportunity({
      ...demoOpportunityJson,
      pursuitContext: {
        ...demoOpportunityJson.pursuitContext,
        incumbentPresent: false,
        notes: [
          "Buyer wants a self-performed delivery team rather than a brokered labor model.",
          "Two sites include executive floors that require visible daytime support.",
        ],
      },
    });
    const { ideaPack } = buildIdeaPackFor(cleanOpportunity);

    expect(ideaPack.competitorGhostAngles).toEqual([]);
  });

  it("keeps executive summary variants distinct while preserving core pursuit facts", () => {
    const { ideaPack } = buildIdeaPackFor();
    const openings = new Set(
      ideaPack.executiveSummaryVariants.map((item) => item.openingLine),
    );

    expect(openings.size).toBe(3);
    expect(ideaPack.executiveSummaryVariants.map((item) => item.title)).toEqual(
      expect.arrayContaining([
        "Switch cleanly, then stabilize",
        "Make the building easier to manage",
        "One accountable operating chain",
      ]),
    );

    ideaPack.executiveSummaryVariants.forEach((variant) => {
      expect(variant.customerDrivers.join(" ")).toContain("4-site");
      expect(variant.customerDrivers.join(" ")).toMatch(/28-day|occupied-hours/);
    });
  });
});
