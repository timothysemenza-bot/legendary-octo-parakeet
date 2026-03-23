import type { ProposalExperience } from "../domain/proposalExperience";
import type { QualificationResult } from "../domain/qualification";
import type { SolutionPlan } from "../domain/solution";
import type {
  ApprovalStage,
  ApprovalCheckpoint,
  AssumptionLedgerEntry,
  OperatorWorkspaceSnapshot,
  PursuitDraft,
  ReviewCheckpoint,
  ScenarioSnapshot,
  ScenarioSummary,
} from "../domain/operatorWorkspace";
import { buildProposalExperience } from "./proposalComposer";
import { assembleSolution } from "./solutionAssembler";

function dedupeAssumptions(values: string[]): string[] {
  return Array.from(new Set(values));
}

function applyDraftToExperience(
  experience: ProposalExperience,
  draft: PursuitDraft,
): ProposalExperience {
  const operatorAssumptions = draft.operatorAssumptions.map(
    (assumption) => assumption.text,
  );

  return {
    ...experience,
    scopeSummary: {
      ...experience.scopeSummary,
      assumptions: dedupeAssumptions([
        ...experience.scopeSummary.assumptions,
        ...operatorAssumptions,
      ]),
    },
  };
}

function filterSolution(solution: SolutionPlan, draft: PursuitDraft): SolutionPlan {
  return {
    ...solution,
    modules: solution.modules.filter(
      (module) => !draft.excludedModuleIds.includes(module.id),
    ),
  };
}

function buildAssumptionLedger(
  experience: ProposalExperience,
  draft: PursuitDraft,
): AssumptionLedgerEntry[] {
  const engineItems = experience.scopeSummary.assumptions.map((text, index) => ({
    id: `engine-${index}`,
    text,
    source: "engine" as const,
    status: "derived" as const,
    owner: "System",
    impactArea: "experience" as const,
  }));

  const operatorItems = draft.operatorAssumptions.map((assumption) => ({
    id: assumption.id,
    text: assumption.text,
    source: "operator" as const,
    status: assumption.status,
    owner: assumption.owner,
    impactArea: assumption.impactArea,
  }));

  return [...engineItems, ...operatorItems];
}

function findNextReviewCheckpoint(
  reviewCheckpoints: ReviewCheckpoint[],
): ReviewCheckpoint | undefined {
  return reviewCheckpoints.find((checkpoint) => checkpoint.status !== "complete");
}

function buildNextReviewLabel(
  reviewCheckpoints: ReviewCheckpoint[],
): string {
  const nextReview = findNextReviewCheckpoint(reviewCheckpoints);

  return nextReview
    ? `${nextReview.apmpLabel}: ${nextReview.title} (${nextReview.status})`
    : "All planned reviews complete";
}

function buildBlockingItems(
  draft: PursuitDraft,
  qualification: QualificationResult,
): string[] {
  return [
    ...qualification.riskFlags
      .filter((flag) => flag.severity === "high")
      .map((flag) => flag.title),
    ...draft.reviewCheckpoints
      .filter((checkpoint) => checkpoint.status === "blocked")
      .map((checkpoint) => `${checkpoint.apmpLabel} is blocked`),
    ...draft.operatorAssumptions
      .filter((assumption) => assumption.status !== "validated")
      .map((assumption) => `${assumption.impactArea}: ${assumption.text}`),
  ];
}

function buildGateAdvanceCriteria(stage: ApprovalStage): string[] {
  if (stage === "qualification") {
    return [
      "The opportunity is strategically worth pursuing.",
      "Margin and transition assumptions are acceptable.",
      "Major fit risks have a mitigation or written rationale.",
    ];
  }

  if (stage === "solution") {
    return [
      "The service mix and staffing plan fit the site profile.",
      "Proof and differentiators support the proposed approach.",
      "The operating model is strong enough to carry into buyer review.",
    ];
  }

  return [
    "The buyer-facing experience is coherent and decision-ready.",
    "The export summary matches the operating story.",
    "Release blockers and open actions are closed or explicitly accepted.",
  ];
}

