import type { Opportunity } from "../../domain/opportunity";
import type {
  QualificationDecision,
  QualificationResult,
  PursuitRecommendation,
} from "../../domain/qualification";
import {
  formatCurrency,
  formatRecommendation,
  formatSeverity,
} from "../formatters";

interface QualificationPanelProps {
  opportunity: Opportunity;
  qualification: QualificationResult;
  decision?: QualificationDecision;
  onDecisionNoteChange?: (note: string) => void;
  onUseEngineRecommendation?: () => void;
  onOverrideStatus?: (status: PursuitRecommendation) => void;
  onClearDecision?: () => void;
}

const decisionTimestampFormatter = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  hour: "numeric",
  minute: "2-digit",
});

const overrideStatuses: PursuitRecommendation[] = ["pursue", "review", "no-bid"];

function formatDecisionTimestamp(value: string | null): string | null {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  return decisionTimestampFormatter.format(parsed);
}

function readRecordedDecisionLabel(
  decision: QualificationDecision | undefined,
  qualification: QualificationResult,
): string {
  if (!decision || decision.mode === "pending") {
    return "Pending operator call";
  }

  if (decision.mode === "follow-engine") {
    return `Follow engine (${formatRecommendation(qualification.recommendedStatus)})`;
  }

  return `Override to ${formatRecommendation(
    decision.selectedStatus ?? qualification.status,
  )}`;
}

export function QualificationPanel({
  opportunity,
  qualification,
  decision,
  onDecisionNoteChange,
  onUseEngineRecommendation,
  onOverrideStatus,
  onClearDecision,
}: QualificationPanelProps) {
  const recordedDecisionLabel = readRecordedDecisionLabel(decision, qualification);
  const decisionTimestamp = formatDecisionTimestamp(decision?.decidedAt ?? null);
  const showDecisionControls = Boolean(
    decision &&
      onDecisionNoteChange &&
      onUseEngineRecommendation &&
      onOverrideStatus &&
      onClearDecision,
  );
  const decisionMode = decision?.mode ?? "pending";
  const decisionNote = decision?.note ?? "";

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Qualification Engine</p>
          <h2>Bid Posture</h2>
        </div>
        <span className={`status-chip ${qualification.status}`}>
          {formatRecommendation(qualification.status)}
        </span>
      </div>

      <div className="score-card">
        <p className="score-value">{qualification.score}</p>
        <div>
          <p className="muted-label">Score</p>
          <p className="score-copy">
            Based on fit, relationship, margin, transition timing, and operating
            complexity.
          </p>
        </div>
      </div>

      <div className="mini-stats">
        <div className="mini-stat">
          <span className="muted-label">Annual value</span>
          <strong>{formatCurrency(opportunity.contract.annualValueEstimate)}</strong>
        </div>
        <div className="mini-stat">
          <span className="muted-label">Transition</span>
          <strong>{opportunity.contract.transitionDays} days</strong>
        </div>
        <div className="mini-stat">
          <span className="muted-label">Engine recommendation</span>
          <strong>{formatRecommendation(qualification.recommendedStatus)}</strong>
        </div>
        <div className="mini-stat">
          <span className="muted-label">Recorded decision</span>
          <strong>{recordedDecisionLabel}</strong>
        </div>
      </div>

      <div className="content-stack">
        {showDecisionControls ? (
          <div>
            <p className="stack-label">Record qualification decision</p>
            <p className="helper-text">
              Capture the actual gate call before the pursuit advances. The engine
              can recommend, but Boss Key should keep the operator-owned decision.
            </p>

            <div className="section-nav qualification-decision-actions">
              <button
                type="button"
                className={
                  decisionMode === "follow-engine"
                    ? "section-nav-button active"
                    : "section-nav-button"
                }
                onClick={() => onUseEngineRecommendation?.()}
              >
                Use engine recommendation
              </button>
              {overrideStatuses.map((status) => (
                <button
                  key={status}
                  type="button"
                  className={
                    decisionMode === "override" && decision?.selectedStatus === status
                      ? "section-nav-button active"
                      : "section-nav-button"
                  }
                  onClick={() => onOverrideStatus?.(status)}
                >
                  Override to {formatRecommendation(status)}
                </button>
              ))}
              <button
                type="button"
                className={
                  decisionMode === "pending"
                    ? "section-nav-button active"
                    : "section-nav-button"
                }
                onClick={() => onClearDecision?.()}
              >
                Clear decision
              </button>
            </div>

            <textarea
              className="scenario-rationale qualification-note"
              value={decisionNote}
              onChange={(event) => onDecisionNoteChange?.(event.target.value)}
              placeholder="Record why we are following or overriding the engine posture."
            />

            {decisionTimestamp ? (
              <p className="helper-text">
                Last recorded {decisionTimestamp}. The live engine recommendation is{" "}
                {formatRecommendation(qualification.recommendedStatus)}.
              </p>
            ) : null}
          </div>
        ) : null}

        <div>
          <p className="stack-label">Score drivers</p>
          <div className="score-breakdown-list">
            {qualification.scoreBreakdown.map((item) => (
              <article key={item.code} className="score-breakdown-card">
                <div className="risk-card-header">
                  <h3>{item.label}</h3>
                  <span
                    className={`score-breakdown-delta ${
                      item.points > 0
                        ? "positive"
                        : item.points < 0
                          ? "negative"
                          : "neutral"
                    }`}
                  >
                    {item.points > 0 ? `+${item.points}` : item.points}
                  </span>
                </div>
                <p>{item.detail}</p>
              </article>
            ))}
          </div>
        </div>

        <div>
          <p className="stack-label">Why the engine landed here</p>
          <ul className="plain-list">
            {qualification.rationale.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        </div>

        <div>
          <p className="stack-label">Risk flags</p>
          {qualification.riskFlags.length === 0 ? (
            <p className="empty-copy">No material risk flags on the current assumptions.</p>
          ) : (
            <div className="risk-list">
              {qualification.riskFlags.map((flag) => (
                <article key={flag.code} className="risk-card">
                  <div className="risk-card-header">
                    <h3>{flag.title}</h3>
                    <span className={`severity-chip ${flag.severity}`}>
                      {formatSeverity(flag.severity)}
                    </span>
                  </div>
                  <p>{flag.detail}</p>
                </article>
              ))}
            </div>
          )}
        </div>

        <div>
          <p className="stack-label">Recommended actions</p>
          <ul className="plain-list">
            {qualification.recommendedActions.map((action) => (
              <li key={action}>{action}</li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
