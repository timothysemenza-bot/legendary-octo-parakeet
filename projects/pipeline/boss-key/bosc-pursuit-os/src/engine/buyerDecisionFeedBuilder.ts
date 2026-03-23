import type { BuyerDecisionFeed } from "../domain/buyerDecisionFeed";
import type { ProposalExperience } from "../domain/proposalExperience";
import type { WorkingStoryBrief } from "../domain/workingStory";

function compactTags(values: string[], count: number): string[] {
  return Array.from(new Set(values.filter(Boolean))).slice(0, count);
}

export function buildBuyerDecisionFeed(
  experience: ProposalExperience,
  workingStoryBrief: WorkingStoryBrief | null,
): BuyerDecisionFeed {
  const topTheme = workingStoryBrief?.selectedWinThemes[0] ?? null;
  const selectedProof = workingStoryBrief?.selectedProofMatches[0] ?? null;
  const topProofExample = experience.proofExamples[0] ?? null;
  const topGhostAngle = workingStoryBrief?.selectedGhostAngles[0] ?? null;
  const topTransition =
    workingStoryBrief?.selectedTransitionAngle ?? null;
  const firstMilestone = experience.transitionApproach.milestones[0] ?? null;
  const coreTags = compactTags(
    [
      `${experience.opportunity.siteProfile.siteCount} sites`,
      `${experience.opportunity.contract.transitionDays}-day launch window`,
      ...experience.scopeSummary.serviceLines,
    ],
    4,
  );
  const themeTags = compactTags(
    [
      ...(topTheme ? [topTheme.title] : []),
      ...experience.differentiators.slice(0, 2),
    ],
    3,
  );

  return {
    headline:
      workingStoryBrief?.summaryVariant.openingLine ??
      experience.overview.headline,
    subhead:
      workingStoryBrief?.summaryVariant.solutionFrame ??
      experience.overview.summary,
    cards: [
      {
        id: "decision-signal",
        kicker: "Why this matters",
        headline: `${experience.opportunity.siteProfile.siteCount} occupied sites need visible service control`,
        body: `${experience.opportunity.buyerName} is not just buying cleaning coverage. The decision is about how fast service noise, tenant friction, and launch risk get reduced across the portfolio.`,
        tags: compactTags(
          [
            `${experience.opportunity.siteProfile.occupiedHours} occupied-hours pattern`,
            ...coreTags,
          ],
          4,
        ),
        tone: "signal",
      },
      {
        id: "operating-answer",
        kicker: "What Boss Key is offering",
        headline:
          topTheme?.title ?? "A controlled janitorial operating model",
        body:
          topTheme?.themeStatement ?? experience.scopeSummary.operatingModel,
        proof: topTheme?.proofPoint,
        tags: themeTags,
        tone: "plan",
      },
      {
        id: "proof-anchor",
        kicker: "Why believe it",
        headline:
          selectedProof?.metric ??
          topProofExample?.metric ??
          "Credible operating proof is available",
        body:
          selectedProof
            ? `${selectedProof.whyItFits} ${selectedProof.strength}`
            : topProofExample?.description ??
          "The operating story is backed by recent proof tied to the delivery model, not generic testimonial language.",
        proof: selectedProof?.title ?? topProofExample?.title,
        tags: compactTags(
          [
            selectedProof?.hotButton ?? "",
            selectedProof?.whereToUse ?? "",
            ...(topProofExample?.bestUse ?? []),
          ],
          3,
        ),
        tone: "proof",
      },
      {
        id: "launch-pace",
        kicker: "What the first month looks like",
        headline:
          topTransition?.title ??
          experience.transitionApproach.title,
        body: firstMilestone
          ? `${experience.transitionApproach.summary} The first visible move is ${firstMilestone.phase.toLowerCase()} with ${firstMilestone.detail.toLowerCase()}.`
          : experience.transitionApproach.summary,
        proof: firstMilestone?.timing,
        tags: compactTags(
          [
            ...(topTransition?.moves.slice(0, 2) ?? []),
            `${experience.opportunity.contract.transitionDays}-day transition`,
          ],
          3,
        ),
        tone: "plan",
      },
      {
        id: "contrast",
        kicker: "Why this feels different",
        headline:
          topGhostAngle?.title ??
          "Visible control beats generic janitorial promises",
        body: topGhostAngle
          ? `${topGhostAngle.ghostStatement} Boss Key answers that risk with ${topGhostAngle.bossKeyCounter.toLowerCase()}.`
          : `${experience.differentiators[0]} ${experience.differentiators[1] ?? ""}`.trim(),
        proof: topGhostAngle?.proofToUse,
        tags: compactTags(
          [
            ...experience.differentiators.slice(0, 2),
            ...(workingStoryBrief?.selectedWinThemes.slice(0, 2).map((theme) => theme.title) ?? []),
          ],
          4,
        ),
        tone: "contrast",
      },
      {
        id: "decision-test",
        kicker: "How to judge the decision",
        headline: "Choose the operator that reduces service noise fastest",
        body: `A modern buyer should be able to see who owns launch, how visible spaces stay inspection-ready, and what proof supports the claim before the proposal ever becomes a PDF.`,
        tags: compactTags(
          [
            `Score ${experience.qualification.score}/100`,
            experience.overview.recommendation,
            "Buyer-visible reporting",
          ],
          3,
        ),
        tone: "confidence",
      },
    ],
  };
}
