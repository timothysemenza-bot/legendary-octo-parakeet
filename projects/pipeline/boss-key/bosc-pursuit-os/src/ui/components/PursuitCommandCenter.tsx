import type { OperatorWorkspaceSnapshot } from "../../domain/operatorWorkspace";
import { formatRecommendation } from "../formatters";

interface PursuitCommandCenterProps {
  snapshot: OperatorWorkspaceSnapshot;
}

function dedupe(values: string[]): string[] {
  return Array.from(new Set(values));
}

export function PursuitCommandCenter({
  snapshot,
}: PursuitCommandCenterProps) {
  const priorities = dedupe([
    ...snapshot.experience.qualification.recommendedActions,
    ...snapshot.gateStatus.blockingItems,
    ...snapshot.gateStatus.openActions,
  ]).slice(0, 4);

  const differentiators = snapshot.experience.differentiators.slice(0, 3);

  return (
    <section className="panel command-center">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Pursuit Desk</p>
          <h2>What Improves Win Probability Right Now</h2>
        </div>
        <span className={`status-chip ${snapshot.summary.status}`}>
          {formatRecommendation(snapshot.summary.status)}
        </span>
      </div>

      <div className="command-grid">
        <article className="command-card spotlight-card">
          <p className="eyebrow">Pursuit call</p>
          <h3>{snapshot.experience.overview.headline}</h3>
          <p>{snapshot.experience.overview.recommendation}</p>
          <div className="command-meta">
            <span>{snapshot.summary.score}/100 score</span>
            <span>{snapshot.summary.blockerCount} blockers</span>
            <span>{snapshot.summary.openActionCount} open actions</span>
          </div>
        </article>

        <article className="command-card">
          <p className="eyebrow">Immediate moves</p>
          {priorities.length === 0 ? (
            <p className="empty-copy">
              No urgent moves surfaced on the current assumptions.
            </p>
          ) : (
            <ul className="plain-list compact">
              {priorities.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          )}
        </article>

        <article className="command-card">
          <p className="eyebrow">Buyer promise</p>
          <p>{snapshot.experience.overview.summary}</p>
          <div className="command-meta">
            {differentiators.map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>
        </article>
      </div>
    </section>
  );
}
