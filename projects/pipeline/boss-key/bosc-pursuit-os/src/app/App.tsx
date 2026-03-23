import { useEffect, useState } from "react";
import demoOpportunityJson from "../../inputs/demo-opportunity.json";
import {
  parseOpportunity,
  type Opportunity,
} from "../domain/opportunity";
import type { OpportunityImportResult } from "../domain/opportunityImportResult";
import {
  createOpportunityLibrary,
  createOpportunityRecord,
  type OpportunityLibraryState,
  type OpportunityRecordOrigin,
} from "../domain/opportunityLibrary";
import {
  type ActionStageType,
  type ActionStatus,
  type ApprovalStatus,
  type AssumptionImpactArea,
  createWorkspaceState,
  resetApprovals,
  resetReviewCheckpoints,
  type OperatorAssumptionStatus,
  type OperatorWorkspaceState,
  type ReviewStatus,
} from "../domain/operatorWorkspace";
import {
  createDefaultQualificationDecision,
  type PursuitRecommendation,
} from "../domain/qualification";
import {
  buildOperatorWorkspaceSnapshot,
  createScenarioSnapshot,
} from "../engine/operatorWorkspace";
import { buildPursuitIdeaPack } from "../engine/ideaPackBuilder";
import { buildBuyerStoryConceptSheet } from "../engine/buyerStoryVariantBuilder";
import { buildWorkingStoryBrief } from "../engine/workingStoryBuilder";
import { qualifyOpportunity } from "../engine/qualificationEngine";
import {
  BuyerExperienceView,
  type ExperienceSection,
} from "../ui/components/BuyerExperienceView";
import { ExportSummaryView } from "../ui/components/ExportSummaryView";
import { IdeaEnginePanel } from "../ui/components/IdeaEnginePanel";
import { NextCheckpointPanel } from "../ui/components/NextCheckpointPanel";
import { OpportunityImportReview } from "../ui/components/OpportunityImportReview";
import { OpportunityListView } from "../ui/components/OpportunityListView";
import { OperatorWorkbench } from "../ui/components/OperatorWorkbench";
import { OpportunityWorkbench } from "../ui/components/OpportunityWorkbench";
import { PursuitCommandCenter } from "../ui/components/PursuitCommandCenter";
import { QualificationPanel } from "../ui/components/QualificationPanel";
import { ScenarioComparisonPanel } from "../ui/components/ScenarioComparisonPanel";
import { WorkingStoryPanel } from "../ui/components/WorkingStoryPanel";
import {
  addOpportunityRecord,
  loadOpportunityLibrary,
  replaceActiveWorkspaceState,
  saveOpportunityLibrary,
  selectOpportunityRecord,
} from "../services/opportunityLibraryStorage";
import { importOpportunityForApp } from "../services/importClient";
import { formatCurrency } from "../ui/formatters";
import "./styles.css";

const demoOpportunity = parseOpportunity(demoOpportunityJson);

interface PendingImportState {
  opportunity: Opportunity;
  result: OpportunityImportResult;
}

function createScenarioSuggestion(
  opportunity: Opportunity,
  savedScenarioCount: number,
): string {
  return `${opportunity.buyerName} scenario ${savedScenarioCount}`;
}

function createBuyerStoryVariantSuggestion(
  opportunity: Opportunity,
  savedVariantCount: number,
): string {
  return `${opportunity.buyerName} concept ${savedVariantCount}`;
}

