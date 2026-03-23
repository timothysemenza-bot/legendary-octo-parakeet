import type { Opportunity } from "../../domain/opportunity";
import type {
  PursuitIdeaContext,
  PursuitIdeaPack,
} from "../../domain/pursuitIdeaPack";
import type { QualificationResult } from "../../domain/qualification";
import type { SolutionPlan } from "../../domain/solution";

export interface IdeaGenerationService {
  compose(
    opportunity: Opportunity,
    qualification: QualificationResult,
    solution: SolutionPlan,
    context: PursuitIdeaContext,
  ): PursuitIdeaPack;
}
