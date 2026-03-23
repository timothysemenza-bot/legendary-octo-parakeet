import type { PursuitIdeaPack } from "../../domain/pursuitIdeaPack";
import { formatRecommendation } from "../formatters";

interface IdeaEnginePanelProps {
  ideaPack: PursuitIdeaPack;
}

export function IdeaEnginePanel({ ideaPack }: IdeaEnginePanelProps) {
  return (
    <section className="panel idea-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Idea engine</p>
          <h2>Operator Strategy Pack</h2>
        </div>
        <span className={`status-chip ${ideaPack.strategyMemo.pursuitCall}`}>
          {formatRecommendation(ideaPack.strategyMemo.pursuitCall)}
        </span>
      </div>

      <div className="idea-hero">
        <article className="idea-hero-card spotlight-card">
          <p className="eyebrow">Unifying concept</p>
          <h3>{ideaPack.strategyMemo.unifyingConcept}</h3>
          <p>{ideaPack.strategyMemo.elevatorPitch}</p>
        </article>
        <article className="idea-hero-card">
          <p className="eyebrow">Priorities</p>
          <ul className="plain-list compact">
            {ideaPack.strategyMemo.priorities.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
      </div>

      <div className="idea-section">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Buyer hot buttons</p>
            <h3>What this janitorial bid is really about</h3>
          </div>
        </div>
        <div className="idea-grid">
          {ideaPack.hotButtons.map((hotButton) => (
            <article key={hotButton.key} className="idea-card">
              <p className="eyebrow">
                {hotButton.weight >= 6 ? "Primary hot button" : "Secondary hot button"}
              </p>
              <strong>{hotButton.title}</strong>
              <p>{hotButton.buyerSignal}</p>
              <ul className="plain-list compact">
                <li>Win leverage: {hotButton.winLeverage}</li>
                <li>Proof focus: {hotButton.proofFocus}</li>
                <li>Signals: {hotButton.sourceSignals.join(" / ")}</li>
              </ul>
            </article>
          ))}
        </div>
      </div>

      <div className="idea-section">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Win themes</p>
            <h3>Theme statements worth testing</h3>
          </div>
        </div>
        <div className="idea-grid">
          {ideaPack.winThemes.map((theme) => (
            <article key={theme.title} className="idea-card">
              <p className="eyebrow">{theme.title}</p>
              <p className="idea-statement">{theme.themeStatement}</p>
              <ul className="plain-list compact">
                <li>Customer issue: {theme.customerIssue}</li>
                <li>Differentiator: {theme.differentiator}</li>
                <li>Proof: {theme.proofPoint}</li>
              </ul>
            </article>
          ))}
        </div>
      </div>

      <div className="idea-section">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Competitive angles</p>
            <h3>Ghosting moves and objection counters</h3>
          </div>
        </div>
        <div className="idea-grid">
          {ideaPack.competitorGhostAngles.map((item) => (
            <article key={item.title} className="idea-card">
              <p className="eyebrow">{item.title}</p>
              <strong>{item.buyerRisk}</strong>
              <p>{item.ghostStatement}</p>
              <ul className="plain-list compact">
                <li>Boss Key counter: {item.bossKeyCounter}</li>
                <li>Proof to use: {item.proofToUse}</li>
              </ul>
            </article>
          ))}
        </div>
        <div className="idea-grid">
          {ideaPack.buyerConcerns.map((item) => (
            <article key={item.concern} className="idea-card">
              <p className="eyebrow">Buyer objection</p>
              <strong>{item.concern}</strong>
              <p>{item.whyItMatters}</p>
              <ul className="plain-list compact">
                <li>Response angle: {item.responseAngle}</li>
                <li>Counter: {item.counterMessage}</li>
                <li>Proof to use: {item.proofToUse}</li>
              </ul>
            </article>
          ))}
        </div>
      </div>

      <div className="idea-section">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Offer construction</p>
            <h3>Differentiators, proof, and transition plays</h3>
          </div>
        </div>
        <div className="idea-grid">
          {ideaPack.differentiatorOptions.map((item) => (
            <article key={item.title} className="idea-card">
              <p className="eyebrow">{item.title}</p>
              <strong>{item.benefit}</strong>
              <p>{item.feature}</p>
              <p className="module-rationale">{item.whyItWins}</p>
            </article>
          ))}
        </div>
        <div className="idea-grid">
          {ideaPack.transitionAngles.map((angle) => (
            <article key={angle.title} className="idea-card">
              <p className="eyebrow">{angle.title}</p>
              <p>{angle.bestFit}</p>
              <ul className="plain-list compact">
                {angle.moves.map((move) => (
                  <li key={move}>{move}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>
        <div className="idea-grid">
          {ideaPack.proofMatches.map((item) => (
            <article key={item.title} className="idea-card">
              <p className="eyebrow">Proof match</p>
              <strong>{item.title}</strong>
              <p>{item.metric}</p>
              <ul className="plain-list compact">
                <li>Hot button: {item.hotButton}</li>
                <li>{item.whyItFits}</li>
                <li>{item.strength}</li>
                <li>{item.whereToUse}</li>
              </ul>
            </article>
          ))}
        </div>
      </div>

      <div className="idea-section">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Executive summary variants</p>
            <h3>Three strong ways to frame the pursuit</h3>
          </div>
        </div>
        <div className="idea-grid">
          {ideaPack.executiveSummaryVariants.map((item) => (
            <article key={item.title} className="idea-card">
              <p className="eyebrow">{item.title}</p>
              <p className="idea-statement">{item.openingLine}</p>
              <ul className="plain-list compact">
                {item.customerDrivers.map((driver) => (
                  <li key={driver}>{driver}</li>
                ))}
              </ul>
              <p>{item.solutionFrame}</p>
              <p>{item.proofThread}</p>
              <p>{item.close}</p>
              <p className="module-rationale">{item.useWhen}</p>
            </article>
          ))}
        </div>
      </div>

      <div className="idea-section">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Questions to answer</p>
            <h3>What to validate before you lock the story</h3>
          </div>
        </div>
        <ul className="plain-list">
          {ideaPack.validationQuestions.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}