function sanitizeFileNamePart(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function createPackagingStateFileName(
  buyerName: string,
  generatedAt: string,
): string {
  return `${sanitizeFileNamePart(buyerName)}-${generatedAt.slice(0, 10)}-workspace-state.json`;
}

export default function App() {
  const [opportunityLibrary, setOpportunityLibrary] =
    useState<OpportunityLibraryState>(() => {
      if (typeof window === "undefined") {
        return createOpportunityLibrary(
          createOpportunityRecord({
            workspaceState: createWorkspaceState(demoOpportunity),
            origin: "demo",
            sourceLabel: "Demo seed",
          }),
        );
      }

      return loadOpportunityLibrary(window.localStorage, demoOpportunity);
    });
  const [pendingImport, setPendingImport] = useState<PendingImportState | null>(null);
  const [activeView, setActiveView] = useState<"desk" | "buyer" | "export">(
    "desk",
  );
  const [deskView, setDeskView] = useState<
    "ideas" | "intake" | "design" | "workflow" | "scenarios"
  >("ideas");
  const [ideaMode, setIdeaMode] = useState<"generate" | "curate">("curate");
  const [activeSection, setActiveSection] =
    useState<ExperienceSection>("overview");
  const [assumptionDraft, setAssumptionDraft] = useState("");
  const [assumptionImpactArea, setAssumptionImpactArea] =
    useState<AssumptionImpactArea>("solution");
  const [assumptionOwner, setAssumptionOwner] = useState("Operator");
  const [scenarioName, setScenarioName] = useState(() =>
    createScenarioSuggestion(demoOpportunity, 1),
  );
  const [scenarioRationale, setScenarioRationale] = useState("");
  const [buyerStoryVariantName, setBuyerStoryVariantName] = useState(() =>
    createBuyerStoryVariantSuggestion(demoOpportunity, 1),
  );
  const [actionDraftTitle, setActionDraftTitle] = useState("");
  const [actionCloseCondition, setActionCloseCondition] = useState(
    "Work is complete and ready for the linked checkpoint.",
  );
  const [actionOwner, setActionOwner] = useState("Operator");
  const [actionDueLabel, setActionDueLabel] = useState("Before next review");
  const [actionStageType, setActionStageType] =
    useState<ActionStageType>("review");
  const [actionLinkedStage, setActionLinkedStage] = useState("content-plan-review");
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadNotice, setUploadNotice] = useState<string | null>(null);

  const activeRecord =
    opportunityLibrary.records.find(
      (record) => record.id === opportunityLibrary.activeRecordId,
    ) ?? opportunityLibrary.records[0];
  const workspaceState = activeRecord.workspaceState;
  const activeDraft = workspaceState.activeDraft;
  const workspaceSnapshot = buildOperatorWorkspaceSnapshot(activeDraft);
  const experience = workspaceSnapshot.experience;
  const pendingImportQualification = pendingImport
    ? qualifyOpportunity(pendingImport.opportunity)
    : null;

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    saveOpportunityLibrary(window.localStorage, opportunityLibrary);
  }, [opportunityLibrary]);

  function resetRecordScopedInputs(
    opportunity: Opportunity,
    savedScenarioCount: number,
    savedVariantCount: number,
  ) {
    setScenarioName(createScenarioSuggestion(opportunity, savedScenarioCount + 1));
    setBuyerStoryVariantName(
      createBuyerStoryVariantSuggestion(opportunity, savedVariantCount + 1),
    );
    setAssumptionDraft("");
    setScenarioRationale("");
    setActionDraftTitle("");
    setActionCloseCondition("Work is complete and ready for the linked checkpoint.");
  }

  function importOriginFromResult(
    result: OpportunityImportResult,
  ): OpportunityRecordOrigin {
    if (result.extractionMethod === "model" || result.extractionMethod === "heuristic") {
      return "source-files";
    }

    return "structured-json";
  }

  function sourceLabelFromResult(result: OpportunityImportResult): string {
    if (result.extractionMethod === "model") {
      return "Model-backed source import";
    }

    if (result.extractionMethod === "heuristic") {
      return "Heuristic source import";
    }

    return "Structured opportunity JSON";
  }

  const ideaPack = buildPursuitIdeaPack(workspaceSnapshot);
  const workingStoryBrief = buildWorkingStoryBrief(
    workspaceSnapshot,
    ideaPack,
    activeDraft.workingStory,
  );
  const buyerStoryVariantRecords = activeDraft.buyerStoryVariants.map((variant) => {
    const brief = buildWorkingStoryBrief(
      workspaceSnapshot,
      ideaPack,
      variant.selection,
    );

    return {
      variant,
      brief,
      conceptSheet: buildBuyerStoryConceptSheet(
        workspaceSnapshot,
        variant,
        brief,
      ),
      promoted: variant.id === activeDraft.promotedBuyerStoryVariantId,
    };
  });
  const promotedBuyerStoryConceptSheet =
    buyerStoryVariantRecords.find((record) => record.promoted)?.conceptSheet ??
    null;

  function updateActiveWorkspace(
    updater: (workspace: OperatorWorkspaceState) => OperatorWorkspaceState,
  ) {
    setOpportunityLibrary((currentState) => {
      const currentRecord =
        currentState.records.find(
          (record) => record.id === currentState.activeRecordId,
        ) ?? currentState.records[0];

      return replaceActiveWorkspaceState(
        currentState,
        updater(currentRecord.workspaceState),
      );
    });
  }

  function updateDraft(
    updater: (
      draft: OperatorWorkspaceState["activeDraft"],
    ) => OperatorWorkspaceState["activeDraft"],
  ) {
    updateActiveWorkspace((currentState) => ({
      ...currentState,
      activeDraft: updater(currentState.activeDraft),
    }));
  }

  function toggleLimitedSelection(
    values: string[],
    value: string,
    maxCount: number,
  ): string[] {
    if (values.includes(value)) {
      return values.filter((item) => item !== value);
    }

    return [...values, value].slice(-maxCount);
  }

  function handleSelectRecord(recordId: string) {
    const match = opportunityLibrary.records.find((record) => record.id === recordId);

    if (!match) {
      return;
    }

    setOpportunityLibrary((currentState) =>
      selectOpportunityRecord(currentState, recordId),
    );
    resetRecordScopedInputs(
      match.workspaceState.activeDraft.opportunity,
      match.workspaceState.savedScenarios.length,
      match.workspaceState.activeDraft.buyerStoryVariants.length,
    );
    setUploadError(null);
    setUploadNotice(null);
  }

  function handleAddDemoOpportunity() {
    const record = createOpportunityRecord({
      workspaceState: createWorkspaceState(demoOpportunity),
      origin: "demo",
      sourceLabel: "Demo seed",
    });

    setOpportunityLibrary((currentState) => addOpportunityRecord(currentState, record));
    setPendingImport(null);
    resetRecordScopedInputs(demoOpportunity, 0, 0);
    setUploadError(null);
    setUploadNotice("Added a fresh demo opportunity to the local library.");
    setActiveView("desk");
    setDeskView("intake");
  }

  function handlePendingImportChange(nextOpportunity: Opportunity) {
    setPendingImport((currentState) =>
      currentState
        ? {
            ...currentState,
            opportunity: nextOpportunity,
            result: {
              ...currentState.result,
              opportunity: nextOpportunity,
            },
          }
        : currentState,
    );
  }

  function handleCreateOpportunityFromImport() {
    if (!pendingImport) {
      return;
    }

    const record = createOpportunityRecord({
      workspaceState: createWorkspaceState(pendingImport.opportunity),
      origin: importOriginFromResult(pendingImport.result),
      sourceLabel: sourceLabelFromResult(pendingImport.result),
      latestImportResult: pendingImport.result,
    });

    setOpportunityLibrary((currentState) => addOpportunityRecord(currentState, record));
    resetRecordScopedInputs(pendingImport.opportunity, 0, 0);
    setUploadNotice(
      `Created a new opportunity for ${pendingImport.opportunity.buyerName} from the imported draft.`,
    );
    setUploadError(null);
    setPendingImport(null);
    setActiveView("desk");
    setDeskView("intake");
  }

  function handleDiscardPendingImport() {
    setPendingImport(null);
    setUploadError(null);
    setUploadNotice("Discarded the pending imported draft.");
  }

  async function handleImportFiles(files: File[]) {
    try {
      const importedPayload = await importOpportunityForApp(files);

      if (importedPayload.kind === "workspace") {
        const record = createOpportunityRecord({
          workspaceState: importedPayload.workspaceState,
          origin: "workspace-json",
          sourceLabel: "Workspace-state JSON",
        });

        setOpportunityLibrary((currentState) =>
          addOpportunityRecord(currentState, record),
        );
        resetRecordScopedInputs(
          importedPayload.workspaceState.activeDraft.opportunity,
          importedPayload.workspaceState.savedScenarios.length,
          importedPayload.workspaceState.activeDraft.buyerStoryVariants.length,
        );
        setPendingImport(null);
      } else {
        setPendingImport({
          opportunity: importedPayload.opportunity,
          result: importedPayload.importResult,
        });
      }

      setUploadError(null);
      setUploadNotice(importedPayload.message);
      setActiveView("desk");
      setDeskView("intake");
    } catch (error) {
      setUploadError(
        error instanceof Error ? error.message : "Unable to read the uploaded files.",
      );
      setUploadNotice(null);
    }
  }

  function handleOpportunityChange(nextOpportunity: Opportunity) {
    updateDraft((draft) => ({
      ...draft,
      opportunity: nextOpportunity,
      qualificationDecision: createDefaultQualificationDecision(),
      approvals: resetApprovals(draft.approvals),
      reviewCheckpoints: resetReviewCheckpoints(draft.reviewCheckpoints),
    }));
  }

  function handleQualificationDecisionNoteChange(note: string) {
    updateDraft((draft) => ({
      ...draft,
      qualificationDecision: {
        ...draft.qualificationDecision,
        note,
      },
    }));
  }

  function handleUseEngineQualificationDecision() {
    updateDraft((draft) => ({
      ...draft,
      qualificationDecision: {
        mode: "follow-engine",
        selectedStatus: null,
        note: draft.qualificationDecision.note,
        decidedAt: new Date().toISOString(),
      },
    }));
  }

  function handleOverrideQualificationDecision(status: PursuitRecommendation) {
    updateDraft((draft) => ({
      ...draft,
      qualificationDecision: {
        mode: "override",
        selectedStatus: status,
        note: draft.qualificationDecision.note,
        decidedAt: new Date().toISOString(),
      },
    }));
  }

  function handleClearQualificationDecision() {
    updateDraft((draft) => ({
      ...draft,
      qualificationDecision: createDefaultQualificationDecision(),
    }));
  }

  function handleToggleModule(moduleId: string) {
    updateDraft((draft) => {
      const excludedModuleIds = draft.excludedModuleIds.includes(moduleId)
        ? draft.excludedModuleIds.filter((id) => id !== moduleId)
        : [...draft.excludedModuleIds, moduleId];

      return {
        ...draft,
        excludedModuleIds,
        approvals: resetApprovals(draft.approvals),
        reviewCheckpoints: resetReviewCheckpoints(draft.reviewCheckpoints),
      };
    });
  }

  function handleAddAssumption() {
    const value = assumptionDraft.trim();
    if (!value) {
      return;
    }

    updateDraft((draft) => ({
      ...draft,
      operatorAssumptions: [
        ...draft.operatorAssumptions,
        {
          id: globalThis.crypto.randomUUID(),
          text: value,
          status: "open",
          owner: assumptionOwner.trim() || "Operator",
          impactArea: assumptionImpactArea,
        },
      ],
      approvals: resetApprovals(draft.approvals),
      reviewCheckpoints: resetReviewCheckpoints(draft.reviewCheckpoints),
    }));
    setAssumptionDraft("");
  }

  function handleRemoveAssumption(assumptionId: string) {
    updateDraft((draft) => ({
      ...draft,
      operatorAssumptions: draft.operatorAssumptions.filter(
        (assumption) => assumption.id !== assumptionId,
      ),
      approvals: resetApprovals(draft.approvals),
      reviewCheckpoints: resetReviewCheckpoints(draft.reviewCheckpoints),
    }));
  }

  function handleUpdateAssumptionStatus(
    assumptionId: string,
    status: OperatorAssumptionStatus,
  ) {
    updateDraft((draft) => ({
      ...draft,
      operatorAssumptions: draft.operatorAssumptions.map((assumption) =>
        assumption.id === assumptionId ? { ...assumption, status } : assumption,
      ),
    }));
  }

  function handleUpdateApprovalStatus(
    stage: OperatorWorkspaceState["activeDraft"]["approvals"][number]["stage"],
    status: ApprovalStatus,
  ) {
    updateDraft((draft) => ({
      ...draft,
      approvals: draft.approvals.map((approval) =>
        approval.stage !== stage
          ? approval
          : {
              ...approval,
              status,
              approvedAt:
                status === "approved" ? new Date().toISOString() : null,
            },
      ),
    }));
  }

  function handleUpdateReviewStatus(
    checkpointId: OperatorWorkspaceState["activeDraft"]["reviewCheckpoints"][number]["id"],
    status: ReviewStatus,
  ) {
    updateDraft((draft) => ({
      ...draft,
      reviewCheckpoints: draft.reviewCheckpoints.map((checkpoint) =>
        checkpoint.id !== checkpointId
          ? checkpoint
          : {
              ...checkpoint,
              status,
              completedAt:
                status === "complete" ? new Date().toISOString() : null,
            },
      ),
    }));
  }

  function handleAddAction() {
    const title = actionDraftTitle.trim();
    const closeCondition = actionCloseCondition.trim();
    const owner = actionOwner.trim();
    const dueLabel = actionDueLabel.trim();

    if (!title || !closeCondition || !owner || !dueLabel) {
      return;
    }

    updateDraft((draft) => ({
      ...draft,
      operatorActions: [
        ...draft.operatorActions,
        {
          id: globalThis.crypto.randomUUID(),
          title,
          owner,
          dueLabel,
          closeCondition,
          stageType: actionStageType,
          linkedStage: actionLinkedStage,
          status: "open",
        },
      ],
    }));

    setActionDraftTitle("");
    setActionCloseCondition("Work is complete and ready for the linked checkpoint.");
  }

  function handleRemoveAction(actionId: string) {
    updateDraft((draft) => ({
      ...draft,
      operatorActions: draft.operatorActions.filter((action) => action.id !== actionId),
    }));
  }

  function handleUpdateActionStatus(actionId: string, status: ActionStatus) {
    updateDraft((draft) => ({
      ...draft,
      operatorActions: draft.operatorActions.map((action) =>
        action.id === actionId ? { ...action, status } : action,
      ),
    }));
  }

  function handleSaveScenario() {
    const trimmedRationale = scenarioRationale.trim();
    if (!trimmedRationale) {
      return;
    }

    const trimmedName = scenarioName.trim();
    const nextName =
      trimmedName ||
      createScenarioSuggestion(
        activeDraft.opportunity,
        workspaceState.savedScenarios.length + 1,
      );

    const snapshot = createScenarioSnapshot(
      nextName,
      activeDraft,
      trimmedRationale,
    );

    updateActiveWorkspace((currentState) => ({
      ...currentState,
      savedScenarios: [snapshot, ...currentState.savedScenarios],
    }));
    setScenarioName(
      createScenarioSuggestion(
        activeDraft.opportunity,
        workspaceState.savedScenarios.length + 2,
      ),
    );
    setScenarioRationale("");
  }

  function handleSaveBuyerStoryVariant() {
    const trimmedName = buyerStoryVariantName.trim();
    const nextName =
      trimmedName ||
      createBuyerStoryVariantSuggestion(
        activeDraft.opportunity,
        activeDraft.buyerStoryVariants.length + 1,
      );

    updateDraft((draft) => ({
      ...draft,
      buyerStoryVariants: [
        {
          id: globalThis.crypto.randomUUID(),
          name: nextName,
          savedAt: new Date().toISOString(),
          selection: structuredClone(draft.workingStory),
        },
        ...draft.buyerStoryVariants,
      ],
    }));

    setBuyerStoryVariantName(
      createBuyerStoryVariantSuggestion(
        activeDraft.opportunity,
        activeDraft.buyerStoryVariants.length + 2,
      ),
    );
  }

  function handleLoadScenario(scenarioId: string) {
    const match = workspaceState.savedScenarios.find(
      (scenario) => scenario.id === scenarioId,
    );

    if (!match) {
      return;
    }

    updateActiveWorkspace((currentState) => ({
      ...currentState,
      activeDraft: structuredClone(match.draft),
    }));
    setScenarioName(match.name);
    setScenarioRationale(match.rationale);
    setBuyerStoryVariantName(
      createBuyerStoryVariantSuggestion(
        match.draft.opportunity,
        match.draft.buyerStoryVariants.length + 1,
      ),
    );
    setUploadError(null);
    setUploadNotice(null);
  }

  function handleDeleteScenario(scenarioId: string) {
    updateActiveWorkspace((currentState) => ({
      ...currentState,
      savedScenarios: currentState.savedScenarios.filter(
        (scenario) => scenario.id !== scenarioId,
      ),
    }));
  }

  function handleLoadBuyerStoryVariant(variantId: string) {
    const match = activeDraft.buyerStoryVariants.find((variant) => variant.id === variantId);

    if (!match) {
      return;
    }

    updateDraft((draft) => ({
      ...draft,
      workingStory: structuredClone(match.selection),
    }));
    setIdeaMode("curate");
    setActiveView("desk");
  }

  function handlePromoteBuyerStoryVariant(variantId: string) {
    updateDraft((draft) => ({
      ...draft,
      promotedBuyerStoryVariantId: variantId,
    }));
  }

  function handleDeleteBuyerStoryVariant(variantId: string) {
    updateDraft((draft) => ({
      ...draft,
      buyerStoryVariants: draft.buyerStoryVariants.filter(
        (variant) => variant.id !== variantId,
      ),
      promotedBuyerStoryVariantId:
        draft.promotedBuyerStoryVariantId === variantId
          ? null
          : draft.promotedBuyerStoryVariantId,
    }));
  }

  function handleActionStageTypeChange(value: ActionStageType) {
    setActionStageType(value);
    setActionLinkedStage(
      value === "review" ? "content-plan-review" : "qualification",
    );
  }

  function handleSelectSummaryVariant(id: string) {
    updateDraft((draft) => ({
      ...draft,
      workingStory: {
        ...draft.workingStory,
        summaryVariantId: id,
      },
    }));
  }

  function handleToggleWinTheme(id: string) {
    updateDraft((draft) => ({
      ...draft,
      workingStory: {
        ...draft.workingStory,
        winThemeIds: toggleLimitedSelection(
          draft.workingStory.winThemeIds,
          id,
          3,
        ),
      },
    }));
  }

  function handleToggleProof(id: string) {
    updateDraft((draft) => ({
      ...draft,
      workingStory: {
        ...draft.workingStory,
        proofIds: toggleLimitedSelection(
          draft.workingStory.proofIds,
          id,
          3,
        ),
      },
    }));
  }

  function handleToggleGhostAngle(id: string) {
    updateDraft((draft) => ({
      ...draft,
      workingStory: {
        ...draft.workingStory,
        ghostAngleIds: toggleLimitedSelection(
          draft.workingStory.ghostAngleIds,
          id,
          2,
        ),
      },
    }));
  }

  function handleSelectTransitionAngle(id: string) {
    updateDraft((draft) => ({
      ...draft,
      workingStory: {
        ...draft.workingStory,
        transitionAngleId:
          draft.workingStory.transitionAngleId === id ? null : id,
      },
    }));
  }

  function handleWorkingStoryNotesChange(value: string) {
    updateDraft((draft) => ({
      ...draft,
      workingStory: {
        ...draft.workingStory,
        operatorNotes: value,
      },
    }));
  }

  function handleResetWorkingStorySelections() {
    updateDraft((draft) => ({
      ...draft,
      workingStory: {
        summaryVariantId: null,
        winThemeIds: [],
        proofIds: [],
        ghostAngleIds: [],
        transitionAngleId: null,
        operatorNotes: "",
      },
    }));
  }

  function handleDownloadPackagingState() {
    if (!promotedBuyerStoryConceptSheet) {
      return;
    }

    const stateJson = JSON.stringify(workspaceState, null, 2);
    const downloadUrl = URL.createObjectURL(
      new Blob([stateJson], { type: "application/json" }),
    );
    const anchor = document.createElement("a");

    anchor.href = downloadUrl;
    anchor.download = createPackagingStateFileName(
      activeDraft.opportunity.buyerName,
      new Date().toISOString(),
    );
    anchor.click();
    URL.revokeObjectURL(downloadUrl);
  }

  return (
    <div className="app-shell">
      <header className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Boss Key Pursuit Operating System</p>
          <h1>Decide faster, shape a stronger service offer, and give buyers a better pitch</h1>
          <p className="hero-summary">
            This workspace is built to help you win more janitorial bids. Use
            the pursuit desk to pressure-test fit, tighten the operating plan,
            surface blockers, and then switch into the buyer view only when the
            story is strong.
          </p>
        </div>

        <div className="hero-grid">
          <article className="hero-card">
            <span>Current buyer</span>
            <strong>{activeDraft.opportunity.buyerName}</strong>
            <p>{activeDraft.opportunity.opportunityName}</p>
          </article>
          <article className="hero-card">
            <span>Deal shape</span>
            <strong>
              {formatCurrency(activeDraft.opportunity.contract.annualValueEstimate)}
            </strong>
            <p>
              {activeDraft.opportunity.siteProfile.siteCount} sites /{" "}
              {activeDraft.opportunity.siteProfile.totalSquareFeet.toLocaleString()} square
              feet
            </p>
          </article>
          <article className="hero-card accent">
            <span>Pursuit posture</span>
            <strong>{workspaceSnapshot.summary.score}/100</strong>
            <p>{experience.overview.recommendation}</p>
          </article>
          <article className="hero-card">
            <span>Next milestone</span>
            <strong>{workspaceSnapshot.summary.nextReviewCheckpoint}</strong>
            <p>
              {workspaceSnapshot.summary.blockerCount} blockers,{" "}
              {workspaceSnapshot.summary.openActionCount} open actions,{" "}
              {workspaceSnapshot.summary.pendingApprovalCount} decisions pending
            </p>
          </article>
        </div>
      </header>

      <main className="workspace-shell">
        <div className="mode-switcher">
          <button
            type="button"
            className={activeView === "desk" ? "mode-button active" : "mode-button"}
            onClick={() => setActiveView("desk")}
          >
            Pursuit Desk
          </button>
          <button
            type="button"
            className={activeView === "buyer" ? "mode-button active" : "mode-button"}
            onClick={() => setActiveView("buyer")}
          >
            Buyer Experience
          </button>
          <button
            type="button"
            className={activeView === "export" ? "mode-button active" : "mode-button"}
            onClick={() => setActiveView("export")}
          >
            Export Summary
          </button>
        </div>

        {activeView === "desk" ? (
          <section className="desk-shell">
            <PursuitCommandCenter snapshot={workspaceSnapshot} />

            <div className="section-nav desk-section-nav">
              {[
                ["ideas", "Idea Engine"],
                ["intake", "Opportunity"],
                ["design", "Solution Design"],
                ["workflow", "Decisions"],
                ["scenarios", "Scenarios"],
              ].map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  className={
                    deskView === value
                      ? "section-nav-button active"
                      : "section-nav-button"
                  }
                  onClick={() =>
                    setDeskView(
                      value as
                        | "ideas"
                        | "intake"
                        | "design"
                        | "workflow"
                        | "scenarios",
                    )
                  }
                >
                  {label}
                </button>
              ))}
            </div>

            {deskView === "ideas" ? (
              <div className="desk-stack">
                <div className="section-nav story-mode-nav">
                  <button
                    type="button"
                    className={
                      ideaMode === "curate"
                        ? "section-nav-button active"
                        : "section-nav-button"
                    }
                    onClick={() => setIdeaMode("curate")}
                  >
                    Curate Story
                  </button>
                  <button
                    type="button"
                    className={
                      ideaMode === "generate"
                        ? "section-nav-button active"
                        : "section-nav-button"
                    }
                    onClick={() => setIdeaMode("generate")}
                  >
                    Generate Ideas
                  </button>
                </div>

                <div className="desk-grid">
                  <div className="desk-primary">
                    {ideaMode === "curate" ? (
                      <WorkingStoryPanel
                        ideaPack={ideaPack}
                        selection={activeDraft.workingStory}
                        brief={workingStoryBrief}
                        buyerStoryVariantName={buyerStoryVariantName}
                        buyerStoryVariantRecords={buyerStoryVariantRecords}
                        onSummaryVariantChange={handleSelectSummaryVariant}
                        onWinThemeToggle={handleToggleWinTheme}
                        onProofToggle={handleToggleProof}
                        onGhostAngleToggle={handleToggleGhostAngle}
                        onTransitionAngleChange={handleSelectTransitionAngle}
                        onOperatorNotesChange={handleWorkingStoryNotesChange}
                        onBuyerStoryVariantNameChange={setBuyerStoryVariantName}
                        onSaveBuyerStoryVariant={handleSaveBuyerStoryVariant}
                        onLoadBuyerStoryVariant={handleLoadBuyerStoryVariant}
                        onPromoteBuyerStoryVariant={handlePromoteBuyerStoryVariant}
                        onDeleteBuyerStoryVariant={handleDeleteBuyerStoryVariant}
                        onResetSelections={handleResetWorkingStorySelections}
                      />
                    ) : (
                      <IdeaEnginePanel ideaPack={ideaPack} />
                    )}
                  </div>

                  <div className="desk-secondary">
                    <QualificationPanel
                      opportunity={activeDraft.opportunity}
                      qualification={experience.qualification}
                      decision={activeDraft.qualificationDecision}
                      onDecisionNoteChange={handleQualificationDecisionNoteChange}
                      onUseEngineRecommendation={handleUseEngineQualificationDecision}
                      onOverrideStatus={handleOverrideQualificationDecision}
                      onClearDecision={handleClearQualificationDecision}
                    />
                    <NextCheckpointPanel checkpoint={workspaceSnapshot.nextCheckpoint} />
                  </div>
                </div>
              </div>
            ) : null}

            {deskView === "intake" ? (
              <div className="desk-grid">
                <div className="desk-primary intake-stack">
                  <OpportunityListView
                    activeRecordId={activeRecord.id}
                    hasPendingImport={Boolean(pendingImport)}
                    records={opportunityLibrary.records}
                    onSelectRecord={handleSelectRecord}
                  />
                  {pendingImport ? (
                    <OpportunityImportReview
                      opportunity={pendingImport.opportunity}
                      result={pendingImport.result}
                      onOpportunityChange={handlePendingImportChange}
                      onAccept={handleCreateOpportunityFromImport}
                      onDiscard={handleDiscardPendingImport}
                    />
                  ) : (
                    <OpportunityWorkbench
                      opportunity={activeDraft.opportunity}
                      uploadError={uploadError}
                      uploadNotice={uploadNotice}
                      onOpportunityChange={handleOpportunityChange}
                      onLoadDemo={handleAddDemoOpportunity}
                      onImportFiles={handleImportFiles}
                    />
                  )}
                </div>

                <div className="desk-secondary">
                  <QualificationPanel
                    opportunity={pendingImport?.opportunity ?? activeDraft.opportunity}
                    qualification={pendingImportQualification ?? experience.qualification}
                    decision={pendingImport ? undefined : activeDraft.qualificationDecision}
                    onDecisionNoteChange={
                      pendingImport ? undefined : handleQualificationDecisionNoteChange
                    }
                    onUseEngineRecommendation={
                      pendingImport ? undefined : handleUseEngineQualificationDecision
                    }
                    onOverrideStatus={
                      pendingImport ? undefined : handleOverrideQualificationDecision
                    }
                    onClearDecision={
                      pendingImport ? undefined : handleClearQualificationDecision
                    }
                  />
                  {pendingImport ? (
                    <section className="panel">
                      <div className="panel-header">
                        <div>
                          <p className="eyebrow">Creation Gate</p>
                          <h2>Review Before Save</h2>
                        </div>
                      </div>
                      <ul className="plain-list compact">
                        <li>Confirm the imported buyer, scope, value, and transition assumptions.</li>
                        <li>Create a new opportunity record only after the imported draft is acceptable.</li>
                        <li>The current saved pursuit remains unchanged until you accept this draft.</li>
                      </ul>
                    </section>
                  ) : (
                    <NextCheckpointPanel checkpoint={workspaceSnapshot.nextCheckpoint} />
                  )}
                </div>
              </div>
            ) : null}

            {deskView === "design" ? (
              <div className="desk-grid">
                <div className="desk-primary">
                  <section className="panel design-preview-panel">
                    <div className="panel-header">
                      <div>
                        <p className="eyebrow">Solution Direction</p>
                        <h2>Offer Shape And Buyer Story</h2>
                      </div>
                    </div>

                    <div className="content-stack">
                      <div>
                        <p className="stack-label">Operating model</p>
                        <p className="panel-copy">
                          {experience.scopeSummary.operatingModel}
                        </p>
                      </div>

                      <div>
                        <p className="stack-label">Included modules</p>
                        <div className="pill-row">
                          {experience.solution.modules.map((module) => (
                            <span key={module.id} className="info-pill">
                              {module.name}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div>
                        <p className="stack-label">Buyer-facing differentiators</p>
                        <ul className="plain-list compact">
                          {experience.differentiators.slice(0, 4).map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      </div>

                      <div>
                        <p className="stack-label">Transition promise</p>
                        <p className="panel-copy">
                          {experience.transitionApproach.summary}
                        </p>
                      </div>
                    </div>
                  </section>
                </div>

                <div className="desk-secondary">
                  <OperatorWorkbench
                    mode="design"
                    approvals={activeDraft.approvals}
                    reviewCheckpoints={activeDraft.reviewCheckpoints}
                    operatorActions={activeDraft.operatorActions}
                    assumptionDraft={assumptionDraft}
                    assumptionImpactArea={assumptionImpactArea}
                    assumptionOwner={assumptionOwner}
                    actionDraftTitle={actionDraftTitle}
                    actionCloseCondition={actionCloseCondition}
                    actionDueLabel={actionDueLabel}
                    actionOwner={actionOwner}
                    actionStageType={actionStageType}
                    actionLinkedStage={actionLinkedStage}
                    autosaveStatus="Local autosave on"
                    availableModules={workspaceSnapshot.availableModules}
                    excludedModuleIds={activeDraft.excludedModuleIds}
                    operatorAssumptions={activeDraft.operatorAssumptions}
                    scenarioRationale={scenarioRationale}
                    scenarioName={scenarioName}
                    onAddAssumption={handleAddAssumption}
                    onAssumptionDraftChange={setAssumptionDraft}
                    onAssumptionImpactAreaChange={setAssumptionImpactArea}
                    onAssumptionOwnerChange={setAssumptionOwner}
                    onActionDraftTitleChange={setActionDraftTitle}
                    onActionCloseConditionChange={setActionCloseCondition}
                    onActionDueLabelChange={setActionDueLabel}
                    onActionOwnerChange={setActionOwner}
                    onActionStageTypeChange={handleActionStageTypeChange}
                    onActionLinkedStageChange={setActionLinkedStage}
                    onAddAction={handleAddAction}
                    onApprovalStatusChange={handleUpdateApprovalStatus}
                    onReviewStatusChange={handleUpdateReviewStatus}
                    onScenarioNameChange={setScenarioName}
                    onScenarioRationaleChange={setScenarioRationale}
                    onSaveScenario={handleSaveScenario}
                    onToggleModule={handleToggleModule}
                    onRemoveAction={handleRemoveAction}
                    onRemoveAssumption={handleRemoveAssumption}
                    onUpdateActionStatus={handleUpdateActionStatus}
                    onUpdateAssumptionStatus={handleUpdateAssumptionStatus}
                  />
                </div>
              </div>
            ) : null}

            {deskView === "workflow" ? (
              <div className="desk-grid">
                <div className="desk-primary">
                  <NextCheckpointPanel checkpoint={workspaceSnapshot.nextCheckpoint} />
                </div>

                <div className="desk-secondary">
                  <OperatorWorkbench
                    mode="workflow"
                    approvals={activeDraft.approvals}
                    reviewCheckpoints={activeDraft.reviewCheckpoints}
                    operatorActions={activeDraft.operatorActions}
                    assumptionDraft={assumptionDraft}
                    assumptionImpactArea={assumptionImpactArea}
                    assumptionOwner={assumptionOwner}
                    actionDraftTitle={actionDraftTitle}
                    actionCloseCondition={actionCloseCondition}
                    actionDueLabel={actionDueLabel}
                    actionOwner={actionOwner}
                    actionStageType={actionStageType}
                    actionLinkedStage={actionLinkedStage}
                    autosaveStatus="Local autosave on"
                    availableModules={workspaceSnapshot.availableModules}
                    excludedModuleIds={activeDraft.excludedModuleIds}
                    operatorAssumptions={activeDraft.operatorAssumptions}
                    scenarioRationale={scenarioRationale}
                    scenarioName={scenarioName}
                    onAddAssumption={handleAddAssumption}
                    onAssumptionDraftChange={setAssumptionDraft}
                    onAssumptionImpactAreaChange={setAssumptionImpactArea}
                    onAssumptionOwnerChange={setAssumptionOwner}
                    onActionDraftTitleChange={setActionDraftTitle}
                    onActionCloseConditionChange={setActionCloseCondition}
                    onActionDueLabelChange={setActionDueLabel}
                    onActionOwnerChange={setActionOwner}
                    onActionStageTypeChange={handleActionStageTypeChange}
                    onActionLinkedStageChange={setActionLinkedStage}
                    onAddAction={handleAddAction}
                    onApprovalStatusChange={handleUpdateApprovalStatus}
                    onReviewStatusChange={handleUpdateReviewStatus}
                    onScenarioNameChange={setScenarioName}
                    onScenarioRationaleChange={setScenarioRationale}
                    onSaveScenario={handleSaveScenario}
                    onToggleModule={handleToggleModule}
                    onRemoveAction={handleRemoveAction}
                    onRemoveAssumption={handleRemoveAssumption}
                    onUpdateActionStatus={handleUpdateActionStatus}
                    onUpdateAssumptionStatus={handleUpdateAssumptionStatus}
                  />
                </div>
              </div>
            ) : null}

            {deskView === "scenarios" ? (
              <div className="desk-stack">
                <OperatorWorkbench
                  mode="scenarios"
                  approvals={activeDraft.approvals}
                  reviewCheckpoints={activeDraft.reviewCheckpoints}
                  operatorActions={activeDraft.operatorActions}
                  assumptionDraft={assumptionDraft}
                  assumptionImpactArea={assumptionImpactArea}
                  assumptionOwner={assumptionOwner}
                  actionDraftTitle={actionDraftTitle}
                  actionCloseCondition={actionCloseCondition}
                  actionDueLabel={actionDueLabel}
                  actionOwner={actionOwner}
                  actionStageType={actionStageType}
                  actionLinkedStage={actionLinkedStage}
                  autosaveStatus="Local autosave on"
                  availableModules={workspaceSnapshot.availableModules}
                  excludedModuleIds={activeDraft.excludedModuleIds}
                  operatorAssumptions={activeDraft.operatorAssumptions}
                  scenarioRationale={scenarioRationale}
                  scenarioName={scenarioName}
                  onAddAssumption={handleAddAssumption}
                  onAssumptionDraftChange={setAssumptionDraft}
                  onAssumptionImpactAreaChange={setAssumptionImpactArea}
                  onAssumptionOwnerChange={setAssumptionOwner}
                  onActionDraftTitleChange={setActionDraftTitle}
                  onActionCloseConditionChange={setActionCloseCondition}
                  onActionDueLabelChange={setActionDueLabel}
                  onActionOwnerChange={setActionOwner}
                  onActionStageTypeChange={handleActionStageTypeChange}
                  onActionLinkedStageChange={setActionLinkedStage}
                  onAddAction={handleAddAction}
                  onApprovalStatusChange={handleUpdateApprovalStatus}
                  onReviewStatusChange={handleUpdateReviewStatus}
                  onScenarioNameChange={setScenarioName}
                  onScenarioRationaleChange={setScenarioRationale}
                  onSaveScenario={handleSaveScenario}
                  onToggleModule={handleToggleModule}
                  onRemoveAction={handleRemoveAction}
                  onRemoveAssumption={handleRemoveAssumption}
                  onUpdateActionStatus={handleUpdateActionStatus}
                  onUpdateAssumptionStatus={handleUpdateAssumptionStatus}
                />

                <ScenarioComparisonPanel
                  currentSnapshot={workspaceSnapshot}
                  currentOpportunityValue={activeDraft.opportunity.contract.annualValueEstimate}
                  savedScenarios={workspaceState.savedScenarios}
                  onDeleteScenario={handleDeleteScenario}
                  onLoadScenario={handleLoadScenario}
                />
              </div>
            ) : null}
          </section>
        ) : activeView === "buyer" ? (
          <section className="mode-surface">
            <BuyerExperienceView
              activeSection={activeSection}
              conceptSheet={promotedBuyerStoryConceptSheet}
              experience={experience}
              onSectionChange={setActiveSection}
            />
          </section>
        ) : (
          <section className="mode-surface">
            <ExportSummaryView
              conceptSheet={promotedBuyerStoryConceptSheet}
              experience={experience}
              packagingStateAvailable={Boolean(promotedBuyerStoryConceptSheet)}
              onDownloadPackagingState={handleDownloadPackagingState}
            />
          </section>
        )}
      </main>
    </div>
  );
}
