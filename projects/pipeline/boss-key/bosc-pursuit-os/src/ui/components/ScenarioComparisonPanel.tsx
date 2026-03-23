import type {
  OperatorWorkspaceSnapshot,
  ScenarioSnapshot,
} from "../../domain/operatorWorkspace";
import { formatCurrency, formatRecommendation } from "../formatters";

interface ScenarioComparisonPanelProps {
  currentSnapshot: OperatorWorkspaceSnapshot;
  currentOpportunityValue: number;
  savedScenarios: ScenarioSnapshot[];
  onDeleteScenario: (scenarioId: string) => void;
  onLoadScenario: (scenarioId: string) => void;
}

function formatSavedAt(value: string): string {
  return new Date(value).toLocaleString();
}

function formatGate(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

export function ScenarioComparisonPanel({
  currentSnapshot,
  currentOpportunityValue,
  savedScenarios,
  onDeleteScenario,
  onLoadScenario,
}: ScenarioComparisonPanelProps) {
  return (
    <section className="panel comparison-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Scenario Comparison</p>
          <h2>Current Draft And Saved Variants</h2>
        </div>
      </div>

      <div className="scenario-grid">
        <article className="scenario-card current">
          <p className="eyebrow">Current draft</p>
          <h3>Live working scenario</h3>
          <div className="scenario-stats">
            <span>{formatRecommendation(currentSnapshot.summary.status)}</span>
            <span>{currentSnapshot.summary.score}/100</span>
            <span>{currentSnapshot.summary.moduleCount} modules</span>
            <span>{currentSnapshot.summary.openAssumptionCount} unresolved assumptions</span>
            <span>{currentSnapshot.summary.completedReviews} reviews complete</span>
            <span>{currentSnapshot.summary.openActionCount} open actions</span>
            <span>{formatCurrency(currentOpportunityValue)}</span>
          </div>
          <div className="scenario-readiness">
            <span>Current gate: {formatGate(currentSnapshot.summary.currentGate)}</span>
            <span>Next review: {currentSnapshot.summary.nextReviewCheckpoint}</span>
            <span>{currentSnapshot.summary.blockerCount} blockers</span>
            <span>{currentSnapshot.summary.pendingApprovalCount} approvals pending</span>
          </div>
        </article>

        {savedScenarios.length === 0 ? (
          <article className="scenario-card">
            <p className="eyebrow">Saved variants</p>
            <h3>No saved scenarios yet</h3>
            <p>
              Save the current draft after you adjust assumptions, approvals, or
              module selections.
            </p>
          </article>
        ) : (
          savedScenarios.map((scenario) => (
            <article key={scenario.id} className="scenario-card">
              <p className="eyebrow">Saved scenario</p>
              <h3>{scenario.name}</h3>
              <p className="scenario-time">{formatSavedAt(scenario.savedAt)}</p>
              <div className="scenario-stats">
                <span>{formatRecommendation(scenario.summary.status)}</span>
                <span>{scenario.summary.score}/100</span>
                <span>{scenario.summary.moduleCount} modules</span>
                <span>{scenario.summary.openAssumptionCount} unresolved assumptions</span>
                <span>{scenario.summary.highRiskCount} high risks</span>
                <span>{scenario.summary.completedReviews} reviews complete</span>
                <span>{scenario.summary.openActionCount} open actions</span>
                <span>
                  {formatCurrency(
                    scenario.draft.opportunity.contract.annualValueEstimate,
                  )}
                </span>
              </div>
              <div className="scenario-readiness">
                <span>Current gate: {formatGate(scenario.summary.currentGate)}</span>
                <span>Next review: {scenario.summary.nextReviewCheckpoint}</span>
                <span>{scenario.summary.blockerCount} blockers</span>
                <span>{scenario.summary.pendingApprovalCount} approvals pending</span>
              </div>
              <p className="scenario-rationale-copy">{scenario.rationale}</p>
              <div className="scenario-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => onLoadScenario(scenario.id)}
                >
                  Load
                </button>
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() => onDeleteScenario(scenario.id)}
                >
                  Delete
                </button>
              </div>
            </article>
          ))
        )}
      </div>
    </section>
  );
}
