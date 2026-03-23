import type { OperatorWorkspaceSnapshot } from "../../domain/operatorWorkspace";

interface NextCheckpointPanelProps {
  checkpoint: OperatorWorkspaceSnapshot["nextCheckpoint"];
}

function formatStatus(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1).replaceAll("-", " ");
}

export function NextCheckpointPanel({
  checkpoint,
}: NextCheckpointPanelProps) {
  return (
    <section className="panel checkpoint-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Next checkpoint</p>
          <h2>{checkpoint.title}</h2>
        </div>
        <span className="info-pill">{checkpoint.label}</span>
      </div>

      <div className="checkpoint-grid">
        <article className="checkpoint-card spotlight-card">
          <p className="eyebrow">Current step</p>
          <h3>{formatStatus(checkpoint.status)}</h3>
          <p>{checkpoint.summary}</p>
          <div className="checkpoint-meta">
            <span>{checkpoint.dueLabel}</span>
            <span>{checkpoint.blockers.length} blockers</span>
            <span>{checkpoint.ownerActions.length} owner actions</span>
          </div>
        </article>

        <article className="checkpoint-card">
          <p className="eyebrow">Blockers</p>
          {checkpoint.blockers.length === 0 ? (
            <p className="empty-copy">No blockers are currently stopping this step.</p>
          ) : (
            <ul className="plain-list compact">
              {checkpoint.blockers.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          )}
        </article>

        <article className="checkpoint-card">
          <p className="eyebrow">What must be true</p>
          <ul className="plain-list compact">
            {checkpoint.advanceCriteria.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
      </div>

      <div className="checkpoint-actions">
        <p className="stack-label">Owner actions</p>
        {checkpoint.ownerActions.length === 0 ? (
          <p className="empty-copy">No step-specific actions are open right now.</p>
        ) : (
          <div className="action-list">
            {checkpoint.ownerActions.map((action) => (
              <article key={action.id} className="action-card">
                <div className="action-card-header">
                  <strong>{action.title}</strong>
                  <span>{action.owner}</span>
                </div>
                <div className="action-meta">
                  <span>{action.dueLabel}</span>
                  <span>{formatStatus(action.stageType)}</span>
                </div>
                <p className="action-close-copy">{action.closeCondition}</p>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
