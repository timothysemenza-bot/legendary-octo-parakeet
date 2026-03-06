export type Stage =
  | "INTAKE"
  | "QUALIFICATION"
  | "STRATEGY"
  | "COMPLIANCE"
  | "CONTENT_PLANNING"
  | "DRAFTING"
  | "REVIEW"
  | "SUBMISSION"
  | "ARCHIVE";

export type GateCode = "GATE_A" | "GATE_B" | "GATE_C" | "GATE_D" | "GATE_E" | "GATE_F" | "GATE_G";
export type GateDecisionValue = "APPROVED" | "REJECTED" | "REWORK_REQUIRED";

export interface TenantContext {
  client_id: string;
  workspace_id: string;
  actor_id: string;
}

export interface IntakeRequest {
  context: TenantContext;
  opportunity_title: string;
  buyer: string;
  due_date: string;
  source_documents: string[];
}

export interface IntakeResponse {
  opportunity_id: string;
  solicitation_id: string;
  stage: Stage;
}

export interface QualifyRequest {
  context: TenantContext;
  criteria_scores: Record<string, number>;
  notes?: string;
}

export interface QualifyResponse {
  recommendation: "GO" | "CONDITIONAL" | "NO_GO";
  weighted_score: number;
  missing_data: string[];
}

export interface ShredRequest {
  context: TenantContext;
  solicitation_id: string;
  raw_text: string;
}

export interface ShredResponse {
  requirement_count: number;
  compliance_matrix_id: string;
  response_matrix_id: string;
}

export interface GateDecisionRequest {
  context: TenantContext;
  decision: GateDecisionValue;
  rationale: string;
  rework_instructions?: string[];
}

export interface GateDecisionResponse {
  gate_decision_id: string;
  opportunity_id: string;
  gate_code: GateCode;
  decision: GateDecisionValue;
  resulting_stage: Stage;
  status: "IN_PROGRESS" | "BLOCKED";
}

export interface ReviewCommentRequest {
  context: TenantContext;
  section_draft_id: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  comment: string;
}

export interface ReviewCommentResponse {
  review_comment_id: string;
  cycle_id: string;
  resolution_status: "OPEN";
}

export interface SubmissionAuthorizeRequest {
  context: TenantContext;
  checksum: string;
  artifact_refs: string[];
}

export interface SubmissionAuthorizeResponse {
  submission_package_id: string;
  authorized_by: string;
  submitted_at: string;
}
