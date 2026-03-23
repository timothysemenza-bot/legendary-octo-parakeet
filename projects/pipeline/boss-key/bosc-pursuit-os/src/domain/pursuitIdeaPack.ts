import type { PursuitRecommendation } from "./qualification";

export interface StrategyMemo {
  headline: string;
  pursuitCall: PursuitRecommendation;
  unifyingConcept: string;
  elevatorPitch: string;
  priorities: string[];
}

export interface HotButton {
  key: string;
  title: string;
  buyerSignal: string;
  winLeverage: string;
  proofFocus: string;
  weight: number;
  sourceSignals: string[];
}

export interface WinTheme {
  id: string;
  title: string;
  customerIssue: string;
  differentiator: string;
  proofPoint: string;
  themeStatement: string;
}

export interface DifferentiatorOption {
  id: string;
  title: string;
  feature: string;
  benefit: string;
  whyItWins: string;
}

export interface BuyerConcernResponse {
  concern: string;
  whyItMatters: string;
  responseAngle: string;
  counterMessage: string;
  proofToUse: string;
}

export interface TransitionAngle {
  id: string;
  title: string;
  bestFit: string;
  moves: string[];
}

export interface ProofMatch {
  id: string;
  title: string;
  metric: string;
  hotButton: string;
  whyItFits: string;
  strength: string;
  whereToUse: string;
}

export interface CompetitorGhostAngle {
  id: string;
  title: string;
  buyerRisk: string;
  ghostStatement: string;
  bossKeyCounter: string;
  proofToUse: string;
}

export interface ExecutiveSummaryVariant {
  id: string;
  title: string;
  openingLine: string;
  customerDrivers: string[];
  solutionFrame: string;
  proofThread: string;
  close: string;
  useWhen: string;
}

export interface PursuitIdeaContext {
  nextCheckpointTitle: string;
  assumptions: string[];
  openActionTitles: string[];
}

export interface PursuitIdeaPack {
  strategyMemo: StrategyMemo;
  hotButtons: HotButton[];
  winThemes: WinTheme[];
  differentiatorOptions: DifferentiatorOption[];
  buyerConcerns: BuyerConcernResponse[];
  competitorGhostAngles: CompetitorGhostAngle[];
  transitionAngles: TransitionAngle[];
  proofMatches: ProofMatch[];
  executiveSummaryVariants: ExecutiveSummaryVariant[];
  validationQuestions: string[];
}
