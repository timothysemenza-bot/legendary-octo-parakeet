import type {
  IntakeRequest,
  IntakeResponse,
  QualifyRequest,
  QualifyResponse,
  ShredRequest,
  ShredResponse
} from "./contracts";

export class OpportunitiesController {
  intake(body: IntakeRequest): IntakeResponse {
    return {
      opportunity_id: `opp_${Date.now()}`,
      solicitation_id: `sol_${Date.now()}`,
      stage: "INTAKE"
    };
  }

  qualify(_opportunityId: string, body: QualifyRequest): QualifyResponse {
    const scores = Object.values(body.criteria_scores || {});
    const weightedScore = scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
    const recommendation =
      weightedScore >= 80 ? "GO" : weightedScore >= 65 ? "CONDITIONAL" : "NO_GO";

    return {
      recommendation,
      weighted_score: Number(weightedScore.toFixed(2)),
      missing_data: []
    };
  }

  shred(_opportunityId: string, body: ShredRequest): ShredResponse {
    const lines = body.raw_text
      .split(/[\r\n]+/)
      .map((line) => line.trim())
      .filter(Boolean);

    return {
      requirement_count: lines.length,
      compliance_matrix_id: `cmx_${Date.now()}`,
      response_matrix_id: `rmx_${Date.now()}`
    };
  }
}
