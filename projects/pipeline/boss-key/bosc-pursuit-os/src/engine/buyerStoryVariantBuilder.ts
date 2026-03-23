import type { BuyerStoryVariant, OperatorWorkspaceSnapshot } from "../domain/operatorWorkspace";
import type { BuyerStoryConceptSheet, WorkingStoryBrief } from "../domain/workingStory";
import type { WinTheme } from "../domain/pursuitIdeaPack";

function isPublicSectorLike(snapshot: OperatorWorkspaceSnapshot): boolean {
  const opportunity = snapshot.experience.opportunity;
  const signals = [
    opportunity.buyerName,
    opportunity.sector,
    ...opportunity.pursuitContext.notes,
  ]
    .join(" ")
    .toLowerCase();

  return /county|city|district|school|library|department|sheriff|authority|public|station|security|background/.test(
    signals,
  );
}

function buildSignalChips(
  snapshot: OperatorWorkspaceSnapshot,
  brief: WorkingStoryBrief,
): string[] {
  return [
    `${snapshot.experience.opportunity.siteProfile.siteCount} sites`,
    `${snapshot.experience.opportunity.contract.transitionDays}-day transition`,
    brief.selectedWinThemes[0]?.title ?? "Structured service control",
    brief.selectedProofMatches[0]?.metric ?? "Proof-backed operating model",
  ];
}

function summarizeWinTheme(
  snapshot: OperatorWorkspaceSnapshot,
  theme: WinTheme,
): string {
  const publicSectorLike = isPublicSectorLike(snapshot);

  switch (theme.id) {
    case "theme-visible-daytime-support":
      return publicSectorLike
        ? "public-facing and secured areas that stay reset during the day"
        : "occupied spaces that stay reset and stocked during the day";
    case "theme-low-disruption-transition":
      return "a first month that feels controlled instead of noisy";
    case "theme-operating-value-under-price-pressure":
      return publicSectorLike
        ? "a rate story built on fewer callbacks and less supervisory chase"
        : "a rate story built on fewer callbacks and less management chase";
    case "theme-floor-care-recovery":
      return "visible floor recovery the buyer can see quickly";
    case "theme-self-performed-accountability":
      return "one accountable chain behind staffing, supervision, and fixes";
    case "theme-consumables-reliability":
      return publicSectorLike
        ? "stocked restrooms and public areas without buyer follow-up"
        : "stocked restrooms and breakrooms without buyer follow-up";
    default:
      return theme.title.toLowerCase();
  }
}

function joinOutcomePhrases(phrases: string[]): string {
  if (phrases.length === 0) {
    return "visible control the buyer can feel quickly";
  }

  if (phrases.length === 1) {
    return phrases[0];
  }

  if (phrases.length === 2) {
    return `${phrases[0]} and ${phrases[1]}`;
  }

  return `${phrases.slice(0, -1).join(", ")}, and ${phrases.at(-1)}`;
}

function buildBriefSummary(
  snapshot: OperatorWorkspaceSnapshot,
  brief: WorkingStoryBrief,
): string {
  const outcomes = brief.selectedWinThemes
    .slice(0, 3)
    .map((theme) => summarizeWinTheme(snapshot, theme));
  const proof = brief.selectedProofMatches[0];
  const proofClause = proof
    ? `, backed by ${proof.metric.toLowerCase()}`
    : "";

  return `Expect ${joinOutcomePhrases(outcomes)}${proofClause}.`;
}

function buildDecisionPoints(
  brief: WorkingStoryBrief,
  snapshot: OperatorWorkspaceSnapshot,
): string[] {
  const buyerName = snapshot.experience.opportunity.buyerName;
  const primaryConcern =
    brief.priorityObjections.find((objection) =>
      /price|lowest|rate/i.test(objection.concern),
    ) ?? brief.priorityObjections[0];
  const points = [
    brief.summaryVariant.openingLine,
    `What ${buyerName} should notice first: ${brief.selectedWinThemes[0] ? summarizeWinTheme(snapshot, brief.selectedWinThemes[0]) : "visible service outcomes the buyer can feel quickly"}.`,
    `First-month control: ${brief.selectedTransitionAngle?.moves[0] ?? snapshot.experience.transitionApproach.milestones[0]?.detail ?? "Show how the first month stays controlled from day one."}`,
    primaryConcern
      ? `Why the rate holds: ${primaryConcern.counterMessage}`
      : "Why the offer holds: operating control stays visible from day one.",
    brief.selectedProofMatches[0]
      ? `Proof to repeat: ${brief.selectedProofMatches[0].title} - ${brief.selectedProofMatches[0].metric}.`
      : "Proof to repeat: measurable operating proof.",
  ];

  return points.slice(0, 5);
}