function buildScenarioSummary(
  qualification: QualificationResult,
  experience: ProposalExperience,
  draft: PursuitDraft,
  approvals: ApprovalCheckpoint[],
  openActions: OperatorWorkspaceSnapshot["openActions"],
): ScenarioSummary {
  return {
    score: qualification.score,
    status: qualification.status,
    moduleCount: experience.solution.modules.length,
    assumptionCount: experience.scopeSummary.assumptions.length,
    openAssumptionCount: draft.operatorAssumptions.filter(
      (assumption) => assumption.status !== "validated",
    ).length,
    highRiskCount: qualification.riskFlags.filter((flag) => flag.severity === "high")
      .length,
    openActionCount: openActions.filter((action) => action.status === "open").length,
    completedReviews: draft.reviewCheckpoints.filter(
      (checkpoint) => checkpoint.status === "complete",
    ).length,
    approvedStages: approvals.filter((approval) => approval.status === "approved")
      .length,
    currentGate: findCurrentGate(approvals),
    nextReviewCheckpoint: buildNextReviewLabel(draft.reviewCheckpoints),
    blockerCount: buildBlockingItems(draft, qualification).length,
    pendingReviewCount: draft.reviewCheckpoints.filter(
      (checkpoint) => checkpoint.status !== "complete",
    ).length,
    pendingApprovalCount: approvals.filter(
      (approval) => approval.status !== "approved",
    ).length,
  };
}

function findCurrentGate(approvals: ApprovalCheckpoint[]): ApprovalStage {
  const nextUnapproved = approvals.find(
    (approval) => approval.status !== "approved",
  );
  return nextUnapproved?.stage ?? "experience";
}

function buildGateStatus(
  draft: PursuitDraft,
  qualification: QualificationResult,
  openActions: OperatorWorkspaceSnapshot["openActions"],
): OperatorWorkspaceSnapshot["gateStatus"] {
  const currentGate = findCurrentGate(draft.approvals);
  const decisionRequired =
    currentGate === "qualification"
      ? "Confirm strategic fit, margin floor, and pursue posture."
      : currentGate === "solution"
        ? "Confirm staffing, proof alignment, and service module fit."
        : "Confirm the buyer-facing experience and export fallback are decision-ready.";

  return {
    currentGate,
    decisionRequired,
    nextReviewCheckpoint: buildNextReviewLabel(draft.reviewCheckpoints),
    blockingItems: buildBlockingItems(draft, qualification).slice(0, 5),
    openActions: openActions
      .filter((action) => action.status === "open")
      .slice(0, 6)
      .map((action) => `${action.title} (${action.owner}, ${action.dueLabel})`),
  };
}

function buildNextCheckpoint(
  draft: PursuitDraft,
  qualification: QualificationResult,
  openActions: OperatorWorkspaceSnapshot["openActions"],
): OperatorWorkspaceSnapshot["nextCheckpoint"] {
  const currentGate = findCurrentGate(draft.approvals);
  const blockingItems = buildBlockingItems(draft, qualification).slice(0, 5);
  const reviewByGate: Record<ApprovalStage, ReviewCheckpoint["id"][]> = {
    qualification: [],
    solution: ["content-plan-review"],
    experience: ["evaluator-review", "gold-readiness-review"],
  };

  const nextReview = draft.reviewCheckpoints.find(
    (checkpoint) =>
      checkpoint.status !== "complete" &&
      reviewByGate[currentGate].includes(checkpoint.id),
  );

  if (nextReview) {
    const ownerActions = openActions.filter(
      (action) =>
        action.status === "open" &&
        action.stageType === "review" &&
        action.linkedStage === nextReview.id,
    );

    return {
      type: "review",
      label: nextReview.apmpLabel,
      title: nextReview.title,
      status: nextReview.status,
      dueLabel: nextReview.dueLabel,
      summary: nextReview.objective,
      blockers: blockingItems,
      ownerActions: ownerActions.slice(0, 4),
      advanceCriteria: nextReview.exitCriteria,
    };
  }

  const approval = draft.approvals.find((item) => item.stage === currentGate);
  const ownerActions = openActions.filter(
    (action) => action.status === "open" && action.stageType === "approval",
  );
  const status = approval?.status ?? "pending";
  const summary =
    currentGate === "qualification"
      ? "Make the pursue decision before spending more energy on solutioning."
      : currentGate === "solution"
        ? "Decide whether the current offer shape is strong enough to move into final buyer prep."
        : "Decide whether the buyer-facing experience is ready to release.";

  return {
    type: "gate",
    label: "Decision gate",
    title:
      currentGate === "qualification"
        ? "Qualification Decision"
        : currentGate === "solution"
          ? "Solution Decision"
          : "Release Decision",
    status,
    dueLabel: "Current step",
    summary,
    blockers: blockingItems,
    ownerActions: ownerActions.slice(0, 4),
    advanceCriteria: buildGateAdvanceCriteria(currentGate),
  };
}

