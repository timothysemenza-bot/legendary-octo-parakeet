import type { OperatorWorkspaceSnapshot } from "../../domain/operatorWorkspace";

interface GateStatusBannerProps {
  gateStatus: OperatorWorkspaceSnapshot["gateStatus"];
}

function formatGate(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

export function GateStatusBanner({ gateStatus }: GateStatusBannerProps) {
  return (
    <section className="panel gate-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Pursuit status</p>
          <h2>Decision Pressure And Blockers</h2>
        </div>
      </div>

      <div className="gate-grid">
        <article className="gate-card spotlight-card">
          <p className="eyebrow">Current decision gate</p>
          <h2>{formatGate(gateStatus.currentGate)}</h2>
          <p>{gateStatus.decisionRequired}</p>
          <span className="info-pill">{gateStatus.nextReviewCheckpoint}</span>
        </article>

        <article className="gate-card">
          <p className="eyebrow">Blocking items</p>
          {gateStatus.blockingItems.length === 0 ? (
            <p className="empty-copy">No active blockers on the current gate.</p>
          ) : (
            <ul className="plain-list">
              {gateStatus.blockingItems.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          )}
        </article>

        <article className="gate-card">
          <p className="eyebrow">Open actions</p>
          <ul className="plain-list">
            {gateStatus.openActions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
      </div>
    </section>
  );
}
