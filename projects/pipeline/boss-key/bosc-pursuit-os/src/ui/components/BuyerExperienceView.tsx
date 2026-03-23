import { useState, type ReactNode } from "react";
import type { ProposalExperience } from "../../domain/proposalExperience";
import type { BuyerStoryConceptSheet } from "../../domain/workingStory";

export type ExperienceSection =
  | "overview"
  | "scope"
  | "differentiators"
  | "transition"
  | "proof";

interface BuyerExperienceViewProps {
  activeSection: ExperienceSection;
  conceptSheet?: BuyerStoryConceptSheet | null;
  experience: ProposalExperience;
  onSectionChange: (section: ExperienceSection) => void;
}

const sectionLabels: Array<{
  id: ExperienceSection;
  label: string;
}> = [
  { id: "overview", label: "Overview" },
  { id: "scope", label: "Scope Summary" },
  { id: "differentiators", label: "Differentiators" },
  { id: "transition", label: "Transition" },
  { id: "proof", label: "Proof" },
];

export function BuyerExperienceView({
  activeSection,
  conceptSheet,
  experience,
  onSectionChange,
}: BuyerExperienceViewProps) {
  const [viewMode, setViewMode] = useState<"feed" | "sections">("feed");
  const metrics = [
    {
      label: "Portfolio",
      value: `${experience.opportunity.siteProfile.siteCount} sites`,
    },
    {
      label: "Square Feet",
      value: `${experience.opportunity.siteProfile.totalSquareFeet.toLocaleString()}`,
    },
    {
      label: "Transition",
      value: `${experience.opportunity.contract.transitionDays} days`,
    },
    {
      label: "Occupancy",
      value: experience.opportunity.siteProfile.occupiedHours,
    },
  ];

  let sectionContent: ReactNode;
  if (activeSection === "overview") {
    sectionContent = (
      <div className="section-content-grid">
        <article className="story-card spotlight-card">
          <p className="eyebrow">Buyer-facing summary</p>
          <h2>{experience.overview.headline}</h2>
          <p>{experience.overview.summary}</p>
          <p className="recommendation-copy">{experience.overview.buyerFraming}</p>
        </article>
        <article className="story-card">
          <p className="eyebrow">Positioning</p>
          <h3>Why this reads like a decision environment</h3>
          <p>
            The strongest buyer-facing version should feel fast to scan, easy
            to trust, and deep enough to explore only when a decision-maker
            wants more detail.
          </p>
          <div className="pill-row">
            {experience.brief90.signalChips.map((line) => (
              <span key={line} className="info-pill">
                {line}
              </span>
            ))}
          </div>
        </article>
      </div>
    );
  } else if (activeSection === "scope") {
    sectionContent = (
      <div className="section-content-grid">
        <article className="story-card spotlight-card">
          <p className="eyebrow">Operating model</p>
          <h3>{experience.scopeSummary.operatingModel}</h3>
          <p>{experience.scopeSummary.coveragePlan}</p>
        </article>
        <article className="story-card">
          <p className="eyebrow">Service modules</p>
          <div className="module-list">
            {experience.solution.modules.map((module) => (
              <article key={module.id} className="module-card">
                <div className="module-card-header">
                  <h3>{module.name}</h3>
                  <span className="module-tag">{module.category}</span>
                </div>
                <p>{module.summary}</p>
                <p className="module-rationale">{module.rationale}</p>
              </article>
            ))}
          </div>
        </article>
      </div>
    );
  } else if (activeSection === "differentiators") {
    sectionContent = (
      <div className="section-content-grid single-column">
        <article className="story-card spotlight-card">
          <p className="eyebrow">Differentiators</p>
          <div className="bullet-grid">
            {experience.differentiators.map((item) => (
              <article key={item} className="bullet-card">
                <p>{item}</p>
              </article>
            ))}
          </div>
        </article>
      </div>
    );
  } else if (activeSection === "transition") {
    sectionContent = (
      <div className="section-content-grid">
        <article className="story-card spotlight-card">
          <p className="eyebrow">Transition approach</p>
          <h3>{experience.transitionApproach.title}</h3>
          <p>{experience.transitionApproach.summary}</p>
        </article>
        <article className="story-card">
          <p className="eyebrow">Milestones</p>
          <div className="timeline">
            {experience.transitionApproach.milestones.map((milestone) => (
              <article key={milestone.phase} className="timeline-card">
                <div className="timeline-heading">
                  <h3>{milestone.phase}</h3>
                  <span>{milestone.timing}</span>
                </div>
                <p>{milestone.detail}</p>
              </article>
            ))}
          </div>
        </article>
      </div>
    );
  } else {
    sectionContent = (
      <div className="section-content-grid">
        {experience.proofExamples.map((example) => (
          <article key={example.title} className="story-card proof-card">
            <p className="eyebrow">Proof example</p>
            <h3>{example.title}</h3>
            <strong>{example.metric}</strong>
            <p>{example.description}</p>
          </article>
        ))}
      </div>
    );
  }

  return (
    <section className="experience-surface">
      <div className="metrics-grid">
        {metrics.map((metric) => (
          <article key={metric.label} className="metric-card">
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
          </article>
        ))}
      </div>

      <div className="section-nav experience-view-nav">
        <button
          type="button"
          className={
            viewMode === "feed" ? "section-nav-button active" : "section-nav-button"
          }
          onClick={() => setViewMode("feed")}
        >
          Decision Feed
        </button>
        <button
          type="button"
          className={
            viewMode === "sections"
              ? "section-nav-button active"
              : "section-nav-button"
          }
          onClick={() => setViewMode("sections")}
        >
          Deep Dive
        </button>
      </div>

      {viewMode === "feed" ? (
        <div className="buyer-feed-stack">
          <article className="story-card spotlight-card buyer-brief-card">
            <p className="eyebrow">
              {conceptSheet ? "Promoted concept sheet" : experience.brief90.title}
            </p>
            <h2>{conceptSheet?.name ?? experience.overview.headline}</h2>
            <p className="idea-statement">
              {conceptSheet
                ? conceptSheet.decisionFeed[0]?.summary ?? experience.overview.buyerFraming
                : experience.overview.buyerFraming}
            </p>
            <p>{conceptSheet?.brief90.summary ?? experience.brief90.summary}</p>
            <div className="pill-row">
              {(conceptSheet?.brief90.signalChips ?? experience.brief90.signalChips).map(
                (chip) => (
                <span key={chip} className="info-pill">
                  {chip}
                </span>
                ),
              )}
            </div>
            <ul className="plain-list compact">
              {(conceptSheet?.brief90.decisionPoints ?? experience.brief90.decisionPoints).map(
                (point) => (
                <li key={point}>{point}</li>
                ),
              )}
            </ul>
          </article>

          <div className="buyer-feed-grid">
            {(conceptSheet?.decisionFeed ?? experience.decisionFeed).map((card) => (
              <article
                key={card.id}
                className={`story-card feed-card ${card.tone}`}
              >
                <p className="eyebrow">{card.label}</p>
                <h3>{card.headline}</h3>
                <p>{card.summary}</p>
                <ul className="plain-list compact">
                  {card.bullets.map((bullet) => (
                    <li key={bullet}>{bullet}</li>
                  ))}
                </ul>
                {card.proof ? (
                  <p className="feed-proof">Proof signal: {card.proof}</p>
                ) : null}
              </article>
            ))}
          </div>

          <article className="story-card buyer-scope-card">
            <p className="eyebrow">Service scope</p>
            <h3>What the account team should feel in practice</h3>
            <p>{experience.scopeSummary.coveragePlan}</p>
            <div className="pill-row">
              {experience.scopeSummary.serviceLines.map((line) => (
                <span key={line} className="info-pill">
                  {line}
                </span>
              ))}
            </div>
          </article>
        </div>
      ) : (
      <div className="experience-layout">
        <div className="experience-main">
          <div className="section-nav">
            {sectionLabels.map((section) => (
              <button
                key={section.id}
                type="button"
                className={
                  section.id === activeSection
                    ? "section-nav-button active"
                    : "section-nav-button"
                }
                onClick={() => onSectionChange(section.id)}
              >
                {section.label}
              </button>
            ))}
          </div>

          {sectionContent}
        </div>

        <aside className="side-panel">
          <div className="story-card">
            <p className="eyebrow">Quick scan</p>
            <ul className="plain-list">
              {experience.brief90.decisionPoints.map((point) => (
                <li key={point}>{point}</li>
              ))}
            </ul>
            <p className="recommendation-copy">{experience.overview.buyerFraming}</p>
          </div>
        </aside>
      </div>
      )}
    </section>
  );
}
