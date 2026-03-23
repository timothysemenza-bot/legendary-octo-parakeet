import {
  ACTION_STAGE_TYPES,
  ACTION_STATUSES,
  APPROVAL_STATUSES,
  ASSUMPTION_IMPACT_AREAS,
  ASSUMPTION_STATUSES,
  type ApprovalCheckpoint,
  type ApprovalStatus,
  type ActionStageType,
  type ActionStatus,
  type OperatorAction,
  type OperatorAssumption,
  type OperatorAssumptionStatus,
  type AssumptionImpactArea,
  REVIEW_STATUSES,
  type ReviewCheckpoint,
  type ReviewStatus,
} from "../../domain/operatorWorkspace";
import type { SolutionModule } from "../../domain/solution";

interface OperatorWorkbenchProps {
  mode?: "all" | "design" | "workflow" | "scenarios";
  actionCloseCondition: string;
  actionDraftTitle: string;
  actionDueLabel: string;
  actionLinkedStage: string;
  actionOwner: string;
  actionStageType: ActionStageType;
  assumptionDraft: string;
  assumptionImpactArea: AssumptionImpactArea;
  assumptionOwner: string;
  autosaveStatus: string;
  approvals: ApprovalCheckpoint[];
  availableModules: SolutionModule[];
  excludedModuleIds: string[];
  operatorActions: OperatorAction[];
  operatorAssumptions: OperatorAssumption[];
  reviewCheckpoints: ReviewCheckpoint[];
  scenarioRationale: string;
  scenarioName: string;
  onActionCloseConditionChange: (value: string) => void;
  onActionDraftTitleChange: (value: string) => void;
  onActionDueLabelChange: (value: string) => void;
  onActionLinkedStageChange: (value: string) => void;
  onActionOwnerChange: (value: string) => void;
  onActionStageTypeChange: (value: ActionStageType) => void;
  onAddAssumption: () => void;
  onAddAction: () => void;
  onAssumptionDraftChange: (value: string) => void;
  onAssumptionImpactAreaChange: (value: AssumptionImpactArea) => void;
  onAssumptionOwnerChange: (value: string) => void;
  onApprovalStatusChange: (
    stage: ApprovalCheckpoint["stage"],
    status: ApprovalStatus,
  ) => void;
  onReviewStatusChange: (
    checkpointId: ReviewCheckpoint["id"],
    status: ReviewStatus,
  ) => void;
  onScenarioNameChange: (value: string) => void;
  onScenarioRationaleChange: (value: string) => void;
  onSaveScenario: () => void;
  onToggleModule: (moduleId: string) => void;
  onRemoveAction: (actionId: string) => void;
  onRemoveAssumption: (assumptionId: string) => void;
  onUpdateActionStatus: (actionId: string, status: ActionStatus) => void;
  onUpdateAssumptionStatus: (
    assumptionId: string,
    status: OperatorAssumptionStatus,
  ) => void;
}

function formatStageLabel(stage: ApprovalCheckpoint["stage"]): string {
  return stage.charAt(0).toUpperCase() + stage.slice(1);
}

