import type { Opportunity } from "../../domain/opportunity";
import type { OpportunityImportResult } from "../../domain/opportunityImportResult";
import { OpportunityFieldsForm } from "./OpportunityFieldsForm";

interface OpportunityImportReviewProps {
  opportunity: Opportunity;
  result: OpportunityImportResult;
  onOpportunityChange: (nextOpportunity: Opportunity) => void;
  onAccept: () => void;
  onDiscard: () => void;
}

function formatExtractionMethod(
  extractionMethod: OpportunityImportResult["extractionMethod"],
): string {
  if (extractionMethod === "model") {
    return "Model-backed import";
  }

  if (extractionMethod === "structured-json") {
    return "Structured JSON import";
  }

  return "Heuristic draft";
}

export function OpportunityImportReview({
  opportunity,
  result,
  onOpportunityChange,
  onAccept,
  onDiscard,
}: OpportunityImportReviewProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Import Review</p>
          <h2>Confirm The Opportunity Before Kickoff</h2>
        </div>
        <div className="review-action-row">
          <button type="button" className="ghost-button" onClick={onDiscard}>
            Discard Draft
          </button>
          <button type="button" className="secondary-button" onClick={onAccept}>
            Create Opportunity
          </button>
        </div>
      </div>

      <p className="panel-copy">{result.summary}</p>

      <div className="import-review-callouts">
        <article className="import-review-card">
          <span className="muted-label">Import method</span>
          <strong>{formatExtractionMethod(result.extractionMethod)}</strong>
          <p>{result.evidence.length} field evidence snippets captured</p>
        </article>
        <article className="import-review-card">
          <span className="muted-label">Buyer</span>
          <strong>{opportunity.buyerName}</strong>
          <p>{opportunity.opportunityName}</p>
        </article>
        <article className="import-review-card">
          <span className="muted-label">Deal shape</span>
          <strong>
            {opportunity.siteProfile.siteCount} sites /{" "}
            {opportunity.siteProfile.totalSquareFeet.toLocaleString()} sf
          </strong>
          <p>{opportunity.contract.transitionDays} day transition assumption</p>
        </article>
      </div>

      <div className="content-stack">
        {result.warnings.length > 0 ? (
          <div>
            <p className="stack-label">Review flags</p>
            <ul className="plain-list">
              {result.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          </div>
        ) : null}

        {result.assumptions.length > 0 ? (
          <div>
            <p className="stack-label">Imported assumptions</p>
            <ul className="plain-list">
              {result.assumptions.map((assumption) => (
                <li key={assumption}>{assumption}</li>
              ))}
            </ul>
          </div>
        ) : null}

        <div>
          <p className="stack-label">Edit the draft before creation</p>
          <p className="helper-text">
            Boss Key will only create a new opportunity record after you review
            or adjust the imported values.
          </p>
        </div>
      </div>

      <OpportunityFieldsForm
        opportunity={opportunity}
        onOpportunityChange={onOpportunityChange}
      />

      <div className="content-stack">
        <div>
          <p className="stack-label">Source evidence</p>
          {result.evidence.length === 0 ? (
            <p className="empty-copy">
              No field-level evidence was captured for this import path.
            </p>
          ) : (
            <div className="import-evidence-list">
              {result.evidence.map((item) => (
                <article key={`${item.field}-${item.sourceFile}`} className="import-evidence-card">
                  <div className="panel-header">
                    <div>
                      <p className="eyebrow">{item.field}</p>
                      <h3>{item.sourceFile}</h3>
                    </div>
                  </div>
                  <p>{item.snippet}</p>
                </article>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
