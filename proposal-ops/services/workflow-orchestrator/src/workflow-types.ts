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
export type GateDecision = "APPROVED" | "REJECTED" | "REWORK_REQUIRED";

export interface WorkflowContext {
  client_id: string;
  workspace_id: string;
  opportunity_id: string;
  current_stage: Stage;
}

export interface GateSignal {
  gate_code: GateCode;
  decision: GateDecision;
  actor_id: string;
  rationale: string;
}
