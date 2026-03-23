import demoOpportunityJson from "../inputs/demo-opportunity.json";
import { describe, expect, it } from "vitest";
import { parseOpportunity } from "../src/domain/opportunity";
import { createPursuitDraft } from "../src/domain/operatorWorkspace";
import { buildPursuitIdeaPack } from "../src/engine/ideaPackBuilder";
import { buildOperatorWorkspaceSnapshot } from "../src/engine/operatorWorkspace";
import { buildWorkingStoryBrief } from "../src/engine/workingStoryBuilder";

const demoOpportunity = parseOpportunity(demoOpportunityJson);

function buildIdeaPack() {
  const draft = createPursuitDraft(demoOpportunity);
  const snapshot = buildOperatorWorkspaceSnapshot(draft);

  return {
    draft,
    snapshot,
    ideaPack: buildPursuitIdeaPack(snapshot),
  };
}

describe("working story builder", () => {
  it("defaults to the top-ranked strategy pieces when nothing is pinned", () => {
    const { draft, snapshot, ideaPack } = buildIdeaPack();
    const brief = buildWorkingStoryBrief(snapshot, ideaPack, draft.workingStory);

    expect(brief.summaryVariant.title).toBe(
      ideaPack.executiveSummaryVariants[0].title,
    );
    expect(brief.selectedWinThemes).toHaveLength(3);
    expect(brief.selectedProofMatches).toHaveLength(3);
    expect(brief.briefText).toContain(brief.summaryVariant.openingLine);
  });

  it("respects pinned summary, themes, proof, ghosting, and transition selections", () => {
    const { snapshot, ideaPack } = buildIdeaPack();
    const brief = buildWorkingStoryBrief(snapshot, ideaPack, {
      summaryVariantId: ideaPack.executiveSummaryVariants[1].id,
      winThemeIds: [ideaPack.winThemes[1].id, ideaPack.winThemes[2].id],
      proofIds: [ideaPack.proofMatches[1].id],
      ghostAngleIds: [ideaPack.competitorGhostAngles[0]?.id ?? ""].filter(Boolean),
      transitionAngleId: ideaPack.transitionAngles[1]?.id ?? null,
      operatorNotes: "Lead with the executive-floor angle.",
    });

    expect(brief.summaryVariant.title).toBe(
      ideaPack.executiveSummaryVariants[1].title,
    );
    expect(brief.selectedWinThemes.map((item) => item.id)).toEqual([
      ideaPack.winThemes[1].id,
      ideaPack.winThemes[2].id,
    ]);
    expect(brief.selectedProofMatches.map((item) => item.id)).toEqual([
      ideaPack.proofMatches[1].id,
    ]);
    expect(brief.selectedTransitionAngle?.id).toBe(
      ideaPack.transitionAngles[1]?.id,
    );
    expect(brief.briefText).toContain("Lead with the executive-floor angle.");
  });

  it("falls back to current top picks when stored refs no longer match", () => {
    const { snapshot, ideaPack } = buildIdeaPack();
    const brief = buildWorkingStoryBrief(snapshot, ideaPack, {
      summaryVariantId: "Missing summary",
      winThemeIds: ["Missing theme"],
      proofIds: ["Missing proof"],
      ghostAngleIds: ["Missing ghost angle"],
      transitionAngleId: "Missing transition",
      operatorNotes: "",
    });

    expect(brief.summaryVariant.title).toBe(
      ideaPack.executiveSummaryVariants[0].title,
    );
    expect(brief.selectedWinThemes[0].id).toBe(ideaPack.winThemes[0].id);
    expect(brief.selectedProofMatches[0].id).toBe(
      ideaPack.proofMatches[0].id,
    );
    expect(brief.briefText).toContain(snapshot.nextCheckpoint.title);
  });
});
