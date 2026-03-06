export type AuditActorType = "human" | "agent" | "system";

export interface AuditEvent {
  event_id: string;
  timestamp: string;
  actor_type: AuditActorType;
  actor_id: string;
  client_id: string;
  workspace_id: string;
  opportunity_id: string;
  action: string;
  before_state: string;
  after_state: string;
  linked_artifacts: string[];
}
