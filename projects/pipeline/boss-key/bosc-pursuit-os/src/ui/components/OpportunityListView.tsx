import type { OpportunityRecord } from "../../domain/opportunityLibrary";
import { qualifyOpportunity } from "../../engine/qualificationEngine";
import { formatCurrency, formatRecommendation } from "../formatters";

interface OpportunityListViewProps {
  activeRecordId: string;
  hasPendingImport: boolean;
  records: OpportunityRecord[];
  onSelectRecord: (recordId: string) => void;
}

const dateFormatter = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
});

function formatUpdatedAt(value: string): string {
  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return "Updated recently";
  }

  return `Updated ${dateFormatter.format(parsed)}`;
}

export function OpportunityListView({
  activeRecordId,
  hasPendingImport,
  records,
  onSelectRecord,
}: OpportunityListViewProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Opportunity Library</p>
          <h2>Saved Pursuits</h2>
        </div>
        <span className="autosave-chip">{records.length} saved</span>
      </div>

      <p className="panel-copy">
        Each opportunity keeps its own pursuit draft, scenario set, and review
        state in local storage.
      </p>

      {hasPendingImport ? (
        <p className="helper-text">
          One imported draft is waiting for review before it becomes a saved
          Boss Key opportunity.
        </p>
      ) : null}

      <div className="opportunity-record-list">
        {records.map((record) => {
          const opportunity = record.workspaceState.activeDraft.opportunity;
          const qualification = qualifyOpportunity(opportunity);
          const active = record.id === activeRecordId;

          return (
            <button
              key={record.id}
              type="button"
              className={
                active
                  ? "opportunity-record-card active"
                  : "opportunity-record-card"
              }
              onClick={() => onSelectRecord(record.id)}
            >
              <div className="opportunity-record-header">
                <div>
                  <p className="eyebrow">{opportunity.buyerName}</p>
                  <h3>{opportunity.opportunityName}</h3>
                </div>
                <span className={`status-chip ${qualification.status}`}>
                  {formatRecommendation(qualification.status)}
                </span>
              </div>

              <div className="opportunity-record-meta">
                <span>{formatCurrency(opportunity.contract.annualValueEstimate)}</span>
                <span>{qualification.score}/100</span>
                <span>{record.sourceLabel}</span>
                <span>{formatUpdatedAt(record.updatedAt)}</span>
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}
