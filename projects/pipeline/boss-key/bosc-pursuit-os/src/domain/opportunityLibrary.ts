import { z } from "zod";
import {
  operatorWorkspaceStateSchema,
  type OperatorWorkspaceState,
} from "./operatorWorkspace";
import {
  opportunityImportResultSchema,
  type OpportunityImportResult,
} from "./opportunityImportResult";

export const OPPORTUNITY_RECORD_ORIGINS = [
  "demo",
  "manual",
  "structured-json",
  "source-files",
  "workspace-json",
] as const;

export type OpportunityRecordOrigin = (typeof OPPORTUNITY_RECORD_ORIGINS)[number];

export interface OpportunityRecord {
  id: string;
  origin: OpportunityRecordOrigin;
  sourceLabel: string;
  createdAt: string;
  updatedAt: string;
  workspaceState: OperatorWorkspaceState;
  latestImportResult: OpportunityImportResult | null;
}

export interface OpportunityLibraryState {
  activeRecordId: string;
  records: OpportunityRecord[];
}

export const opportunityRecordSchema = z.object({
  id: z.string().min(1),
  origin: z.enum(OPPORTUNITY_RECORD_ORIGINS),
  sourceLabel: z.string().min(1),
  createdAt: z.string().min(1),
  updatedAt: z.string().min(1),
  workspaceState: operatorWorkspaceStateSchema,
  latestImportResult: opportunityImportResultSchema.nullable().default(null),
});

export const opportunityLibraryStateSchema = z.object({
  activeRecordId: z.string().min(1),
  records: z.array(opportunityRecordSchema).min(1),
});

function createRecordId(): string {
  if (typeof globalThis.crypto?.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }

  return `opp-record-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function createOpportunityRecord({
  workspaceState,
  origin,
  sourceLabel,
  latestImportResult = null,
}: {
  workspaceState: OperatorWorkspaceState;
  origin: OpportunityRecordOrigin;
  sourceLabel: string;
  latestImportResult?: OpportunityImportResult | null;
}): OpportunityRecord {
  const now = new Date().toISOString();

  return {
    id: createRecordId(),
    origin,
    sourceLabel,
    createdAt: now,
    updatedAt: now,
    workspaceState: structuredClone(workspaceState),
    latestImportResult: latestImportResult
      ? structuredClone(latestImportResult)
      : null,
  };
}

export function touchOpportunityRecord(
  record: OpportunityRecord,
  workspaceState: OperatorWorkspaceState,
): OpportunityRecord {
  return {
    ...record,
    updatedAt: new Date().toISOString(),
    workspaceState,
  };
}

export function createOpportunityLibrary(
  record: OpportunityRecord,
): OpportunityLibraryState {
  return {
    activeRecordId: record.id,
    records: [record],
  };
}