export function OperatorWorkbench({
  mode = "all",
  actionCloseCondition,
  actionDraftTitle,
  actionDueLabel,
  actionLinkedStage,
  actionOwner,
  actionStageType,
  approvals,
  assumptionDraft,
  assumptionImpactArea,
  assumptionOwner,
  autosaveStatus,
  availableModules,
  excludedModuleIds,
  operatorActions,
  operatorAssumptions,
  reviewCheckpoints,
  scenarioRationale,
  scenarioName,
  onActionCloseConditionChange,
  onActionDraftTitleChange,
  onActionDueLabelChange,
  onActionLinkedStageChange,
  onActionOwnerChange,
  onActionStageTypeChange,
  onAddAssumption,
  onAddAction,
  onAssumptionDraftChange,
  onAssumptionImpactAreaChange,
  onAssumptionOwnerChange,
  onApprovalStatusChange,
  onReviewStatusChange,
  onScenarioNameChange,
  onScenarioRationaleChange,
  onSaveScenario,
  onToggleModule,
  onRemoveAction,
  onRemoveAssumption,
  onUpdateActionStatus,
  onUpdateAssumptionStatus,
}: OperatorWorkbenchProps) {
  const showDesign = mode === "all" || mode === "design";
  const showWorkflow = mode === "all" || mode === "workflow";
  const showScenarios = mode === "all" || mode === "scenarios";
  const linkedStageOptions =
    actionStageType === "review"
      ? reviewCheckpoints.map((checkpoint) => ({
          value: checkpoint.id,
          label: checkpoint.title,
        }))
      : approvals.map((approval) => ({
          value: approval.stage,
          label: formatStageLabel(approval.stage),
        }));

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Operator Layer</p>
          <h2>Workbench Controls</h2>
        </div>
        <span className="autosave-chip">{autosaveStatus}</span>
      </div>

      {showWorkflow ? (
        <details className="operator-group" open>
          <summary className="operator-group-summary">Decision gates</summary>
          <div className="operator-section">
            <div className="approval-grid">
              {approvals.map((approval) => {
                return (
                  <article
                    key={approval.stage}
                    className={
                      approval.status === "approved"
                        ? "approval-card approved"
                        : approval.status === "rejected"
                          ? "approval-card rejected"
                          : approval.status === "rework-required"
                            ? "approval-card rework"
                            : "approval-card"
                    }
                  >
                    <strong>{formatStageLabel(approval.stage)}</strong>
                    <span>
                      {approval.status === "approved"
                        ? "Approved"
                        : approval.status === "rework-required"
                          ? "Needs rework"
                          : approval.status === "rejected"
                            ? "Rejected"
                            : "Pending approval"}
                    </span>
                    <select
                      value={approval.status}
                      onChange={(event) =>
                        onApprovalStatusChange(
                          approval.stage,
                          event.target.value as ApprovalStatus,
                        )
                      }
                    >
                      {APPROVAL_STATUSES.map((status) => (
                        <option key={status} value={status}>
                          {status}
                        </option>
                      ))}
                    </select>
                  </article>
                );
              })}
            </div>
          </div>
        </details>
      ) : null}

      {showWorkflow ? (
        <details className="operator-group" open>
          <summary className="operator-group-summary">Review plan</summary>
          <div className="operator-section">
            <div className="review-grid">
              {reviewCheckpoints.map((checkpoint) => (
                <article key={checkpoint.id} className="review-card">
                  <p className="eyebrow">{checkpoint.apmpLabel}</p>
                  <strong>{checkpoint.title}</strong>
                  <p>{checkpoint.objective}</p>
                  <div className="review-card-meta">
                    <span>{checkpoint.dueLabel}</span>
                  </div>
                  <ul className="review-checklist">
                    {checkpoint.exitCriteria.map((criterion) => (
                      <li key={criterion}>{criterion}</li>
                    ))}
                  </ul>
                  <select
                    value={checkpoint.status}
                    onChange={(event) =>
                      onReviewStatusChange(
                        checkpoint.id,
                        event.target.value as ReviewStatus,
                      )
                    }
                  >
                    {REVIEW_STATUSES.map((status) => (
                      <option key={status} value={status}>
                        {status}
                      </option>
                    ))}
                  </select>
                </article>
              ))}
            </div>
          </div>
        </details>
      ) : null}

      {showDesign ? (
        <details className="operator-group">
          <summary className="operator-group-summary">
            Assumptions and constraints
          </summary>
          <div className="operator-section">
            <div className="assumption-entry">
              <input
                type="text"
                placeholder="Add an operator assumption or caveat"
                value={assumptionDraft}
                onChange={(event) => onAssumptionDraftChange(event.target.value)}
              />
              <input
                type="text"
                placeholder="Owner"
                value={assumptionOwner}
                onChange={(event) => onAssumptionOwnerChange(event.target.value)}
              />
              <select
                value={assumptionImpactArea}
                onChange={(event) =>
                  onAssumptionImpactAreaChange(
                    event.target.value as AssumptionImpactArea,
                  )
                }
              >
                {ASSUMPTION_IMPACT_AREAS.map((area) => (
                  <option key={area} value={area}>
                    {area}
                  </option>
                ))}
              </select>
              <button type="button" className="secondary-button" onClick={onAddAssumption}>
                Add
              </button>
            </div>

            {operatorAssumptions.length === 0 ? (
              <p className="empty-copy">No operator-added assumptions yet.</p>
            ) : (
              <div className="assumption-list">
                {operatorAssumptions.map((assumption) => (
                  <article key={assumption.id} className="assumption-card">
                    <p>{assumption.text}</p>
                    <div className="assumption-meta">
                      <span>{assumption.owner}</span>
                      <span>{assumption.impactArea}</span>
                    </div>
                    <div className="assumption-actions">
                      <select
                        value={assumption.status}
                        onChange={(event) =>
                          onUpdateAssumptionStatus(
                            assumption.id,
                            event.target.value as OperatorAssumptionStatus,
                          )
                        }
                      >
                        {ASSUMPTION_STATUSES.map((status) => (
                          <option key={status} value={status}>
                            {status}
                          </option>
                        ))}
                      </select>
                      <button
                        type="button"
                        className="ghost-button"
                        onClick={() => onRemoveAssumption(assumption.id)}
                      >
                        Remove
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </div>
        </details>
      ) : null}

      {showDesign ? (
        <details className="operator-group">
          <summary className="operator-group-summary">Solution options</summary>
          <div className="operator-section">
            <div className="module-override-list">
              {availableModules.map((module) => {
                const included = !excludedModuleIds.includes(module.id);

                return (
                  <label key={module.id} className="module-toggle">
                    <input
                      type="checkbox"
                      checked={included}
                      onChange={() => onToggleModule(module.id)}
                    />
                    <div>
                      <strong>{module.name}</strong>
                      <p>{module.summary}</p>
                    </div>
                  </label>
                );
              })}
            </div>
          </div>
        </details>
      ) : null}

      {showWorkflow ? (
        <details className="operator-group" open>
          <summary className="operator-group-summary">Action log</summary>
          <div className="operator-section">
            <div className="action-entry">
              <input
                type="text"
                placeholder="Action title"
                value={actionDraftTitle}
                onChange={(event) => onActionDraftTitleChange(event.target.value)}
              />
              <input
                type="text"
                placeholder="Owner"
                value={actionOwner}
                onChange={(event) => onActionOwnerChange(event.target.value)}
              />
              <input
                type="text"
                placeholder="Due label"
                value={actionDueLabel}
                onChange={(event) => onActionDueLabelChange(event.target.value)}
              />
              <select
                value={actionStageType}
                onChange={(event) =>
                  onActionStageTypeChange(event.target.value as ActionStageType)
                }
              >
                {ACTION_STAGE_TYPES.map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
              <select
                value={actionLinkedStage}
                onChange={(event) => onActionLinkedStageChange(event.target.value)}
              >
                {linkedStageOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <button type="button" className="secondary-button" onClick={onAddAction}>
                Add Action
              </button>
            </div>
            <input
              className="action-close-condition"
              type="text"
              placeholder="Close condition"
              value={actionCloseCondition}
              onChange={(event) => onActionCloseConditionChange(event.target.value)}
            />

            {operatorActions.length === 0 ? (
              <p className="empty-copy">No operator-owned actions yet.</p>
            ) : (
              <div className="action-list">
                {operatorActions.map((action) => (
                  <article key={action.id} className="action-card">
                    <div className="action-card-header">
                      <strong>{action.title}</strong>
                      <span>{action.linkedStage}</span>
                    </div>
                    <div className="action-meta">
                      <span>{action.owner}</span>
                      <span>{action.dueLabel}</span>
                    </div>
                    <p className="action-close-copy">{action.closeCondition}</p>
                    <div className="assumption-actions">
                      <select
                        value={action.status}
                        onChange={(event) =>
                          onUpdateActionStatus(
                            action.id,
                            event.target.value as ActionStatus,
                          )
                        }
                      >
                        {ACTION_STATUSES.map((status) => (
                          <option key={status} value={status}>
                            {status}
                          </option>
                        ))}
                      </select>
                      <button
                        type="button"
                        className="ghost-button"
                        onClick={() => onRemoveAction(action.id)}
                      >
                        Remove
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </div>
        </details>
      ) : null}

      {showScenarios ? (
        <details className="operator-group">
          <summary className="operator-group-summary">Scenario checkpoints</summary>
          <div className="operator-section">
            <div className="scenario-save-row">
              <input
                type="text"
                value={scenarioName}
                onChange={(event) => onScenarioNameChange(event.target.value)}
              />
              <button
                type="button"
                className="secondary-button"
                onClick={onSaveScenario}
                disabled={scenarioRationale.trim().length === 0}
              >
                Save Scenario
              </button>
            </div>
            <textarea
              className="scenario-rationale"
              placeholder="Why does this scenario exist? Capture the decision basis."
              value={scenarioRationale}
              onChange={(event) => onScenarioRationaleChange(event.target.value)}
            />
          </div>
        </details>
      ) : null}
    </section>
  );
}
