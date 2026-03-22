export type EngagementStage =
  | "SIGNAL_CAPTURE"
  | "ENGAGEMENT_TRIAGE"
  | "TIMELINE_SEED"
  | "ACTION_SEED"
  | "APPROVAL_WAIT"
  | "FOUNDER_BRIEF"
  | "FOLLOW_THROUGH"
  | "KNOWLEDGE_PROMOTION"
  | "CLOSED";

export type EngagementGateCode =
  | "GATE_ENGAGEMENT_TRIAGE"
  | "GATE_APPROVAL_DECISION"
  | "GATE_FOUNDER_SIGNOFF";

export type EngagementGateDecision = "APPROVED" | "REJECTED" | "REWORK_REQUIRED";

export type EngagementWorkflowStatus = "IN_PROGRESS" | "WAITING_APPROVAL" | "BLOCKED" | "COMPLETED";

export interface EngagementWorkflowContext {
  run_id: string;
  owner: string;
  agent_id: string;
  source_signal_id: string;
  current_stage: EngagementStage;
  status: EngagementWorkflowStatus;
  processed_signal_ids: string[];
  provenance?: string;
}

export interface EngagementGateSignal {
  gate_code: EngagementGateCode;
  decision: EngagementGateDecision;
  actor_id: string;
  rationale: string;
  signal_id: string;
}

export interface StageTransition {
  allowed: boolean;
  next_stage: EngagementStage;
  status: EngagementWorkflowStatus;
  reason: string;
}
