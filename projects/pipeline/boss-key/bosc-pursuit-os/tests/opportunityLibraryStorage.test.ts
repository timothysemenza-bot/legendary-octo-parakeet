import eastBayOpportunityJson from "../inputs/east-bay-library-opportunity.json";
import { describe, expect, it } from "vitest";
import { parseOpportunity } from "../src/domain/opportunity";
import { createWorkspaceState } from "../src/domain/operatorWorkspace";
import {
  loadOpportunityLibrary,
  saveOpportunityLibrary,
} from "../src/services/opportunityLibraryStorage";
import { WORKSPACE_STORAGE_KEY } from "../src/services/operatorWorkspaceStorage";

function createMemoryStorage(seed: Record<string, string> = {}) {
  const values = new Map(Object.entries(seed));

  return {
    getItem(key: string) {
      return values.get(key) ?? null;
    },
    setItem(key: string, value: string) {
      values.set(key, value);
    },
  };
}

const eastBayOpportunity = parseOpportunity(eastBayOpportunityJson);

describe("opportunity library storage", () => {
  it("seeds a demo record when no saved library exists", () => {
    const storage = createMemoryStorage();
    const library = loadOpportunityLibrary(storage, eastBayOpportunity);

    expect(library.records).toHaveLength(1);
    expect(library.records[0].origin).toBe("demo");
    expect(library.records[0].workspaceState.activeDraft.opportunity.id).toBe(
      eastBayOpportunity.id,
    );
  });

  it("migrates the legacy single-workspace state into the new library", () => {
    const legacyWorkspace = createWorkspaceState(eastBayOpportunity);
    const storage = createMemoryStorage({
      [WORKSPACE_STORAGE_KEY]: JSON.stringify(legacyWorkspace),
    });

    const library = loadOpportunityLibrary(storage, eastBayOpportunity);

    expect(library.records).toHaveLength(1);
    expect(library.records[0].origin).toBe("manual");
    expect(library.records[0].sourceLabel).toBe("Migrated local workspace");
    expect(library.records[0].workspaceState.activeDraft.opportunity.buyerName).toBe(
      eastBayOpportunity.buyerName,
    );
  });

  it("round-trips the saved library state", () => {
    const storage = createMemoryStorage();
    const initialLibrary = loadOpportunityLibrary(storage, eastBayOpportunity);

    saveOpportunityLibrary(storage, initialLibrary);
    const reloadedLibrary = loadOpportunityLibrary(storage, eastBayOpportunity);

    expect(reloadedLibrary.activeRecordId).toBe(initialLibrary.activeRecordId);
    expect(reloadedLibrary.records[0].workspaceState.activeDraft.opportunity.id).toBe(
      initialLibrary.records[0].workspaceState.activeDraft.opportunity.id,
    );
  });
});
