import type { Opportunity } from "../domain/opportunity";
import {
  createOpportunityLibrary,
  createOpportunityRecord,
  opportunityLibraryStateSchema,
  touchOpportunityRecord,
  type OpportunityLibraryState,
  type OpportunityRecord,
} from "../domain/opportunityLibrary";
import {
  createWorkspaceState,
  operatorWorkspaceStateSchema,
  type OperatorWorkspaceState,
} from "../domain/operatorWorkspace";
import {
  WORKSPACE_STORAGE_KEY,
  type StorageLike,
} from "./operatorWorkspaceStorage";

export const OPPORTUNITY_LIBRARY_STORAGE_KEY =
  "boss-key.pursuit-os.opportunity-library.v1";

function normalizeLibraryState(
  state: OpportunityLibraryState,
): OpportunityLibraryState {
  const activeRecordPresent = state.records.some(
    (record) => record.id === state.activeRecordId,
  );

  return {
    activeRecordId: activeRecordPresent
      ? state.activeRecordId
      : state.records[0].id,
    records: state.records,
  };
}

function buildFallbackLibrary(
  fallbackOpportunity: Opportunity,
): OpportunityLibraryState {
  return createOpportunityLibrary(
    createOpportunityRecord({
      workspaceState: createWorkspaceState(fallbackOpportunity),
      origin: "demo",
      sourceLabel: "Demo seed",
    }),
  );
}

export function loadOpportunityLibrary(
  storage: StorageLike,
  fallbackOpportunity: Opportunity,
): OpportunityLibraryState {
  const raw = storage.getItem(OPPORTUNITY_LIBRARY_STORAGE_KEY);

  if (raw) {
    try {
      return normalizeLibraryState(
        opportunityLibraryStateSchema.parse(JSON.parse(raw)),
      );
    } catch {
      // Fall through to migration / fallback.
    }
  }

  const legacyRaw = storage.getItem(WORKSPACE_STORAGE_KEY);
  if (legacyRaw) {
    try {
      const legacyWorkspaceState = operatorWorkspaceStateSchema.parse(
        JSON.parse(legacyRaw),
      );

      return createOpportunityLibrary(
        createOpportunityRecord({
          workspaceState: legacyWorkspaceState,
          origin: "manual",
          sourceLabel: "Migrated local workspace",
        }),
      );
    } catch {
      // Fall through to the seeded demo record.
    }
  }

  return buildFallbackLibrary(fallbackOpportunity);
}

export function saveOpportunityLibrary(
  storage: StorageLike,
  state: OpportunityLibraryState,
): void {
  storage.setItem(OPPORTUNITY_LIBRARY_STORAGE_KEY, JSON.stringify(state));
}

export function replaceActiveWorkspaceState(
  state: OpportunityLibraryState,
  nextWorkspaceState: OperatorWorkspaceState,
): OpportunityLibraryState {
  return {
    ...state,
    records: state.records.map((record) =>
      record.id !== state.activeRecordId
        ? record
        : touchOpportunityRecord(record, nextWorkspaceState),
    ),
  };
}

export function addOpportunityRecord(
  state: OpportunityLibraryState,
  record: OpportunityRecord,
): OpportunityLibraryState {
  return {
    activeRecordId: record.id,
    records: [record, ...state.records],
  };
}

export function selectOpportunityRecord(
  state: OpportunityLibraryState,
  recordId: string,
): OpportunityLibraryState {
  if (!state.records.some((record) => record.id === recordId)) {
    return state;
  }

  return {
    ...state,
    activeRecordId: recordId,
  };
}