export function buildBuyerStoryConceptSheet(
  snapshot: OperatorWorkspaceSnapshot,
  variant: BuyerStoryVariant,
  brief: WorkingStoryBrief,
): BuyerStoryConceptSheet {
  const publicSectorLike = isPublicSectorLike(snapshot);
  const decisionFeed = [
    {
      id: `${variant.id}-opening`,
      label: "Story direction",
      headline: brief.summaryVariant.title,
      summary: brief.summaryVariant.openingLine,
      bullets: [
        ...brief.summaryVariant.customerDrivers.slice(0, 3),
        brief.summaryVariant.solutionFrame,
      ].slice(0, 4),
      proof: brief.summaryVariant.proofThread,
      tone: "signal" as const,
    },
    {
      id: `${variant.id}-themes`,
      label: "What the buyer gets",
      headline:
        brief.selectedWinThemes[0]?.title ?? "Service control with visible buyer value",
      summary:
        publicSectorLike
          ? "Lead with the day-to-day outcomes the buyer team should feel quickly: steadier public-facing areas, fewer visible misses, and clearer ownership when something slips."
          : "Lead with the day-to-day outcomes the buyer should feel quickly: less chasing, fewer visible misses, and clearer ownership when something slips.",
      bullets: brief.selectedWinThemes.map((theme) => theme.themeStatement).slice(0, 3),
      tone: "confidence" as const,
    },
    {
      id: `${variant.id}-proof`,
      label: "Proof that travels",
      headline: "Proof a buyer can repeat",
      summary:
        "The strongest concept sheet keeps proof portable enough for a skim, a meeting, or a forwarded screenshot.",
      bullets: brief.selectedProofMatches.map(
        (proof) => `${proof.title}: ${proof.metric}`,
      ).slice(0, 3),
      proof: brief.selectedProofMatches[0]
        ? `${brief.selectedProofMatches[0].title}: ${brief.selectedProofMatches[0].metric}`
        : undefined,
      tone: "proof" as const,
    },
    {
      id: `${variant.id}-transition`,
      label: "What changes first",
      headline:
        brief.selectedTransitionAngle?.title ?? "Controlled transition and first-month clarity",
      summary:
        brief.selectedTransitionAngle?.bestFit ??
        snapshot.experience.transitionApproach.summary,
      bullets:
        brief.selectedTransitionAngle?.moves.slice(0, 3) ??
        snapshot.experience.transitionApproach.milestones
          .slice(0, 3)
          .map((milestone) => `${milestone.phase}: ${milestone.detail}`),
      tone: "transition" as const,
    },
  ];

  if (brief.selectedGhostAngles.length > 0 || brief.priorityObjections.length > 0) {
    decisionFeed.push({
      id: `${variant.id}-contrast`,
      label: "Why this wins",
      headline: brief.priorityObjections[0]?.concern ?? "Answer the doubt before it turns into inertia",
      summary:
        "The contrast is simple: Boss Key shows who owns the work, how misses surface, and why the rate is safer than it first appears.",
      bullets: [
        ...brief.selectedGhostAngles.map((angle) => angle.ghostStatement),
        ...brief.priorityObjections.map((objection) => objection.counterMessage),
      ].slice(0, 3),
      tone: "confidence" as const,
    });
  }

  return {
    variantId: variant.id,
    name: variant.name,
    savedAt: variant.savedAt,
    brief90: {
      title: variant.name,
      summary: buildBriefSummary(snapshot, brief),
      signalChips: buildSignalChips(snapshot, brief),
      decisionPoints: buildDecisionPoints(brief, snapshot),
    },
    decisionFeed,
    themeTitles: brief.selectedWinThemes.map((theme) => theme.title),
    proofTitles: brief.selectedProofMatches.map((proof) => proof.title),
    memoText: brief.briefText,
  };
}
