import type { OperatorWorkspaceSnapshot } from "../domain/operatorWorkspace";
import type { PursuitIdeaPack } from "../domain/pursuitIdeaPack";
import type { IdeaGenerationService } from "../services/ideas/IdeaGenerationService";
import { RuleBasedIdeaGenerationService } from "../services/ideas/RuleBasedIdeaGenerationService";

const defaultIdeaGenerationService = new RuleBasedIdeaGenerationService();

export function buildPursuitIdeaPack(
  snapshot: OperatorWorkspaceSnapshot,
  ideaGenerationService: IdeaGenerationService = defaultIdeaGenerationService,
): PursuitIdeaPack {
  const openActionTitles = snapshot.openActions
    .filter((action) => action.status === "open")
    .sort((left, right) => {
      if (left.source === right.source) {
        return 0;
      }

      return left.source === "operator" ? -1 : 1;
    })
    .map((action) => action.title);

  return ideaGenerationService.compose(
    snapshot.experience.opportunity,
    snapshot.experience.qualification,
    snapshot.experience.solution,
    {
      nextCheckpointTitle: snapshot.nextCheckpoint.title,
      assumptions: snapshot.assumptionLedger.map((item) => item.text),
      openActionTitles,
    },
  );
}
