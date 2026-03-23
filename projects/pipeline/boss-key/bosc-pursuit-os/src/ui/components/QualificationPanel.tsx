import type { Opportunity } from "../../domain/opportunity";
import type { QualificationResult } from "../../domain/qualification";
import {
  formatCurrency,
  formatRecommendation,
  formatSeverity,
} from "../formatters";

interface QualificationPanelProps {
  opportunity: Opportunity;
  qualification: QualificationResult;
}

export function QualificationPanel({
  opportunity,
  qualification,
}: QualificationPanelProps) {
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
      </div>

      <div className="content-stack">
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