function buildSystemActions(
  draft: PursuitDraft,
  qualification: QualificationResult,
): OperatorWorkspaceSnapshot["openActions"] {
  const systemRiskActions = qualification.riskFlags.map((flag) => ({
    id: `risk-${flag.code}`,
    title: `Mitigate ${flag.title.toLowerCase()}`,
    owner: "Operator",
    dueLabel: "Before next gate",
    closeCondition: "Risk is mitigated or an explicit disposition is recorded.",
    stageType: "approval" as const,
    linkedStage: findCurrentGate(draft.approvals),
    source: "system" as const,
    status: "open" as const,
  }));

  const systemRecommendationActions = qualification.recommendedActions.map(
    (action, index) => ({
      id: `recommendation-${index}`,
      title: action,
      owner: "Operator",
      dueLabel: "Before next gate",
      closeCondition: "Recommendation is resolved or accepted with written rationale.",
      stageType: "approval" as const,
      linkedStage: findCurrentGate(draft.approvals),
      source: "system" as const,
      status: "open" as const,
    }),
  );

  const assumptionActions = draft.operatorAssumptions
    .filter((assumption) => assumption.status !== "validated")
    .map((assumption) => ({
      id: `assumption-${assumption.id}`,
      title: `Resolve ${assumption.impactArea} assumption`,
      owner: assumption.owner,
      dueLabel: "Before next gate",
      closeCondition: "Assumption is validated, retired, or explicitly accepted as a watch item.",
      stageType: "approval" as const,
      linkedStage: assumption.impactArea,
      source: "system" as const,
      status: "open" as const,
    }));

  const reviewActions = draft.reviewCheckpoints
    .filter((checkpoint) => checkpoint.status !== "complete")
    .map((checkpoint) => ({
      id: `review-${checkpoint.id}`,
      title:
        checkpoint.status === "blocked"
          ? `Clear blockers for ${checkpoint.apmpLabel.toLowerCase()}`
          : checkpoint.status === "rework-required"
            ? `Close rework from ${checkpoint.apmpLabel.toLowerCase()}`
            : checkpoint.status === "in-review"
              ? `Consolidate comments from ${checkpoint.apmpLabel.toLowerCase()}`
              : checkpoint.status === "ready"
                ? `Conduct ${checkpoint.apmpLabel.toLowerCase()}`
                : `Prepare ${checkpoint.apmpLabel.toLowerCase()}`,
      owner: "Operator",
      dueLabel: checkpoint.dueLabel,
      closeCondition:
        checkpoint.status === "blocked"
          ? "The blocking issue is removed and the checkpoint returns to ready."
          : checkpoint.status === "rework-required"
            ? "Rework is complete and the checkpoint can be closed or returned to review."
            : checkpoint.status === "in-review"
              ? "Comments are dispositioned into owned actions with close conditions."
              : checkpoint.status === "ready"
                ? "The review is completed against its exit criteria."
                : "Inputs, proof, and issue log are ready for the checkpoint.",
      stageType: "review" as const,
      linkedStage: checkpoint.id,
      source: "system" as const,
      status: "open" as const,
    }));

  return [
    ...systemRiskActions,
    ...systemRecommendationActions,
    ...assumptionActions,
    ...reviewActions,
  ];
}

function buildOperatorActions(
  draft: PursuitDraft,
): OperatorWorkspaceSnapshot["openActions"] {
  return draft.operatorActions.map((action) => ({
    ...action,
    source: "operator" as const,
  }));
}

export function buildOperatorWorkspaceSnapshot(
  draft: PursuitDraft,
): OperatorWorkspaceSnapshot {
  const baseSolution = assembleSolution(draft.opportunity);
  const filteredSolution = filterSolution(baseSolution, draft);
  const baseExperience = buildProposalExperience(draft.opportunity, undefined, {
    solutionOverride: filteredSolution,
  });
  const experience = applyDraftToExperience(baseExperience, draft);
  const openActions = [
    ...buildSystemActions(draft, experience.qualification),
    ...buildOperatorActions(draft),
  ];
  const summary = buildScenarioSummary(
    experience.qualification,
    experience,
    draft,
    draft.approvals,
    openActions,
  );

  return {
    experience,
    availableModules: baseSolution.modules,
    assumptionLedger: buildAssumptionLedger(baseExperience, draft),
    openActions,
    nextCheckpoint: buildNextCheckpoint(draft, experience.qualification, openActions),
    gateStatus: buildGateStatus(draft, experience.qualification, openActions),
    summary,
    approvals: draft.approvals,
    reviewCheckpoints: draft.reviewCheckpoints,
  };
}

export function createScenarioSnapshot(
  name: string,
  draft: PursuitDraft,
  rationale: string,
): ScenarioSnapshot {
  const snapshot = buildOperatorWorkspaceSnapshot(draft);

  return {
    id: globalThis.crypto.randomUUID(),
    name,
    rationale,
    savedAt: new Date().toISOString(),
    draft: structuredClone(draft),
    summary: snapshot.summary,
  };
}
