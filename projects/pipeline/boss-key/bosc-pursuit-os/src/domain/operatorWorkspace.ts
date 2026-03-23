import { z } from "zod";
import { opportunitySchema, type Opportunity } from "./opportunity";
import type { ProposalExperience } from "./proposalExperience";
import {
  createDefaultQualificationDecision,
  PURSUIT_RECOMMENDATIONS,
  QUALIFICATION_DECISION_MODES,
  type PursuitRecommendation,
  type QualificationDecision,
} from "./qualification";
import type { SolutionModule } from "./solution";

export const APPROVAL_STAGES = [
  "qualification",
  "solution",
  "experience",
] as const;
export const APPROVAL_STATUSES = [
  "pending",
  "approved",
  "rework-required",
  "rejected",
] as const;
export const REVIEW_CHECKPOINT_IDS = [
  "content-plan-review",
  "evaluator-review",
  "gold-readiness-review",
] as const;
export const REVIEW_STATUSES = [
  "pending",
  "ready",
  "in-review",
  "rework-required",
  "complete",
  "blocked",
] as const;
export const ASSUMPTION_STATUSES = ["open", "validated", "watch"] as const;
export const ASSUMPTION_IMPACT_AREAS = [
  "qualification",
  "solution",
  "pricing",
  "experience",
  "submission",
] as const;
export const ACTION_STATUSES = ["open", "done"] as const;
export const ACTION_STAGE_TYPES = ["approval", "review"] as const;

export type ApprovalStage = (typeof APPROVAL_STAGES)[number];
export type ApprovalStatus = (typeof APPROVAL_STATUSES)[number];
export type ReviewCheckpointId = (typeof REVIEW_CHECKPOINT_IDS)[number];
export type ReviewStatus = (typeof REVIEW_STATUSES)[number];
export type OperatorAssumptionStatus = (typeof ASSUMPTION_STATUSES)[number];
export type AssumptionImpactArea = (typeof ASSUMPTION_IMPACT_AREAS)[number];
export type ActionStatus = (typeof ACTION_STATUSES)[number];
export type ActionStageType = (typeof ACTION_STAGE_TYPES)[number];

export interface ApprovalCheckpoint {
  stage: ApprovalStage;
  status: ApprovalStatus;
  approvedAt: string | null;
}

export interface OperatorAssumption {
  id: string;
  text: string;
  status: OperatorAssumptionStatus;
  owner: string;
  impactArea: AssumptionImpactArea;
}

export interface ReviewCheckpoint {
  id: ReviewCheckpointId;
  apmpLabel: string;
  title: string;
  objective: string;
  exitCriteria: string[];
  status: ReviewStatus;
  dueLabel: string;
  completedAt: string | null;
}

export interface OperatorAction {
  id: string;
  title: string;
  owner: string;
  dueLabel: string;
  closeCondition: string;
  stageType: ActionStageType;
  linkedStage: string;
  status: ActionStatus;
}

export interface WorkingStorySelection {
  summaryVariantId: string | null;
  winThemeIds: string[];
  proofIds: string[];
  ghostAngleIds: string[];
  transitionAngleId: string | null;
  operatorNotes: string;
}

export interface BuyerStoryVariant {
  id: string;
  name: string;
  savedAt: string;
  selection: WorkingStorySelection;
}

export interface PursuitDraft {
  opportunity: Opportunity;
  excludedModuleIds: string[];
  qualificationDecision: QualificationDecision;
  operatorAssumptions: OperatorAssumption[];
  approvals: ApprovalCheckpoint[];
  reviewCheckpoints: ReviewCheckpoint[];
  operatorActions: OperatorAction[];
  workingStory: WorkingStorySelection;
  buyerStoryVariants: BuyerStoryVariant[];
  promotedBuyerStoryVariantId: string | null;
}

export interface ScenarioSummary {
  score: number;
  status: PursuitRecommendation;
  moduleCount: number;
  assumptionCount: number;
  openAssumptionCount: number;
  highRiskCount: number;
  openActionCount: number;
  completedReviews: number;
  approvedStages: number;
  currentGate: ApprovalStage;
  nextReviewCheckpoint: string;
  blockerCount: number;
  pendingReviewCount: number;
  pendingApprovalCount: number;
}

export interface ScenarioSnapshot {
  id: string;
  name: string;
  rationale: string;
  savedAt: string;
  draft: PursuitDraft;
  summary: ScenarioSummary;
}

export interface OperatorWorkspaceState {
  activeDraft: PursuitDraft;
  savedScenarios: ScenarioSnapshot[];
}

export interface AssumptionLedgerEntry {
  id: string;
  text: string;
  source: "engine" | "operator";
  status: "derived" | OperatorAssumptionStatus;
  owner: string;
  impactArea: AssumptionImpactArea;
}

