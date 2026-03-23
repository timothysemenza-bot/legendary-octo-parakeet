import { useState } from "react";
import type { WorkingStorySelection } from "../../domain/operatorWorkspace";
import type { PursuitIdeaPack } from "../../domain/pursuitIdeaPack";
import type {
  BuyerStoryVariantRecord,
  WorkingStoryBrief,
} from "../../domain/workingStory";

interface WorkingStoryPanelProps {
  ideaPack: PursuitIdeaPack;
  selection: WorkingStorySelection;
  brief: WorkingStoryBrief;
  buyerStoryVariantName: string;
  buyerStoryVariantRecords: BuyerStoryVariantRecord[];
  onSummaryVariantChange: (id: string) => void;
  onWinThemeToggle: (id: string) => void;
  onProofToggle: (id: string) => void;
  onGhostAngleToggle: (id: string) => void;
  onTransitionAngleChange: (id: string) => void;
  onOperatorNotesChange: (value: string) => void;
  onBuyerStoryVariantNameChange: (value: string) => void;
  onSaveBuyerStoryVariant: () => void;
  onLoadBuyerStoryVariant: (variantId: string) => void;
  onPromoteBuyerStoryVariant: (variantId: string) => void;
  onDeleteBuyerStoryVariant: (variantId: string) => void;
  onResetSelections: () => void;
}

function isSelected(values: string[], id: string): boolean {
  return values.includes(id);
}

