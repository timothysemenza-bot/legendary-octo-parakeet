import type { Opportunity } from "../domain/opportunity";
import type {
  BuyerStoryVariant,
  OperatorWorkspaceState,
  OperatorWorkspaceSnapshot,
} from "../domain/operatorWorkspace";
import type { Brief90, DecisionFeedCard } from "../domain/proposalExperience";
import type {
  BuyerStoryConceptSheet,
  WorkingStoryBrief,
} from "../domain/workingStory";
import { buildBuyerStoryConceptSheet } from "../engine/buyerStoryVariantBuilder";
import { buildPursuitIdeaPack } from "../engine/ideaPackBuilder";
import { buildOperatorWorkspaceSnapshot } from "../engine/operatorWorkspace";
import { buildWorkingStoryBrief } from "../engine/workingStoryBuilder";
import { formatCurrency } from "../ui/formatters";

export interface PackagedPromotedConceptSheet {
  generatedAt: string;
  bundleSlug: string;
  bundleTitle: string;
  opportunity: Opportunity;
  snapshot: OperatorWorkspaceSnapshot;
  promotedVariant: BuyerStoryVariant;
  workingStoryBrief: WorkingStoryBrief;
  conceptSheet: BuyerStoryConceptSheet;
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .replace(/-{2,}/g, "-");
}

function createBundleSlug(opportunity: Opportunity): string {
  return slugify(`${opportunity.buyerName} concept sheet`);
}

function renderSignalChips(signalChips: string[]): string {
  return signalChips
    .map((chip) => `<span class="chip">${escapeHtml(chip)}</span>`)
    .join("");
}

function renderDecisionPoints(points: string[]): string {
  return points
    .map((point) => `<li>${escapeHtml(point)}</li>`)
    .join("");
}

function renderDecisionFeed(cards: DecisionFeedCard[]): string {
  return cards
    .map((card) => {
      const bullets = card.bullets
        .map((bullet) => `<li>${escapeHtml(bullet)}</li>`)
        .join("");
      const proof = card.proof
        ? `<p class="card-proof">${escapeHtml(card.proof)}</p>`
        : "";

      return `
        <article class="feed-card tone-${card.tone}">
          <p class="card-label">${escapeHtml(card.label)}</p>
          <h3>${escapeHtml(card.headline)}</h3>
          <p class="card-summary">${escapeHtml(card.summary)}</p>
          <ul>${bullets}</ul>
          ${proof}
        </article>
      `;
    })
    .join("");
}

function renderList(items: string[], emptyLabel: string): string {
  const values = items.length > 0 ? items : [emptyLabel];

  return values
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join("");
}

function renderMilestones(
  packagedConceptSheet: PackagedPromotedConceptSheet,
): string {
  const { snapshot, workingStoryBrief } = packagedConceptSheet;
  const transitionMoves = workingStoryBrief.selectedTransitionAngle?.moves;

  return snapshot.experience.transitionApproach.milestones
    .slice(0, 3)
    .map((milestone, index) => {
      const detail = transitionMoves?.[index] ?? milestone.detail;

      return `
        <article class="timeline-step">
          <p class="timeline-phase">${escapeHtml(milestone.phase)}</p>
          <strong>${escapeHtml(milestone.timing)}</strong>
          <p>${escapeHtml(detail)}</p>
        </article>
      `;
    })
    .join("");
}

function renderBrief90(brief90: Brief90): string {
  return `
    <section class="brief-panel">
      <div class="panel-header">
        <p class="eyebrow">Buyer-ready brief</p>
        <h2>${escapeHtml(brief90.title)}</h2>
      </div>
      <p class="brief-summary">${escapeHtml(brief90.summary)}</p>
      <div class="chip-row">
        ${renderSignalChips(brief90.signalChips)}
      </div>
      <ul class="decision-points">
        ${renderDecisionPoints(brief90.decisionPoints)}
      </ul>
    </section>
  `;
}

export function buildPackagedPromotedConceptSheet(
  workspaceState: OperatorWorkspaceState,
  generatedAt: string = new Date().toISOString(),
): PackagedPromotedConceptSheet {
  const snapshot = buildOperatorWorkspaceSnapshot(workspaceState.activeDraft);
  const ideaPack = buildPursuitIdeaPack(snapshot);
  const promotedVariant = workspaceState.activeDraft.buyerStoryVariants.find(
    (variant) =>
      variant.id === workspaceState.activeDraft.promotedBuyerStoryVariantId,
  );

  if (!promotedVariant) {
    throw new Error(
      "A promoted buyer story variant is required before packaging a concept sheet.",
    );
  }

  const workingStoryBrief = buildWorkingStoryBrief(
    snapshot,
    ideaPack,
    promotedVariant.selection,
  );
  const conceptSheet = buildBuyerStoryConceptSheet(
    snapshot,
    promotedVariant,
    workingStoryBrief,
  );

  return {
    generatedAt,
    bundleSlug: createBundleSlug(snapshot.experience.opportunity),
    bundleTitle: `${snapshot.experience.opportunity.buyerName} concept sheet`,
    opportunity: snapshot.experience.opportunity,
    snapshot,
    promotedVariant,
    workingStoryBrief,
    conceptSheet,
  };
}

