import type { Opportunity } from "./opportunity";
import type { QualificationResult } from "./qualification";
import type {
  ProofExample,
  SolutionPlan,
  TransitionMilestone,
} from "./solution";

export interface DecisionFeedCard {
  id: string;
  label: string;
  headline: string;
  summary: string;
  bullets: string[];
  proof?: string;
  tone: "signal" | "confidence" | "transition" | "proof";
}

export interface Brief90 {
  title: string;
  summary: string;
  signalChips: string[];
  decisionPoints: string[];
}

export interface ProposalExperience {
  opportunity: Opportunity;
  qualification: QualificationResult;
  solution: SolutionPlan;
  overview: {
    headline: string;
    summary: string;
    buyerFraming: string;
    recommendation: string;
  };
  scopeSummary: {
    operatingModel: string;
    coveragePlan: string;
    serviceLines: string[];
    assumptions: string[];
  };
  differentiators: string[];
  transitionApproach: {
    title: string;
    summary: string;
    milestones: TransitionMilestone[];
  };
  brief90: Brief90;
  decisionFeed: DecisionFeedCard[];
  proofExamples: ProofExample[];
  exportSummary: {
    sections: Array<{
      title: string;
      items: string[];
    }>;
  };
}

export type ProposalNarrativeSections = Pick<
  ProposalExperience,
  | "overview"
  | "scopeSummary"
  | "differentiators"
  | "transitionApproach"
  | "brief90"
  | "decisionFeed"
  | "exportSummary"
>;
