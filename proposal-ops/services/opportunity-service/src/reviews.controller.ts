import type { ReviewCommentRequest, ReviewCommentResponse } from "./contracts";

export class ReviewsController {
  addComment(_opportunityId: string, cycleId: string, _body: ReviewCommentRequest): ReviewCommentResponse {
    return {
      review_comment_id: `rvc_${Date.now()}`,
      cycle_id: cycleId,
      resolution_status: "OPEN"
    };
  }
}
