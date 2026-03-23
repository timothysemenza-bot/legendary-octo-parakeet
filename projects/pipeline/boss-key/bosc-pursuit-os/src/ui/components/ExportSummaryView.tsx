import { useState } from "react";
import type { ProposalExperience } from "../../domain/proposalExperience";
import type { BuyerStoryConceptSheet } from "../../domain/workingStory";
import {
  formatCurrency,
  formatRecommendation,
  formatPercent,
} from "../formatters";

interface ExportSummaryViewProps {
  conceptSheet?: BuyerStoryConceptSheet | null;
  experience: ProposalExperience;
  packagingStateAvailable?: boolean;
  onDownloadPackagingState?: () => void;
}

export function ExportSummaryView({
  conceptSheet,
  experience,
  packagingStateAvailable = false,
  onDownloadPackagingState,
}: ExportSummaryViewProps) {
  const [exportMode, setExportMode] = useState<"concept" | "summary">(
    conceptSheet ? "concept" : "summary",
  );

  return (
    <section className="export-surface">
      <div className="export-header print-hidden">
        <div>
          <p className="eyebrow dark">Fallback export</p>
          <h2>{conceptSheet ? "Printable Concept Sheet Or Summary" : "Printable Summary View"}</h2>
        </div>
        <div className="export-header-actions">
          {packagingStateAvailable && onDownloadPackagingState ? (
            <button
              type="button"
              className="secondary-button light"
              onClick={onDownloadPackagingState}
            >
              Download packaging state
            </button>
          ) : null}
          {conceptSheet ? (
            <div className="section-nav print-hidden">
              <button
                type="button"
                className={
                  exportMode === "concept"
                    ? "section-nav-button active"
                    : "section-nav-button"
                }
                onClick={() => setExportMode("concept")}
              >
                Concept Sheet
              </button>
              <button
                type="button"
                className={
                  exportMode === "summary"
                    ? "section-nav-button active"
                    : "section-nav-button"
                }
                onClick={() => setExportMode("summary")}
              >
                Summary
              </button>
            </div>
          ) : null}
          <button
            type="button"
            className="secondary-button light"
            onClick={() => window.print()}
          >
            {exportMode === "concept" ? "Print concept sheet" : "Print summary"}
          </button>
        </div>
      </div>

      {conceptSheet && exportMode === "concept" ? (
        <article className="export-card">
          <header className="export-block">
            <p className="eyebrow dark">Promoted concept sheet</p>
            <h3>{conceptSheet.name}</h3>
            <p>{conceptSheet.brief90.summary}</p>
          </header>

          <div className="pill-row export-pill-row">
            {conceptSheet.brief90.signalChips.map((chip) => (
              <span key={chip} className="info-pill export-pill">
                {chip}
              </span>
            ))}
          </div>

          <section className="export-block">
            <h4>90-Second Brief</h4>
            <ul className="plain-list dark">
              {conceptSheet.brief90.decisionPoints.map((point) => (
                <li key={point}>{point}</li>
              ))}
            </ul>
          </section>

          <div className="export-grid">
            {conceptSheet.decisionFeed.map((card) => (
              <section key={card.id} className="export-step">
                <strong>{card.headline}</strong>
                <span>{card.label}</span>
                <p>{card.summary}</p>
                <ul className="plain-list dark">
                  {card.bullets.map((bullet) => (
                    <li key={bullet}>{bullet}</li>
                  ))}
                </ul>
                {card.proof ? <p>{card.proof}</p> : null}
              </section>
            ))}
          </div>

          <section className="export-block">
            <h4>Concept Memo</h4>
            <pre className="concept-sheet-memo">{conceptSheet.memoText}</pre>
          </section>
        </article>
      ) : (
      <article className="export-card">
        <header className="export-block">
          <p className="eyebrow dark">Opportunity</p>
          <h3>{experience.opportunity.opportunityName}</h3>
          <p>
            {experience.opportunity.buyerName} | {experience.opportunity.geography.city},{" "}
            {experience.opportunity.geography.state}
          </p>
        </header>

        <div className="export-grid">
          <section className="export-block">
            <h4>Commercial Snapshot</h4>
            <ul className="plain-list dark">
              <li>
                Annual value:{" "}
                {formatCurrency(experience.opportunity.contract.annualValueEstimate)}
              </li>
              <li>Term: {experience.opportunity.contract.termMonths} months</li>
              <li>
                Target margin:{" "}
                {formatPercent(experience.opportunity.contract.targetGrossMarginPercent)}
              </li>
              <li>Transition: {experience.opportunity.contract.transitionDays} days</li>
            </ul>
          </section>

          <section className="export-block">
            <h4>Qualification</h4>
            <ul className="plain-list dark">
              <li>
                Recommendation: {formatRecommendation(experience.qualification.status)}
              </li>
              <li>Score: {experience.qualification.score}/100</li>
              <li>Risk flags: {experience.qualification.riskFlags.length}</li>
            </ul>
          </section>
        </div>

        {experience.exportSummary.sections.map((section) => (
          <section key={section.title} className="export-block">
            <h4>{section.title}</h4>
            <ul className="plain-list dark">
              {section.items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
        ))}

        <section className="export-block">
          <h4>Staffing and Transition</h4>
          <p>{experience.solution.staffing.summary}</p>
          <div className="export-grid">
            {experience.transitionApproach.milestones.map((milestone) => (
              <article key={milestone.phase} className="export-step">
                <strong>{milestone.phase}</strong>
                <span>{milestone.timing}</span>
                <p>{milestone.detail}</p>
              </article>
            ))}
          </div>
        </section>
      </article>
      )}
    </section>
  );
}
