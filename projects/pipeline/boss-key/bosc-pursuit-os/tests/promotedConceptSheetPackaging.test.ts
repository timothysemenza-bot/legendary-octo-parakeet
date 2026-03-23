import demoWorkspaceStateJson from "../inputs/ridgeview-demo-workspace-state.json";
import { describe, expect, it } from "vitest";
import { operatorWorkspaceStateSchema } from "../src/domain/operatorWorkspace";
import {
  buildPackagedPromotedConceptSheet,
  renderShareableConceptSheetHtml,
  renderWorkingStoryBriefMarkdown,
} from "../src/deliverables/promotedConceptSheetPackaging";

const demoWorkspaceState = operatorWorkspaceStateSchema.parse(
  demoWorkspaceStateJson,
);

describe("promoted concept sheet packaging", () => {
  it("builds a packaged concept sheet from the promoted buyer story variant", () => {
    const packagedConceptSheet = buildPackagedPromotedConceptSheet(
      demoWorkspaceState,
      "2026-03-23T15:00:00.000Z",
    );

    expect(packagedConceptSheet.promotedVariant.name).toBe("Visible control launch");
    expect(packagedConceptSheet.conceptSheet.name).toBe("Visible control launch");
    expect(packagedConceptSheet.conceptSheet.decisionFeed.length).toBeGreaterThanOrEqual(4);
    expect(packagedConceptSheet.bundleSlug).toBe("ridgeview-property-group-concept-sheet");
  });

  it("renders a shareable HTML concept sheet with escaped content", () => {
    const stateWithUnsafeName = structuredClone(demoWorkspaceState);
    stateWithUnsafeName.activeDraft.buyerStoryVariants[0] = {
      ...stateWithUnsafeName.activeDraft.buyerStoryVariants[0],
      name: `Visible <control> & launch`,
    };

    const packagedConceptSheet = buildPackagedPromotedConceptSheet(
      stateWithUnsafeName,
      "2026-03-23T15:00:00.000Z",
    );
    const html = renderShareableConceptSheetHtml(packagedConceptSheet);

    expect(html).toContain("Visible &lt;control&gt; &amp; launch");
    expect(html).toContain("Boss Key concept sheet");
    expect(html).toContain("What Ridgeview Property Group Should Believe Fast");
    expect(html).not.toContain("Visible <control> & launch");
  });

  it("renders the internal working story brief as markdown text", () => {
    const packagedConceptSheet = buildPackagedPromotedConceptSheet(
      demoWorkspaceState,
      "2026-03-23T15:00:00.000Z",
    );
    const markdown = renderWorkingStoryBriefMarkdown(packagedConceptSheet);

    expect(markdown).toContain("# Working Story");
    expect(markdown).toContain("## Pursuit posture");
    expect(markdown).toContain("## Before");
  });
});
