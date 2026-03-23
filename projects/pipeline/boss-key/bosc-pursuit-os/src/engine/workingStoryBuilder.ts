import type {
  OperatorWorkspaceSnapshot,
  WorkingStorySelection,
} from "../domain/operatorWorkspace";
import type {
  BuyerConcernResponse,
  CompetitorGhostAngle,
  ExecutiveSummaryVariant,
  ProofMatch,
  PursuitIdeaPack,
  TransitionAngle,
  WinTheme,
} from "../domain/pursuitIdeaPack";
import type { WorkingStoryBrief } from "../domain/workingStory";

function matchesRef(item: { id: string; title: string }, ref: string | null): boolean {
  return ref !== null && (item.id === ref || item.title === ref);
}

function pickSingleByRef<T extends { id: string; title: string }>(
  items: T[],
  selectedRef: string | null,
): T {
  return items.find((item) => matchesRef(item, selectedRef)) ?? items[0];
}

function resolveSelections<T extends { id: string; title: string }>(
  items: T[],
  selectedRefs: string[],
  fallbackCount: number,
): T[] {
  const selected = selectedRefs
    .map((ref) => items.find((item) => matchesRef(item, ref)))
    .filter((item): item is T => Boolean(item));

  if (selected.length > 0) {
    return selected.slice(0, Math.min(fallbackCount, selected.length));
  }

  return items.slice(0, Math.min(fallbackCount, items.length));
}

function pickPriorityObjections(
  buyerConcerns: BuyerConcernResponse[],
  selectedProofMatches: ProofMatch[],
): BuyerConcernResponse[] {
  const selectedProofTitles = selectedProofMatches.map((proof) =>
    proof.title.toLowerCase(),
  );
  const matched = buyerConcerns.filter((concern) =>
    selectedProofTitles.some((title) =>
      concern.proofToUse.toLowerCase().includes(title),
    ),
  );

  return (matched.length > 0 ? matched : buyerConcerns).slice(0, 2);
}

function buildBriefText(
  snapshot: OperatorWorkspaceSnapshot,
  ideaPack: PursuitIdeaPack,
  summaryVariant: ExecutiveSummaryVariant,
  selectedWinThemes: WinTheme[],
  selectedProofMatches: ProofMatch[],
  selectedGhostAngles: CompetitorGhostAngle[],
  selectedTransitionAngle: TransitionAngle | null,
  priorityObjections: BuyerConcernResponse[],
  operatorNotes: string,
): string {
  const lines: string[] = [
    `# Working Story`,
    "",
    `## Pursuit posture`,
    `- Buyer: ${snapshot.experience.opportunity.buyerName}`,
    `- Opportunity: ${snapshot.experience.opportunity.opportunityName}`,
    `- Pursuit call: ${ideaPack.strategyMemo.pursuitCall}`,
    `- Unifying concept: ${ideaPack.strategyMemo.unifyingConcept}`,
    `- Next checkpoint: ${snapshot.nextCheckpoint.title}`,
    "",
    `## Opening angle`,
    summaryVariant.openingLine,
    "",
    `- Drivers: ${summaryVariant.customerDrivers.join("; ")}`,
    `- Solution frame: ${summaryVariant.solutionFrame}`,
    `- Proof thread: ${summaryVariant.proofThread}`,
    `- Close: ${summaryVariant.close}`,
    "",
    `## Reinforce these themes`,
    ...selectedWinThemes.map(
      (theme) =>
        `- ${theme.title}: ${theme.themeStatement} Proof: ${theme.proofPoint}.`,
    ),
    "",
    `## Carry this proof`,
    ...selectedProofMatches.map(
      (proof) =>
        `- ${proof.title}: ${proof.metric}. ${proof.whyItFits} Use: ${proof.whereToUse}.`,
    ),
  ];

  if (selectedGhostAngles.length > 0) {
    lines.push("", `## Ghost carefully`);
    lines.push(
      ...selectedGhostAngles.map(
        (angle) =>
          `- ${angle.title}: ${angle.ghostStatement} Counter with ${angle.bossKeyCounter} Proof: ${angle.proofToUse}.`,
      ),
    );
  }

  if (selectedTransitionAngle) {
    lines.push("", `## Transition emphasis`);
    lines.push(`- ${selectedTransitionAngle.title}: ${selectedTransitionAngle.bestFit}`);
    lines.push(...selectedTransitionAngle.moves.map((move) => `- ${move}`));
  }

  if (priorityObjections.length > 0) {
    lines.push("", `## Answer if challenged`);
    lines.push(
      ...priorityObjections.map(
        (concern) =>
          `- ${concern.concern}: ${concern.counterMessage} Proof: ${concern.proofToUse}.`,
      ),
    );
  }

  lines.push("", `## Before ${snapshot.nextCheckpoint.title}`);
  lines.push(
    ...ideaPack.validationQuestions
      .slice(0, 3)
      .map((question) => `- ${question}`),
  );

  if (operatorNotes.trim()) {
    lines.push("", `## Operator notes`, operatorNotes.trim());
  }

  return lines.join("\n");
}

export function buildWorkingStoryBrief(
  snapshot: OperatorWorkspaceSnapshot,
  ideaPack: PursuitIdeaPack,
  selection: WorkingStorySelection,
): WorkingStoryBrief {
  const summaryVariant = pickSingleByRef(
    ideaPack.executiveSummaryVariants,
    selection.summaryVariantId,
  );
  const selectedWinThemes = resolveSelections(
    ideaPack.winThemes,
    selection.winThemeIds,
    3,
  );
  const selectedProofMatches = resolveSelections(
    ideaPack.proofMatches,
    selection.proofIds,
    3,
  );
  const selectedGhostAngles = resolveSelections(
    ideaPack.competitorGhostAngles,
    selection.ghostAngleIds,
    2,
  );
  const selectedTransitionAngle =
    ideaPack.transitionAngles.length > 0
      ? pickSingleByRef(
          ideaPack.transitionAngles,
          selection.transitionAngleId,
        )
      : null;
  const priorityObjections = pickPriorityObjections(
    ideaPack.buyerConcerns,
    selectedProofMatches,
  );
  const headline = `${snapshot.experience.opportunity.buyerName} working story`;

  return {
    headline,
    summaryVariant,
    selectedWinThemes,
    selectedProofMatches,
    selectedGhostAngles,
    selectedTransitionAngle,
    priorityObjections,
    briefText: buildBriefText(
      snapshot,
      ideaPack,
      summaryVariant,
      selectedWinThemes,
      selectedProofMatches,
      selectedGhostAngles,
      selectedTransitionAngle,
      priorityObjections,
      selection.operatorNotes,
    ),
  };
}