export function renderWorkingStoryBriefMarkdown(
  packagedConceptSheet: PackagedPromotedConceptSheet,
): string {
  return `${packagedConceptSheet.workingStoryBrief.briefText}\n`;
}

export function renderShareableConceptSheetHtml(
  packagedConceptSheet: PackagedPromotedConceptSheet,
): string {
  const { conceptSheet, opportunity, snapshot, workingStoryBrief } = packagedConceptSheet;
  const operatingHighlights = [
    `${opportunity.siteProfile.siteCount} sites across ${opportunity.geography.region}`,
    `${opportunity.siteProfile.totalSquareFeet.toLocaleString()} square feet`,
    `${opportunity.contract.transitionDays}-day transition plan`,
    `${formatCurrency(opportunity.contract.annualValueEstimate)} annual program`,
  ];

  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${escapeHtml(conceptSheet.name)} | Boss Key Pursuit OS</title>
    <style>
      :root {
        color-scheme: light;
        --ink: #13202b;
        --muted: #5c6b78;
        --line: #d6dde3;
        --surface: #f5f7f8;
        --card: #ffffff;
        --accent: #0d6d68;
        --accent-soft: #d7f2ef;
        --signal: #0e7490;
        --confidence: #166534;
        --proof: #7c3aed;
        --transition: #b45309;
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
        color: var(--ink);
        background: linear-gradient(180deg, #eef5f7 0%, #ffffff 28%);
      }

      main {
        width: min(1120px, calc(100vw - 48px));
        margin: 0 auto;
        padding: 40px 0 56px;
      }

      .hero {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 28px;
        padding: 32px;
        box-shadow: 0 24px 70px rgba(19, 32, 43, 0.08);
      }

      .eyebrow {
        margin: 0 0 10px;
        font-size: 12px;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: var(--accent);
        font-weight: 700;
      }

      .hero-grid {
        display: grid;
        grid-template-columns: 1.45fr 0.95fr;
        gap: 24px;
        align-items: start;
      }

      h1,
      h2,
      h3,
      h4,
      p {
        margin-top: 0;
      }

      h1 {
        font-size: clamp(2rem, 4vw, 3.3rem);
        line-height: 1.02;
        margin-bottom: 14px;
      }

      .hero-copy > p:last-child,
      .hero-copy > h1 + p {
        font-size: 1.05rem;
        line-height: 1.65;
        color: var(--muted);
      }

      .hero-proof {
        font-weight: 700;
        color: var(--ink);
      }

      .meta-card,
      .brief-panel,
      .support-card,
      .feed-card,
      .timeline-step {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 22px;
      }

      .meta-card {
        padding: 20px;
        background: var(--surface);
      }

      .meta-card strong,
      .support-card strong {
        display: block;
        font-size: 1rem;
        margin-bottom: 8px;
      }

      .meta-card p,
      .support-card p,
      .timeline-step p,
      .feed-card p {
        color: var(--muted);
        line-height: 1.55;
      }

      .stack {
        display: grid;
        gap: 18px;
      }

      .brief-panel {
        margin-top: 28px;
        padding: 26px;
      }

      .panel-header {
        display: flex;
        justify-content: space-between;
        gap: 16px;
        align-items: start;
      }

      .brief-summary {
        font-size: 1.02rem;
        line-height: 1.65;
      }

      .chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin: 18px 0 20px;
      }

      .chip {
        border-radius: 999px;
        padding: 9px 14px;
        background: var(--accent-soft);
        color: var(--accent);
        font-size: 0.92rem;
        font-weight: 700;
      }

      .decision-points,
      .support-card ul,
      .feed-card ul {
        margin: 0;
        padding-left: 18px;
      }

      .decision-points li,
      .support-card li,
      .feed-card li {
        margin: 0 0 10px;
        line-height: 1.55;
      }

      .section {
        margin-top: 28px;
      }

      .section-header {
        display: flex;
        justify-content: space-between;
        gap: 16px;
        margin-bottom: 16px;
        align-items: end;
      }

      .section-header p {
        color: var(--muted);
        max-width: 54ch;
        margin-bottom: 0;
      }

      .feed-grid,
      .support-grid,
      .timeline {
        display: grid;
        gap: 16px;
      }

      .feed-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }

      .support-grid {
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      }

      .timeline {
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }

      .feed-card,
      .support-card,
      .timeline-step {
        padding: 20px;
      }

      .card-label {
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }

      .tone-signal .card-label {
        color: var(--signal);
      }

      .tone-confidence .card-label {
        color: var(--confidence);
      }

      .tone-proof .card-label {
        color: var(--proof);
      }

      .tone-transition .card-label {
        color: var(--transition);
      }

      .card-summary,
      .card-proof {
        margin-bottom: 14px;
      }

      .card-proof {
        font-weight: 700;
        color: var(--ink);
      }

      .timeline-phase {
        margin-bottom: 6px;
        font-size: 12px;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--accent);
        font-weight: 700;
      }

      footer {
        margin-top: 28px;
        padding-top: 18px;
        border-top: 1px solid var(--line);
        color: var(--muted);
        font-size: 0.9rem;
      }

      @media (max-width: 900px) {
        main {
          width: min(100vw - 24px, 1120px);
          padding-top: 24px;
        }

        .hero,
        .brief-panel,
        .feed-card,
        .support-card,
        .timeline-step,
        .meta-card {
          border-radius: 18px;
        }

        .hero-grid,
        .feed-grid,
        .support-grid,
        .timeline {
          grid-template-columns: 1fr;
        }
      }

      @media print {
        body {
          background: #ffffff;
        }

        main {
          width: 100%;
          padding: 0;
        }

        .hero,
        .brief-panel,
        .feed-card,
        .support-card,
        .timeline-step,
        .meta-card {
          box-shadow: none;
          break-inside: avoid;
        }
      }
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <div class="hero-grid">
          <div class="hero-copy">
            <p class="eyebrow">Boss Key concept sheet</p>
            <h1>${escapeHtml(conceptSheet.name)}</h1>
            <p>${escapeHtml(workingStoryBrief.summaryVariant.openingLine)}</p>
            <p class="hero-proof">${escapeHtml(workingStoryBrief.summaryVariant.proofThread)}</p>
          </div>
          <div class="stack">
            <article class="meta-card">
              <strong>Prepared for ${escapeHtml(opportunity.buyerName)}</strong>
              <p>${escapeHtml(opportunity.opportunityName)}</p>
            </article>
            <article class="meta-card">
              <strong>Service footprint</strong>
              <p>${escapeHtml(operatingHighlights.join(" | "))}</p>
            </article>
            <article class="meta-card">
              <strong>Offer shape</strong>
              <p>${escapeHtml(snapshot.experience.scopeSummary.operatingModel)}</p>
            </article>
          </div>
        </div>

        ${renderBrief90(conceptSheet.brief90)}
      </section>

      <section class="section">
        <div class="section-header">
          <div>
            <p class="eyebrow">Decision feed</p>
            <h2>What ${escapeHtml(opportunity.buyerName)} Should Believe Fast</h2>
          </div>
          <p>This handoff is built to survive a skim, a forwarded email, or a quick buyer meeting without losing the operating story behind it.</p>
        </div>
        <div class="feed-grid">
          ${renderDecisionFeed(conceptSheet.decisionFeed)}
        </div>
      </section>

      <section class="section">
        <div class="section-header">
          <div>
            <p class="eyebrow">Support</p>
            <h2>Why The Story Holds Up</h2>
          </div>
          <p>The concept sheet stays concise, but it still points back to the operating proof, service controls, and objection bridges that make the story believable.</p>
        </div>
        <div class="support-grid">
          <article class="support-card">
            <strong>Service lines</strong>
            <ul>${renderList(snapshot.experience.scopeSummary.serviceLines, "Structured janitorial coverage")}</ul>
          </article>
          <article class="support-card">
            <strong>Theme emphasis</strong>
            <ul>${renderList(conceptSheet.themeTitles, "Service control with visible buyer value")}</ul>
          </article>
          <article class="support-card">
            <strong>Proof signals</strong>
            <ul>${renderList(conceptSheet.proofTitles, "Documented service proof")}</ul>
          </article>
          <article class="support-card">
            <strong>Objection bridge</strong>
            <ul>${renderList(workingStoryBrief.priorityObjections.map((objection) => objection.counterMessage).slice(0, 2), "Lead with visible control and a cleaner launch path.")}</ul>
          </article>
        </div>
      </section>

      <section class="section">
        <div class="section-header">
          <div>
            <p class="eyebrow">Transition</p>
            <h2>What The First Month Looks Like</h2>
          </div>
          <p>${escapeHtml(workingStoryBrief.selectedTransitionAngle?.bestFit ?? snapshot.experience.transitionApproach.summary)}</p>
        </div>
        <div class="timeline">
          ${renderMilestones(packagedConceptSheet)}
        </div>
      </section>

      <footer>
        Generated from Boss Key Pursuit OS on ${escapeHtml(packagedConceptSheet.generatedAt)}. HTML is the shareable primary artifact; PDF is the portable fallback.
      </footer>
    </main>
  </body>
</html>
`;
}
