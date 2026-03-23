import type {
  OperatorWorkspaceState,
} from "../domain/operatorWorkspace";
import {
  createWorkspaceState,
  operatorWorkspaceStateSchema,
  type PursuitDraft,
} from "../domain/operatorWorkspace";
import type { Opportunity } from "../domain/opportunity";

export const WORKSPACE_STORAGE_KEY = "bosc-pursuit-os.workspace.v2";

export interface StorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

export function loadWorkspaceState(
  storage: StorageLike,
  fallbackOpportunity: Opportunity,
): OperatorWorkspaceState {
  const raw = storage.getItem(WORKSPACE_STORAGE_KEY);

  if (!raw) {
    return createWorkspaceState(fallbackOpportunity);
  }

  try {
    return operatorWorkspaceStateSchema.parse(JSON.parse(raw));
  } catch {
    return createWorkspaceState(fallbackOpportunity);
  }
}

export function saveWorkspaceState(
  storage: StorageLike,
  state: OperatorWorkspaceState,
): void {
  storage.setItem(WORKSPACE_STORAGE_KEY, JSON.stringify(state));
}

export function replaceActiveDraft(
  state: OperatorWorkspaceState,
  nextDraft: PursuitDraft,
): OperatorWorkspaceState {
  return {
    ...state,
    activeDraft: nextDraft,
  };
}
