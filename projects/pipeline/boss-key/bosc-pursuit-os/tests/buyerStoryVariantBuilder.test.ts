import demoOpportunityJson from "../inputs/ridgeview-demo-opportunity.json";
import { describe, expect, it } from "vitest";
import { parseOpportunity } from "../src/domain/opportunity";
import { createPursuitDraft, type BuyerStoryVariant } from "../src/domain/operatorWorkspace";
import { buildPursuitIdeaPack } from "../src/engine/ideaPackBuilder";
import { buildOperatorWorkspaceSnapshot } from "../src/engine/operatorWorkspace";
import { buildBuyerStoryConceptSheet } from "../src/engine/buyerStoryVariantBuilder";
import { buildWorkingStoryBrief } from "../src/engine/workingStoryBuilder";

const demoOpportunity = parseOpportunity(demoOpportunityJson);

describe("buyer story concept sheet builder", () => {
  it("builds a named concept sheet from a saved buyer story selection", () => {
    const draft = createPursuitDraft(demoOpportunity);
    const snapshot = buildOperatorWorkspaceSnapshot(draft);
    const ideaPack = buildPursuitIdeaPack(snapshot);
    const variant: BuyerStoryVariant = {
      id: "variant-1",
      name: "Executive confidence concept",
      savedAt: "2026-03-23T14:00:00.000Z",
      selection: {
        summaryVariantId: ideaPack.executiveSummaryVariants[1].id,
        winThemeIds: [ideaPack.winThemes[0].id, ideaPack.winThemes[1].id],
        proofIds: [ideaPack.proofMatches[0].id],
        ghostAngleIds: [ideaPack.competitorGhostAngles[0]?.id ?? ""].filter(Boolean),
        transitionAngleId: ideaPack.transitionAngles[0]?.id ?? null,
        operatorNotes: "Keep the building-experience story compact.",
      },
    };

    const brief = buildWorkingStoryBrief(snapshot, ideaPack, variant.selection);
    const conceptSheet = buildBuyerStoryConceptSheet(snapshot, variant, brief);

    expect(conceptSheet.name).toBe("Executive confidence concept");
    expect(conceptSheet.brief90.signalChips).toContain("4 sites");
    expect(conceptSheet.brief90.summary).toContain("Expect");
    expect(conceptSheet.brief90.decisionPoints.join(" ")).not.toContain(
      "Advance only when",
    );
    expect(conceptSheet.decisionFeed[0].headline).toBe(brief.summaryVariant.title);
    expect(conceptSheet.themeTitles).toEqual(
      expect.arrayContaining([brief.selectedWinThemes[0].title]),
    );
    expect(conceptSheet.memoText).toContain("Operator notes");
  });
});
