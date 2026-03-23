import type { Opportunity } from "../domain/opportunity";
import type { ProposalExperience } from "../domain/proposalExperience";
import type { QualificationResult } from "../domain/qualification";
import type { SolutionPlan } from "../domain/solution";
import { qualifyOpportunity } from "./qualificationEngine";
import { assembleSolution } from "./solutionAssembler";
import type { NarrativeService } from "../services/narrative/NarrativeService";
import { RuleBasedNarrativeService } from "../services/narrative/RuleBasedNarrativeService";

const defaultNarrativeService = new RuleBasedNarrativeService();

export interface ProposalBuildOptions {
  qualificationOverride?: QualificationResult;
  solutionOverride?: SolutionPlan;
}

export function buildProposalExperience(
  opportunity: Opportunity,
  narrativeService: NarrativeService = defaultNarrativeService,
  options: ProposalBuildOptions = {},
): ProposalExperience {
  const qualification = options.qualificationOverride ?? qualifyOpportunity(opportunity);
  const solution = options.solutionOverride ?? assembleSolution(opportunity);
  const narrative = narrativeService.compose(
    opportunity,
    qualification,
    solution,
  );

  return {
    opportunity,
    qualification,
    solution,
    ...narrative,
    proofExamples: solution.proofExamples,
  };
}
