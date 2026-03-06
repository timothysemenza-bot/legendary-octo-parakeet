import { GatesController } from "./gates.controller";
import { OpportunitiesController } from "./opportunities.controller";
import { ReviewsController } from "./reviews.controller";
import { SubmissionController } from "./submission.controller";

// NestJS wiring placeholder. Replace with @Module when Nest packages are added.
export class AppModule {
  readonly opportunities = new OpportunitiesController();
  readonly gates = new GatesController();
  readonly reviews = new ReviewsController();
  readonly submission = new SubmissionController();
}
