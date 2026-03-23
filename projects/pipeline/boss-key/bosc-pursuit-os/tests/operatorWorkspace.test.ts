import demoOpportunityJson from "../inputs/demo-opportunity.json";
import { describe, expect, it } from "vitest";
import { parseOpportunity } from "../src/domain/opportunity";
import {
  createPursuitDraft,
  createWorkspaceState,
} from "../src/domain/operatorWorkspace";
import {
  buildOperatorWorkspaceSnapshot,
  createScenarioSnapshot,
} from "../src/engine/operatorWorkspace";
import { qualifyOpportunity } from "../src/engine/qualificationEngine";
import {
  loadWorkspaceState,
  saveWorkspaceState,
  WORKSPACE_STORAGE_KEY,
} from "../src/services/operatorWorkspaceStorage";

const demoOpportunity = parseOpportunity(demoOpportunityJson);

describe("operator workspace composition", () => {
  it("seeds APMP-shaped review checkpoints with exit criteria", () => {
    const draft = createPursuitDraft(demoOpportunity);

    expect(draft.reviewCheckpoints).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: "content-plan-review",
          apmpLabel: "Pink Review",
          exitCriteria: expect.arrayContaining([
            "Outline and section intent are stable.",
          ]),
        }),
        expect.objectContaining({
          id: "evaluator-review",
          apmpLabel: "Red Review",
        }),
        expect.objectContaining({
          id: "gold-readiness-review",
          apmpLabel: "Gold Review",
        }),
      ]),
    );
  });

  it("filters excluded modules and carries operator assumptions into the experience snapshot", () => {
    const draft = createPursuitDraft(demoOpportunity);
    draft.excludedModuleIds = ["day-porter-coverage", "consumables-control"];
    draft.operatorAssumptions = [
      {
        id: "assumption-1",
        text: "Buyer will allow a transition walk-through before go-live.",
        status: "watch",
        owner: "Operations lead",
        impactArea: "solution",
      },
    ];
    draft.approvals[0] = {
      ...draft.approvals[0],
      status: "approved",
      approvedAt: "2026-03-22T20:00:00.000Z",
    };

    const snapshot = buildOperatorWorkspaceSnapshot(draft);

    expect(snapshot.experience.solution.modules.map((module) => module.id)).not.toContain(
      "day-porter-coverage",
    );
    expect(snapshot.experience.solution.modules.map((module) => module.id)).not.toContain(
      "consumables-control",
    );
    expect(snapshot.assumptionLedger).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: "assumption-1",
          text: "Buyer will allow a transition walk-through before go-live.",
          source: "operator",
          status: "watch",
        }),
      ]),
    );
    expect(snapshot.experience.scopeSummary.assumptions).toContain(
      "Buyer will allow a transition walk-through before go-live.",
    );
    expect(snapshot.summary.approvedStages).toBe(1);
    expect(snapshot.summary.moduleCount).toBe(snapshot.experience.solution.modules.length);
    expect(snapshot.summary.openAssumptionCount).toBe(1);
    expect(snapshot.summary.currentGate).toBe("solution");
    expect(snapshot.summary.nextReviewCheckpoint).toContain("Pink Review");
    expect(snapshot.summary.blockerCount).toBeGreaterThanOrEqual(1);
    expect(snapshot.summary.pendingReviewCount).toBe(3);
    expect(snapshot.summary.pendingApprovalCount).toBe(2);
    expect(snapshot.nextCheckpoint.type).toBe("review");
    expect(snapshot.nextCheckpoint.title).toBe("Content Plan Review");
    expect(snapshot.nextCheckpoint.advanceCriteria).toContain(
      "Outline and section intent are stable.",
    );
    expect(snapshot.gateStatus.currentGate).toBe("solution");
  });

  it("captures a scenario snapshot with a persisted copy of the active draft", () => {
    const draft = createPursuitDraft(demoOpportunity);
    draft.operatorAssumptions.push({
      id: "assumption-2",
      text: "Operator will assign a single launch supervisor.",
      status: "validated",
      owner: "Proposal manager",
      impactArea: "experience",
    });

    const snapshot = createScenarioSnapshot(
      "Launch-ready variant",
      draft,
      "Baseline scenario with launch control fully staffed.",
    );

    expect(snapshot.name).toBe("Launch-ready variant");
    expect(snapshot.rationale).toContain("Baseline scenario");
    expect(snapshot.draft).toEqual(draft);
    expect(snapshot.summary.currentGate).toBe("qualification");
    expect(snapshot.summary.nextReviewCheckpoint).toContain("Pink Review");
    expect(snapshot.id).toHaveLength(36);
    expect(snapshot.savedAt).toContain("T");
  });

  it("builds review readiness metadata and carries action close conditions into open actions", () => {
    const draft = createPursuitDraft(demoOpportunity);
    draft.approvals[0] = {
      ...draft.approvals[0],
      status: "approved",
      approvedAt: "2026-03-22T20:00:00.000Z",
    };
    draft.approvals[1] = {
      ...draft.approvals[1],
      status: "approved",
      approvedAt: "2026-03-22T20:30:00.000Z",
    };
    draft.reviewCheckpoints[0] = {
      ...draft.reviewCheckpoints[0],
      status: "complete",
      completedAt: "2026-03-22T21:00:00.000Z",
    };
    draft.reviewCheckpoints[1] = {
      ...draft.reviewCheckpoints[1],
      status: "rework-required",
    };
    draft.operatorActions.push({
      id: "action-1",
      title: "Close red review staffing narrative gap",
      owner: "Proposal manager",
      dueLabel: "Before experience approval",
      closeCondition: "Staffing narrative is updated and red-review comments are resolved.",
      stageType: "review",
      linkedStage: "evaluator-review",
      status: "open",
    });

    const snapshot = buildOperatorWorkspaceSnapshot(draft);

    expect(snapshot.summary.completedReviews).toBe(1);
    expect(snapshot.summary.nextReviewCheckpoint).toContain("Red Review");
    expect(snapshot.summary.pendingReviewCount).toBe(2);
    expect(snapshot.openActions).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: "action-1",
          source: "operator",
          closeCondition:
            "Staffing narrative is updated and red-review comments are resolved.",
        }),
        expect.objectContaining({
          id: "review-evaluator-review",
          source: "system",
          title: expect.stringContaining("Close rework"),
        }),
      ]),
    );
    expect(snapshot.gateStatus.nextReviewCheckpoint).toContain("Red Review");
    expect(snapshot.nextCheckpoint.type).toBe("review");
    expect(snapshot.nextCheckpoint.title).toContain("Red Review");
    expect(snapshot.nextCheckpoint.ownerActions).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: "review-evaluator-review",
          title: expect.stringContaining("Close rework"),
        }),
      ]),
    );
  });

  it("falls back to the current gate when reviews for that gate are complete", () => {
    const draft = createPursuitDraft(demoOpportunity);
    draft.approvals[0] = {
      ...draft.approvals[0],
      status: "approved",
      approvedAt: "2026-03-22T20:00:00.000Z",
    };
    draft.reviewCheckpoints[0] = {
      ...draft.reviewCheckpoints[0],
      status: "complete",
      completedAt: "2026-03-22T21:00:00.000Z",
    };

    const snapshot = buildOperatorWorkspaceSnapshot(draft);

    expect(snapshot.nextCheckpoint.type).toBe("gate");
    expect(snapshot.nextCheckpoint.title).toBe("Solution Decision");
    expect(snapshot.nextCheckpoint.advanceCriteria).toContain(
      "The service mix and staffing plan fit the site profile.",
    );
  });

  it("treats an unrecorded qualification call as a blocker at the qualification gate", () => {
    const draft = createPursuitDraft(demoOpportunity);

    const snapshot = buildOperatorWorkspaceSnapshot(draft);

    expect(snapshot.gateStatus.blockingItems).toContain(
      "Qualification decision is not recorded.",
    );
    expect(snapshot.openActions).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: "qualification-decision",
          title: "Record qualification decision",
          source: "system",
        }),
      ]),
    );
    expect(snapshot.nextCheckpoint.type).toBe("gate");
    expect(snapshot.nextCheckpoint.title).toBe("Qualification Decision");
  });

  it("lets the operator override the engine recommendation while preserving the underlying score", () => {
    const draft = createPursuitDraft(demoOpportunity);
    const engineResult = qualifyOpportunity(demoOpportunity);
    draft.qualificationDecision = {
      mode: "override",
      selectedStatus: "no-bid",
      note: "Do not advance until the bid economics improve.",
      decidedAt: "2026-03-23T16:00:00.000Z",
    };

    const snapshot = buildOperatorWorkspaceSnapshot(draft);

    expect(snapshot.experience.qualification.recommendedStatus).toBe(
      engineResult.recommendedStatus,
    );
    expect(snapshot.experience.qualification.status).toBe("no-bid");
    expect(snapshot.summary.status).toBe("no-bid");
    expect(snapshot.gateStatus.blockingItems).not.toContain(
      "Qualification decision is not recorded.",
    );
  });
});

