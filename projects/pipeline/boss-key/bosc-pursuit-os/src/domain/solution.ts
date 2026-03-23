import type { ServiceType } from "./opportunity";

export type SolutionModuleCategory = "core" | "operations" | "experience" | "proof";

export interface SolutionModule {
  id: string;
  name: string;
  category: SolutionModuleCategory;
  summary: string;
  rationale: string;
  differentiator: string;
  servicesCovered: ServiceType[];
  assumptions: string[];
}

export interface StaffingPlan {
  nightlyCleanerFte: number;
  dayPorterFte: number;
  supervisorFte: number;
  summary: string;
}

export interface TransitionMilestone {
  phase: string;
  timing: string;
  detail: string;
}

export type ProofEvidenceType =
  | "case-study"
  | "operations-metric"
  | "transition-playbook";

export interface ProofExample {
  id: string;
  title: string;
  metric: string;
  description: string;
  tags: string[];
  services: ServiceType[];
  buyerHotButtons: string[];
  evidenceType: ProofEvidenceType;
  bestUse: string[];
}

export interface SolutionPlan {
  modules: SolutionModule[];
  staffing: StaffingPlan;
  transitionMilestones: TransitionMilestone[];
  proofExamples: ProofExample[];
  assumptions: string[];
}
