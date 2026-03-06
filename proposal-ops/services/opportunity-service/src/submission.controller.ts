import type { SubmissionAuthorizeRequest, SubmissionAuthorizeResponse } from "./contracts";
import { canAuthorizeSubmission } from "../../../packages/workflow-definitions/state-machine";

export class SubmissionController {
  authorize(
    _opportunityId: string,
    body: SubmissionAuthorizeRequest,
    gateFDecision: "APPROVED" | "REJECTED" | "REWORK_REQUIRED" | null
  ): SubmissionAuthorizeResponse {
    if (!canAuthorizeSubmission(gateFDecision)) {
      throw new Error("Submission blocked: Gate F must be APPROVED.");
    }

    return {
      submission_package_id: `sub_${Date.now()}`,
      authorized_by: body.context.actor_id,
      submitted_at: new Date().toISOString()
    };
  }
}
