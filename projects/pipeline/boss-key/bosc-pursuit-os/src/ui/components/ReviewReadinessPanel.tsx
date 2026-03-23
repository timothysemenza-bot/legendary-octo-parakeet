import type { OperatorWorkspaceSnapshot } from "../../domain/operatorWorkspace";

interface ReviewReadinessPanelProps {
  openActions: OperatorWorkspaceSnapshot["openActions"];
  reviewCheckpoints: OperatorWorkspaceSnapshot["reviewCheckpoints"];
}

export function ReviewReadinessPanel({
  openActions,
  reviewCheckpoints,
}: ReviewReadinessPanelProps) {
  return (
    <section className="panel review-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Readiness tracker</p>
          <h2>How Close This Bid Is To Buyer-Ready</h2>
        </div>
      </div>

      <div className="review-readiness-grid">
        {reviewCheckpoints.map((checkpoint) => {
          const linkedActions = openActions.filter(
            (action) =>
              action.status === "open" &&
              action.stageType === "review" &&
              action.linkedStage === checkpoint.id,
          );

          return (
            <article key={checkpoint.id} className="review-readiness-card">
              <p className="eyebrow">{checkpoint.apmpLabel}</p>
              <h3>{checkpoint.title}</h3>
              <p>{checkpoint.objective}</p>
              <div className="review-status-row">
                <span className="info-pill">{checkpoint.status}</span>
                <span className="info-pill">{checkpoint.dueLabel}</span>
              </div>
              <ul className="review-checklist">
                {checkpoint.exitCriteria.map((criterion) => (
                  <li key={criterion}>{criterion}</li>
                ))}
              </ul>
              <p className="review-action-count">
                {linkedActions.length} linked open action
                {linkedActions.length === 1 ? "" : "s"}
              </p>
              {linkedActions.length > 0 ? (
                <ul className="plain-list compact">
                  {linkedActions.slice(0, 2).map((action) => (
                    <li key={action.id}>
                      {action.title}: {action.closeCondition}
                    </li>
                  ))}
                </ul>
              ) : null}
            </article>
          );
        })}
      </div>

      <div className="review-actions-summary">
        <p className="stack-label">Top open actions</p>
        <ul className="plain-list">
          {openActions
            .filter((action) => action.status === "open")
            .slice(0, 5)
            .map((action) => (
              <li key={action.id}>
                {action.title} ({action.owner}, {action.dueLabel})
              </li>
            ))}
        </ul>
      </div>
    </section>
  );
}
