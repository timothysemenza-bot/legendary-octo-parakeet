import type { Opportunity } from "../../domain/opportunity";
import type { ProposalNarrativeSections } from "../../domain/proposalExperience";
import type { QualificationResult } from "../../domain/qualification";
import type { SolutionPlan } from "../../domain/solution";

export interface NarrativeService {
  compose(
    opportunity: Opportunity,
    qualification: QualificationResult,
    solution: SolutionPlan,
  ): ProposalNarrativeSections;
}