export interface OperatorWorkspaceSnapshot {
  experience: ProposalExperience;
  availableModules: SolutionModule[];
  assumptionLedger: AssumptionLedgerEntry[];
  openActions: Array<{
    id: string;
    title: string;
    owner: string;
    dueLabel: string;
    closeCondition: string;
    stageType: ActionStageType;
    linkedStage: string;
    source: "system" | "operator";
    status: ActionStatus;
  }>;
  nextCheckpoint: {
    type: "gate" | "review";
    label: string;
    title: string;
    status: string;
    dueLabel: string;
    summary: string;
    blockers: string[];
    ownerActions: Array<{
      id: string;
      title: string;
      owner: string;
      dueLabel: string;
      closeCondition: string;
      stageType: ActionStageType;
      linkedStage: string;
      source: "system" | "operator";
      status: ActionStatus;
    }>;
    advanceCriteria: string[];
  };
  gateStatus: {
    currentGate: ApprovalStage;
    decisionRequired: string;
    nextReviewCheckpoint: string;
    blockingItems: string[];
    openActions: string[];
  };
  summary: ScenarioSummary;
  approvals: ApprovalCheckpoint[];
  reviewCheckpoints: ReviewCheckpoint[];
}

const approvalStageSchema = z.enum(APPROVAL_STAGES);
const approvalStatusSchema = z.enum(APPROVAL_STATUSES);
const reviewCheckpointIdSchema = z.enum(REVIEW_CHECKPOINT_IDS);
const reviewStatusSchema = z.enum(REVIEW_STATUSES);
const assumptionStatusSchema = z.enum(ASSUMPTION_STATUSES);
const assumptionImpactAreaSchema = z.enum(ASSUMPTION_IMPACT_AREAS);
const actionStatusSchema = z.enum(ACTION_STATUSES);
const actionStageTypeSchema = z.enum(ACTION_STAGE_TYPES);
const pursuitRecommendationSchema = z.enum(PURSUIT_RECOMMENDATIONS);
const qualificationDecisionModeSchema = z.enum(QUALIFICATION_DECISION_MODES);

function readOptionalString(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null;
}

function readStringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

export const approvalCheckpointSchema = z.object({
  stage: approvalStageSchema,
  status: approvalStatusSchema,
  approvedAt: z.string().nullable(),
});

export const operatorAssumptionSchema = z.object({
  id: z.string().min(1),
  text: z.string().min(1),
  status: assumptionStatusSchema,
  owner: z.string().min(1),
  impactArea: assumptionImpactAreaSchema,
});

export const reviewCheckpointSchema = z.object({
  id: reviewCheckpointIdSchema,
  apmpLabel: z.string().min(1).default("Review checkpoint"),
  title: z.string().min(1),
  objective: z.string().min(1),
  exitCriteria: z.array(z.string().min(1)).min(1),
  status: reviewStatusSchema,
  dueLabel: z.string().min(1),
  completedAt: z.string().nullable(),
});

export const operatorActionSchema = z.object({
  id: z.string().min(1),
  title: z.string().min(1),
  owner: z.string().min(1),
  dueLabel: z.string().min(1),
  closeCondition: z.string().min(1),
  stageType: actionStageTypeSchema,
  linkedStage: z.string().min(1),
  status: actionStatusSchema,
});

export const workingStorySelectionSchema = z.preprocess(
  (value) => {
    const record =
      typeof value === "object" && value !== null
        ? (value as Record<string, unknown>)
        : {};

    return {
      summaryVariantId:
        readOptionalString(record.summaryVariantId) ??
        readOptionalString(record.summaryVariantTitle),
      winThemeIds:
        readStringArray(record.winThemeIds).length > 0
          ? readStringArray(record.winThemeIds)
          : readStringArray(record.winThemeTitles),
      proofIds:
        readStringArray(record.proofIds).length > 0
          ? readStringArray(record.proofIds)
          : readStringArray(record.proofTitles),
      ghostAngleIds:
        readStringArray(record.ghostAngleIds).length > 0
          ? readStringArray(record.ghostAngleIds)
          : readStringArray(record.ghostAngleTitles),
      transitionAngleId:
        readOptionalString(record.transitionAngleId) ??
        readOptionalString(record.transitionAngleTitle),
      operatorNotes:
        typeof record.operatorNotes === "string" ? record.operatorNotes : "",
    };
  },
  z.object({
    summaryVariantId: z.string().nullable().default(null),
    winThemeIds: z.array(z.string()).default([]),
    proofIds: z.array(z.string()).default([]),
    ghostAngleIds: z.array(z.string()).default([]),
    transitionAngleId: z.string().nullable().default(null),
    operatorNotes: z.string().default(""),
  }),
);

export const buyerStoryVariantSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  savedAt: z.string().min(1),
  selection: workingStorySelectionSchema,
});

export const qualificationDecisionSchema = z.object({
  mode: qualificationDecisionModeSchema.default("pending"),
  selectedStatus: pursuitRecommendationSchema.nullable().default(null),
  note: z.string().default(""),
  decidedAt: z.string().nullable().default(null),
});

