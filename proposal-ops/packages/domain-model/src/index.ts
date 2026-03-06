export type ISODate = string;

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

export interface TenantScoped {
  client_id: string;
  workspace_id: string;
}

export interface Opportunity extends TenantScoped {
  id: string;
  title: string;
  buyer: string;
  due_date: ISODate;
  stage: Stage;
  status: "IN_PROGRESS" | "BLOCKED" | "COMPLETED";
  owner_id: string;
  priority: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
}

export interface Requirement extends TenantScoped {
  id: string;
  solicitation_id: string;
  req_code: string;
  text: string;
  atomic_index: number;
  category: string;
  mandatory: boolean;
  source_locator: {
    doc_id: string;
    page: number;
    line_start: number;
    line_end: number;
  };
}

export interface ComplianceMatrixRow extends TenantScoped {
  id: string;
  opportunity_id: string;
  requirement_id: string;
  response_section_id: string;
  status: "UNMAPPED" | "MAPPED" | "IN_PROGRESS" | "VALIDATED";
  owner_id: string;
  evidence_refs: string[];
}

export interface SectionDraft extends TenantScoped {
  id: string;
  opportunity_id: string;
  section_code: string;
  owner_id: string;
  status: "DRAFT" | "IN_REVIEW" | "APPROVED" | "REWORK";
  content_ref: string;
  citations: string[];
  unsupported_claim_flags: string[];
}

export interface GateDecision extends TenantScoped {
  id: string;
  opportunity_id: string;
  gate_code: GateCode;
  decision: GateDecisionValue;
  decider_id: string;
  rationale: string;
  rework_instructions: string[];
  created_at: string;
}