describe("operator workspace persistence", () => {
  it("round-trips a clean workspace state through storage", () => {
    const storage: Record<string, string> = {};
    const state = createWorkspaceState(demoOpportunity);

    saveWorkspaceState(
      {
        getItem(key) {
          return storage[key] ?? null;
        },
        setItem(key, value) {
          storage[key] = value;
        },
      },
      state,
    );

    const loaded = loadWorkspaceState(
      {
        getItem(key) {
          return storage[key] ?? null;
        },
        setItem() {
          return undefined;
        },
      },
      demoOpportunity,
    );

    expect(loaded).toEqual(state);
  });

  it("serializes operator assumptions into the stored payload", () => {
    const storage: Record<string, string> = {};
    const state = createWorkspaceState(demoOpportunity);
    state.activeDraft.operatorAssumptions.push({
      id: "assumption-3",
      text: "Validated insurance certificate will be available at kickoff.",
      status: "open",
      owner: "Finance lead",
      impactArea: "submission",
    });

    saveWorkspaceState(
      {
        getItem(key) {
          return storage[key] ?? null;
        },
        setItem(key, value) {
          storage[key] = value;
        },
      },
      state,
    );

    expect(storage[WORKSPACE_STORAGE_KEY]).toContain("Validated insurance certificate");
    expect(JSON.parse(storage[WORKSPACE_STORAGE_KEY] ?? "{}")).toMatchObject({
      activeDraft: {
        operatorAssumptions: [
          {
            id: "assumption-3",
            text: "Validated insurance certificate will be available at kickoff.",
            status: "open",
            owner: "Finance lead",
            impactArea: "submission",
          },
        ],
      },
    });
  });

  it("persists working story selections through storage round-trip", () => {
    const storage: Record<string, string> = {};
    const state = createWorkspaceState(demoOpportunity);
    state.activeDraft.workingStory = {
      summaryVariantId: "summary-make-the-building-easier-to-manage",
      winThemeIds: ["theme-visible-daytime-support"],
      proofIds: ["proof-executive-floor-response-program"],
      ghostAngleIds: ["ghost-visible-daytime-support"],
      transitionAngleId: "transition-occupied-hours-assurance",
      operatorNotes:
        "Keep the lobby and executive-floor visibility front and center.",
    };

    saveWorkspaceState(
      {
        getItem(key) {
          return storage[key] ?? null;
        },
        setItem(key, value) {
          storage[key] = value;
        },
      },
      state,
    );

    const loaded = loadWorkspaceState(
      {
        getItem(key) {
          return storage[key] ?? null;
        },
        setItem() {
          return undefined;
        },
      },
      demoOpportunity,
    );

    expect(loaded.activeDraft.workingStory).toEqual(
      state.activeDraft.workingStory,
    );
  });

  it("persists buyer story variants and the promoted variant id", () => {
    const storage: Record<string, string> = {};
    const state = createWorkspaceState(demoOpportunity);
    state.activeDraft.buyerStoryVariants = [
      {
        id: "variant-1",
        name: "Executive confidence concept",
        savedAt: "2026-03-23T14:00:00.000Z",
        selection: {
          summaryVariantId: "summary-make-the-building-easier-to-manage",
          winThemeIds: ["theme-visible-daytime-support"],
          proofIds: ["proof-executive-floor-response-program"],
          ghostAngleIds: [],
          transitionAngleId: "transition-occupied-hours-assurance",
          operatorNotes: "Lead with occupied-hours confidence.",
        },
      },
    ];
    state.activeDraft.promotedBuyerStoryVariantId = "variant-1";

    saveWorkspaceState(
      {
        getItem(key) {
          return storage[key] ?? null;
        },
        setItem(key, value) {
          storage[key] = value;
        },
      },
      state,
    );

    const loaded = loadWorkspaceState(
      {
        getItem(key) {
          return storage[key] ?? null;
        },
        setItem() {
          return undefined;
        },
      },
      demoOpportunity,
    );

    expect(loaded.activeDraft.buyerStoryVariants).toEqual(
      state.activeDraft.buyerStoryVariants,
    );
    expect(loaded.activeDraft.promotedBuyerStoryVariantId).toBe("variant-1");
  });

  it("persists qualification decisions through storage round-trip", () => {
    const storage: Record<string, string> = {};
    const state = createWorkspaceState(demoOpportunity);
    state.activeDraft.qualificationDecision = {
      mode: "override",
      selectedStatus: "review",
      note: "Need pricing clarification before we commit to pursue.",
      decidedAt: "2026-03-23T18:00:00.000Z",
    };

    saveWorkspaceState(
      {
        getItem(key) {
          return storage[key] ?? null;
        },
        setItem(key, value) {
          storage[key] = value;
        },
      },
      state,
    );

    const loaded = loadWorkspaceState(
      {
        getItem(key) {
          return storage[key] ?? null;
        },
        setItem() {
          return undefined;
        },
      },
      demoOpportunity,
    );

    expect(loaded.activeDraft.qualificationDecision).toEqual(
      state.activeDraft.qualificationDecision,
    );
  });

  it("persists review checkpoints and operator actions with APMP metadata", () => {
    const storage: Record<string, string> = {};
    const state = createWorkspaceState(demoOpportunity);
    state.activeDraft.reviewCheckpoints[1] = {
      ...state.activeDraft.reviewCheckpoints[1],
      status: "rework-required",
    };
    state.activeDraft.operatorActions.push({
      id: "action-2",
      title: "Resolve export fallback comments",
      owner: "Operations lead",
      dueLabel: "Before final delivery",
      closeCondition: "Export summary matches the approved buyer-facing experience.",
      stageType: "review",
      linkedStage: "gold-readiness-review",
      status: "open",
    });

    saveWorkspaceState(
      {
        getItem(key) {
          return storage[key] ?? null;
        },
        setItem(key, value) {
          storage[key] = value;
        },
      },
      state,
    );

    const saved = JSON.parse(storage[WORKSPACE_STORAGE_KEY] ?? "{}");

    expect(saved.activeDraft.reviewCheckpoints).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ id: "content-plan-review" }),
        expect.objectContaining({
          id: "evaluator-review",
          status: "rework-required",
          apmpLabel: "Red Review",
        }),
      ]),
    );
    expect(saved.activeDraft.operatorActions).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: "action-2",
          closeCondition:
            "Export summary matches the approved buyer-facing experience.",
        }),
      ]),
    );
  });

  it("starts a fresh draft with an empty working story selection", () => {
    const draft = createPursuitDraft(demoOpportunity);

    expect(draft.workingStory).toEqual({
      summaryVariantId: null,
      winThemeIds: [],
      proofIds: [],
      ghostAngleIds: [],
      transitionAngleId: null,
      operatorNotes: "",
    });
    expect(draft.buyerStoryVariants).toEqual([]);
    expect(draft.promotedBuyerStoryVariantId).toBeNull();
  });

  it("fills working story defaults when older stored payloads omit the curation state", () => {
    const state = createWorkspaceState(demoOpportunity);
    const legacyPayload = {
      ...state,
      activeDraft: {
        ...state.activeDraft,
      },
    };

    delete (legacyPayload.activeDraft as { workingStory?: unknown }).workingStory;

    const loaded = loadWorkspaceState(
      {
        getItem() {
          return JSON.stringify(legacyPayload);
        },
        setItem() {
          return undefined;
        },
      },
      demoOpportunity,
    );

    expect(loaded.activeDraft.workingStory).toEqual({
      summaryVariantId: null,
      winThemeIds: [],
      proofIds: [],
      ghostAngleIds: [],
      transitionAngleId: null,
      operatorNotes: "",
    });
    expect(loaded.activeDraft.buyerStoryVariants).toEqual([]);
    expect(loaded.activeDraft.promotedBuyerStoryVariantId).toBeNull();
  });

  it("fills qualification decision defaults when older stored payloads omit them", () => {
    const state = createWorkspaceState(demoOpportunity);
    const legacyPayload = {
      ...state,
      activeDraft: {
        ...state.activeDraft,
      },
    };

    delete (legacyPayload.activeDraft as { qualificationDecision?: unknown })
      .qualificationDecision;

    const loaded = loadWorkspaceState(
      {
        getItem() {
          return JSON.stringify(legacyPayload);
        },
        setItem() {
          return undefined;
        },
      },
      demoOpportunity,
    );

    expect(loaded.activeDraft.qualificationDecision).toEqual({
      mode: "pending",
      selectedStatus: null,
      note: "",
      decidedAt: null,
    });
  });

  it("maps legacy title-based working story payloads into the new ref fields", () => {
    const state = createWorkspaceState(demoOpportunity);
    const legacyPayload = {
      ...state,
      activeDraft: {
        ...state.activeDraft,
        workingStory: {
          summaryVariantTitle: "Switch cleanly, then stabilize",
          winThemeTitles: ["Switch cleanly, improve quickly"],
          proofTitles: ["Corporate campus mobilization"],
          ghostAngleTitles: ["Ghost the seamless-start claim"],
          transitionAngleTitle: "Launch control sprint",
          operatorNotes: "Keep the launch story tight.",
        },
      },
    };

    const loaded = loadWorkspaceState(
      {
        getItem() {
          return JSON.stringify(legacyPayload);
        },
        setItem() {
          return undefined;
        },
      },
      demoOpportunity,
    );

    expect(loaded.activeDraft.workingStory).toEqual({
      summaryVariantId: "Switch cleanly, then stabilize",
      winThemeIds: ["Switch cleanly, improve quickly"],
      proofIds: ["Corporate campus mobilization"],
      ghostAngleIds: ["Ghost the seamless-start claim"],
      transitionAngleId: "Launch control sprint",
      operatorNotes: "Keep the launch story tight.",
    });
  });

  it("falls back to a fresh workspace when stored state is invalid", () => {
    const loaded = loadWorkspaceState(
      {
        getItem() {
          return "{not-valid-json";
        },
        setItem() {
          return undefined;
        },
      },
      demoOpportunity,
    );

    expect(loaded.activeDraft.opportunity.id).toBe(demoOpportunity.id);
    expect(loaded.savedScenarios).toEqual([]);
    expect(loaded.activeDraft.approvals).toHaveLength(3);
  });
});
