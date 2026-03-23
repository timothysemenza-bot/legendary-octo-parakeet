import type {
  BuyerConcernResponse,
  CompetitorGhostAngle,
  ExecutiveSummaryVariant,
  ProofMatch,
  TransitionAngle,
  WinTheme,
} from "./pursuitIdeaPack";
import type { Brief90, DecisionFeedCard } from "./proposalExperience";
import type { BuyerStoryVariant } from "./operatorWorkspace";

export interface WorkingStoryBrief {
  headline: string;
  summaryVariant: ExecutiveSummaryVariant;
  selectedWinThemes: WinTheme[];
  selectedProofMatches: ProofMatch[];
  selectedGhostAngles: CompetitorGhostAngle[];
  selectedTransitionAngle: TransitionAngle | null;
  priorityObjections: BuyerConcernResponse[];
  briefText: string;
}

export interface BuyerStoryConceptSheet {
  variantId: string;
  name: string;
  savedAt: string;
  brief90: Brief90;
  decisionFeed: DecisionFeedCard[];
  themeTitles: string[];
  proofTitles: string[];
  memoText: string;
}

export interface BuyerStoryVariantRecord {
  variant: BuyerStoryVariant;
  brief: WorkingStoryBrief;
  conceptSheet: BuyerStoryConceptSheet;
  promoted: boolean;
}