export const pursuitDraftSchema = z.object({
  opportunity: opportunitySchema,
  excludedModuleIds: z.array(z.string()),
  qualificationDecision: qualificationDecisionSchema.default(
    createDefaultQualificationDecision(),
  ),
  operatorAssumptions: z.array(operatorAssumptionSchema),
  approvals: z.array(approvalCheckpointSchema),
  reviewCheckpoints: z.array(reviewCheckpointSchema),
  operatorActions: z.array(operatorActionSchema),
  workingStory: workingStorySelectionSchema.default({
    summaryVariantId: null,
    winThemeIds: [],
    proofIds: [],
    ghostAngleIds: [],
    transitionAngleId: null,
    operatorNotes: "",
  }),
  buyerStoryVariants: z.array(buyerStoryVariantSchema).default([]),
  promotedBuyerStoryVariantId: z.string().nullable().default(null),
});

export const scenarioSummarySchema = z.object({
  score: z.number().min(0).max(100),
  status: pursuitRecommendationSchema,
  moduleCount: z.number().int().min(0),
  assumptionCount: z.number().int().min(0),
  openAssumptionCount: z.number().int().min(0),
  highRiskCount: z.number().int().min(0),
  openActionCount: z.number().int().min(0),
  completedReviews: z.number().int().min(0),
  approvedStages: z.number().int().min(0),
  currentGate: approvalStageSchema.default("qualification"),
  nextReviewCheckpoint: z.string().min(1).default("Content Plan Review (pending)"),
  blockerCount: z.number().int().min(0).default(0),
  pendingReviewCount: z.number().int().min(0).default(0),
  pendingApprovalCount: z.number().int().min(0).default(0),
});

export const scenarioSnapshotSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  rationale: z.string().min(1),
  savedAt: z.string().min(1),
  draft: pursuitDraftSchema,
  summary: scenarioSummarySchema,
});

export const operatorWorkspaceStateSchema = z.object({
  activeDraft: pursuitDraftSchema,
  savedScenarios: z.array(scenarioSnapshotSchema),
});

export function createDefaultApprovals(): ApprovalCheckpoint[] {
  return APPROVAL_STAGES.map((stage) => ({
    stage,
    status: "pending",
    approvedAt: null,
  }));
}

export function createDefaultReviewCheckpoints(): ReviewCheckpoint[] {
  return [
    {
      id: "content-plan-review",
      apmpLabel: "Pink Review",
      title: "Content Plan Review",
      objective:
        "Validate story structure, proof plan, and section intent before evaluator-style drafting.",
      exitCriteria: [
        "Outline and section intent are stable.",
        "Evaluation factors are mapped to sections and proof.",
        "Major content gaps have owners and due dates.",
        "Win themes and discriminators are explicit.",
      ],
      status: "pending",
      dueLabel: "Before solution approval",
      completedAt: null,
    },
    {
      id: "evaluator-review",
      apmpLabel: "Red Review",
      title: "Red Review (Evaluator View)",
      objective:
        "Assess the proposal experience as a buyer would and identify rework before final polish.",
      exitCriteria: [
        "Buyer questions are answered from an evaluator view.",
        "Strengths and proof are visible in the experience.",
        "Pricing narrative aligns with the delivery approach.",
        "Major evaluator-facing defects have disposition owners.",
      ],
      status: "pending",
      dueLabel: "Before experience approval",
      completedAt: null,
    },
    {
      id: "gold-readiness-review",
      apmpLabel: "Gold Review",
      title: "Gold Readiness Review",
      objective:
        "Confirm production readiness, export fallback, and final decision controls before release.",
      exitCriteria: [
        "Final files and forms are present in the controlled package.",
        "Executive, pricing, and contract approvals are captured.",
        "Naming, attachments, and export packaging are locked.",
        "Submission and contingency paths are confirmed.",
      ],
      status: "pending",
      dueLabel: "Before final delivery",
      completedAt: null,
    },
  ];
}

export function createPursuitDraft(opportunity: Opportunity): PursuitDraft {
  return {
    opportunity,
    excludedModuleIds: [],
    qualificationDecision: createDefaultQualificationDecision(),
    operatorAssumptions: [],
    approvals: createDefaultApprovals(),
    reviewCheckpoints: createDefaultReviewCheckpoints(),
    operatorActions: [],
    workingStory: {
      summaryVariantId: null,
      winThemeIds: [],
      proofIds: [],
      ghostAngleIds: [],
      transitionAngleId: null,
      operatorNotes: "",
    },
    buyerStoryVariants: [],
    promotedBuyerStoryVariantId: null,
  };
}

export function resetApprovals(approvals: ApprovalCheckpoint[]): ApprovalCheckpoint[] {
  return approvals.map((approval) => ({
    ...approval,
    status: "pending",
    approvedAt: null,
  }));
}

export function resetReviewCheckpoints(
  reviewCheckpoints: ReviewCheckpoint[],
): ReviewCheckpoint[] {
  return reviewCheckpoints.map((checkpoint) => ({
    ...checkpoint,
    status: "pending",
    completedAt: null,
  }));
}

export function createWorkspaceState(
  opportunity: Opportunity,
): OperatorWorkspaceState {
  return {
    activeDraft: createPursuitDraft(opportunity),
    savedScenarios: [],
  };
}