export function WorkingStoryPanel({
  ideaPack,
  selection,
  brief,
  buyerStoryVariantName,
  buyerStoryVariantRecords,
  onSummaryVariantChange,
  onWinThemeToggle,
  onProofToggle,
  onGhostAngleToggle,
  onTransitionAngleChange,
  onOperatorNotesChange,
  onBuyerStoryVariantNameChange,
  onSaveBuyerStoryVariant,
  onLoadBuyerStoryVariant,
  onPromoteBuyerStoryVariant,
  onDeleteBuyerStoryVariant,
  onResetSelections,
}: WorkingStoryPanelProps) {
  const [copyStatus, setCopyStatus] = useState<"idle" | "copied" | "failed">(
    "idle",
  );

  async function handleCopyBrief() {
    try {
      await navigator.clipboard.writeText(brief.briefText);
      setCopyStatus("copied");
      window.setTimeout(() => setCopyStatus("idle"), 2000);
    } catch {
      setCopyStatus("failed");
      window.setTimeout(() => setCopyStatus("idle"), 2500);
    }
  }

  return (
    <section className="panel working-story-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Working story</p>
          <h2>Curate the live-bid strategy brief</h2>
          <p className="working-story-copy">
            Pin only the pieces you want to carry forward. If you leave a slot
            unpinned, the highest-ranked option stays live.
          </p>
        </div>
        <div className="working-story-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={handleCopyBrief}
          >
            {copyStatus === "copied"
              ? "Memo copied"
              : copyStatus === "failed"
                ? "Copy failed"
                : "Copy memo text"}
          </button>
          <button
            type="button"
            className="secondary-button"
            onClick={onResetSelections}
          >
            Reset curation
          </button>
        </div>
      </div>

      <div className="working-story-layout">
        <div className="working-story-controls">
          <section className="idea-section">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Step 1</p>
                <h3>Pin the opening</h3>
              </div>
            </div>
            <div className="story-option-grid">
              {ideaPack.executiveSummaryVariants.map((variant) => {
                const active =
                  (selection.summaryVariantId ?? brief.summaryVariant.id) ===
                  variant.id;

                return (
                  <article
                    key={variant.id}
                    className={active ? "story-option-card active" : "story-option-card"}
                  >
                    <p className="eyebrow">{variant.title}</p>
                    <p className="idea-statement">{variant.openingLine}</p>
                    <p className="module-rationale">{variant.useWhen}</p>
                    <button
                      type="button"
                      className={active ? "mode-button active" : "mode-button"}
                      onClick={() => onSummaryVariantChange(variant.id)}
                    >
                      {active ? "Pinned opening" : "Pin opening"}
                    </button>
                  </article>
                );
              })}
            </div>
          </section>

          <section className="idea-section">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Step 2</p>
                <h3>Choose the themes and proof</h3>
              </div>
            </div>

            <div className="story-option-grid compact-grid">
              {ideaPack.winThemes.map((theme) => {
                const active =
                  selection.winThemeIds.length === 0
                    ? brief.selectedWinThemes.some((item) => item.id === theme.id)
                    : isSelected(selection.winThemeIds, theme.id);

                return (
                  <article
                    key={theme.id}
                    className={active ? "story-option-card active" : "story-option-card"}
                  >
                    <p className="eyebrow">Win theme</p>
                    <strong>{theme.title}</strong>
                    <p>{theme.customerIssue}</p>
                    <button
                      type="button"
                      className={active ? "mode-button active" : "mode-button"}
                      onClick={() => onWinThemeToggle(theme.id)}
                    >
                      {active ? "Included" : "Include"}
                    </button>
                  </article>
                );
              })}
            </div>

            <div className="story-option-grid compact-grid">
              {ideaPack.proofMatches.map((proof) => {
                const active =
                  selection.proofIds.length === 0
                    ? brief.selectedProofMatches.some((item) => item.id === proof.id)
                    : isSelected(selection.proofIds, proof.id);

                return (
                  <article
                    key={proof.id}
                    className={active ? "story-option-card active" : "story-option-card"}
                  >
                    <p className="eyebrow">Proof</p>
                    <strong>{proof.title}</strong>
                    <p>{proof.metric}</p>
                    <p className="module-rationale">{proof.whereToUse}</p>
                    <button
                      type="button"
                      className={active ? "mode-button active" : "mode-button"}
                      onClick={() => onProofToggle(proof.id)}
                    >
                      {active ? "Included" : "Include"}
                    </button>
                  </article>
                );
              })}
            </div>
          </section>

          <section className="idea-section">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Step 3</p>
                <h3>Shape the contrast and transition</h3>
              </div>
            </div>

            <div className="story-option-grid compact-grid">
              {ideaPack.competitorGhostAngles.length > 0 ? (
                ideaPack.competitorGhostAngles.map((angle) => {
                  const active =
                    selection.ghostAngleIds.length === 0
                      ? brief.selectedGhostAngles.some((item) => item.id === angle.id)
                      : isSelected(selection.ghostAngleIds, angle.id);

                  return (
                    <article
                      key={angle.id}
                      className={active ? "story-option-card active" : "story-option-card"}
                    >
                      <p className="eyebrow">Ghosting angle</p>
                      <strong>{angle.title}</strong>
                      <p>{angle.buyerRisk}</p>
                      <button
                        type="button"
                        className={active ? "mode-button active" : "mode-button"}
                        onClick={() => onGhostAngleToggle(angle.id)}
                      >
                        {active ? "Included" : "Include"}
                      </button>
                    </article>
                  );
                })
              ) : (
                <p className="empty-copy">
                  No competitor ghosting angle is suggested for this pursuit right now.
                </p>
              )}
            </div>

            <div className="story-option-grid compact-grid">
              {ideaPack.transitionAngles.length > 0 ? (
                ideaPack.transitionAngles.map((angle) => {
                  const active =
                    (selection.transitionAngleId ?? brief.selectedTransitionAngle?.id) ===
                    angle.id;

                  return (
                    <article
                      key={angle.id}
                      className={active ? "story-option-card active" : "story-option-card"}
                    >
                      <p className="eyebrow">Transition play</p>
                      <strong>{angle.title}</strong>
                      <p>{angle.bestFit}</p>
                      <button
                        type="button"
                        className={active ? "mode-button active" : "mode-button"}
                        onClick={() => onTransitionAngleChange(angle.id)}
                      >
                        {active ? "Pinned transition" : "Pin transition"}
                      </button>
                    </article>
                  );
                })
              ) : (
                <p className="empty-copy">
                  No transition play is available until the solution shape is stable enough.
                </p>
              )}
            </div>
          </section>

          <section className="idea-section">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Step 4</p>
                <h3>Add operator notes</h3>
              </div>
            </div>
            <textarea
              className="scenario-rationale story-notes-field"
              value={selection.operatorNotes}
              onChange={(event) => onOperatorNotesChange(event.target.value)}
              placeholder="Add the one thing you want to remember before turning this into live bid language."
            />
          </section>
        </div>

        <div className="working-story-brief">
          <article className="story-brief-card spotlight-card">
            <p className="eyebrow">Compact strategy brief</p>
            <h3>{brief.headline}</h3>
            <p className="idea-statement">{brief.summaryVariant.openingLine}</p>
            <ul className="plain-list compact">
              <li>Summary variant: {brief.summaryVariant.title}</li>
              <li>Selected themes: {brief.selectedWinThemes.length}</li>
              <li>Selected proof items: {brief.selectedProofMatches.length}</li>
              <li>Selected ghosting angles: {brief.selectedGhostAngles.length}</li>
            </ul>
          </article>

          <div className="story-brief-sections">
            <article className="story-brief-card">
              <p className="eyebrow">Reinforce</p>
              <ul className="plain-list compact">
                {brief.selectedWinThemes.map((theme) => (
                  <li key={theme.title}>{theme.themeStatement}</li>
                ))}
              </ul>
            </article>

            <article className="story-brief-card">
              <p className="eyebrow">Carry proof</p>
              <ul className="plain-list compact">
                {brief.selectedProofMatches.map((proof) => (
                  <li key={proof.title}>
                    {proof.title}: {proof.metric}
                  </li>
                ))}
              </ul>
            </article>

            {brief.selectedGhostAngles.length > 0 ? (
              <article className="story-brief-card">
                <p className="eyebrow">Ghost carefully</p>
                <ul className="plain-list compact">
                  {brief.selectedGhostAngles.map((angle) => (
                    <li key={angle.title}>{angle.ghostStatement}</li>
                  ))}
                </ul>
              </article>
            ) : (
              <article className="story-brief-card">
                <p className="eyebrow">Ghost carefully</p>
                <p className="empty-copy">
                  Keep the story positive unless the buyer is clearly signaling incumbent
                  frustration or transition anxiety.
                </p>
              </article>
            )}

            {brief.priorityObjections.length > 0 ? (
              <article className="story-brief-card">
                <p className="eyebrow">Answer if challenged</p>
                <ul className="plain-list compact">
                  {brief.priorityObjections.map((objection) => (
                    <li key={objection.concern}>{objection.counterMessage}</li>
                  ))}
                </ul>
              </article>
            ) : (
              <article className="story-brief-card">
                <p className="eyebrow">Answer if challenged</p>
                <p className="empty-copy">
                  No priority objections were surfaced from the current proof and hot-button mix.
                </p>
              </article>
            )}
          </div>

          <article className="story-brief-card">
            <p className="eyebrow">Strategy memo text</p>
            <textarea
              className="story-brief-text"
              value={brief.briefText}
              readOnly
            />
          </article>

          <article className="story-brief-card">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Buyer story variants</p>
                <h3>Save, compare, and promote concept directions</h3>
              </div>
            </div>

            <div className="variant-save-row">
              <input
                type="text"
                value={buyerStoryVariantName}
                onChange={(event) => onBuyerStoryVariantNameChange(event.target.value)}
                placeholder="Name this buyer story direction"
              />
              <button
                type="button"
                className="mode-button active"
                onClick={onSaveBuyerStoryVariant}
              >
                Save variant
              </button>
            </div>

            {buyerStoryVariantRecords.length > 0 ? (
              <div className="variant-card-list">
                {buyerStoryVariantRecords.map((record) => (
                  <article
                    key={record.variant.id}
                    className={
                      record.promoted
                        ? "story-option-card active buyer-variant-card"
                        : "story-option-card buyer-variant-card"
                    }
                  >
                    <div className="variant-card-header">
                      <div>
                        <p className="eyebrow">{record.variant.name}</p>
                        <strong>{record.brief.summaryVariant.title}</strong>
                      </div>
                      {record.promoted ? (
                        <span className="status-chip pursue">Promoted</span>
                      ) : null}
                    </div>
                    <p>{record.conceptSheet.brief90.summary}</p>
                    <div className="pill-row">
                      {record.conceptSheet.brief90.signalChips.map((chip) => (
                        <span key={chip} className="info-pill">
                          {chip}
                        </span>
                      ))}
                    </div>
                    <ul className="plain-list compact">
                      {record.conceptSheet.themeTitles.slice(0, 2).map((theme) => (
                        <li key={theme}>{theme}</li>
                      ))}
                      {record.conceptSheet.proofTitles.slice(0, 1).map((proof) => (
                        <li key={proof}>Proof: {proof}</li>
                      ))}
                    </ul>
                    {record.variant.selection.operatorNotes ? (
                      <p className="module-rationale">
                        Note: {record.variant.selection.operatorNotes}
                      </p>
                    ) : null}
                    <div className="scenario-actions">
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() => onLoadBuyerStoryVariant(record.variant.id)}
                      >
                        Load into curation
                      </button>
                      <button
                        type="button"
                        className={
                          record.promoted ? "mode-button active" : "mode-button"
                        }
                        onClick={() => onPromoteBuyerStoryVariant(record.variant.id)}
                      >
                        {record.promoted ? "Promoted to buyer view" : "Promote"}
                      </button>
                      <button
                        type="button"
                        className="ghost-button"
                        onClick={() => onDeleteBuyerStoryVariant(record.variant.id)}
                      >
                        Delete
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <p className="empty-copy">
                Save the current curation as a named buyer story so you can compare
                multiple directions and promote the strongest concept sheet.
              </p>
            )}
          </article>
        </div>
      </div>
    </section>
  );
}
