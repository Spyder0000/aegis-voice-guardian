import React from "react";

const highlights = [
  {
    title: "Voice is allowed to start the flow",
    body: "Sahara ASR can hear the request, but a tactile confirmation card has to approve any risky transfer.",
  },
  {
    title: "Risk stays explainable",
    body: "Every hold records the amount, recipient, risk level, and the reasons behind the decision.",
  },
];

const proofPoints = [
  {
    label: "Risk gate",
    value: "PIN before release",
  },
  {
    label: "Audit trail",
    value: "Explainable ledger",
  },
  {
    label: "Decision modes",
    value: "Release, hold, escalate",
  },
  {
    label: "Sample data",
    value: "Ready to review",
  },
];

const steps = [
  "A voice request enters the system.",
  "The trust score flags the transfer when the pattern looks suspicious.",
  "A visual confirmation card takes over and demands an explicit PIN or cancel.",
  "The ledger stores the reason trail for review.",
];

export default function LandingPage({ onOpenDashboard }) {
  return (
    <main className="landing-shell">
      <section className="landing-hero-band">
        <div className="hero-band__glow hero-band__glow--left" />
        <div className="hero-band__glow hero-band__glow--right" />

        <header className="landing-topbar">
          <div className="brand-lockup">
            <span className="brand-mark" aria-hidden="true" />
            <div>
              <p className="brand-eyebrow">AEGIS Voice Guardian</p>
              <p className="brand-subtitle">A safety-first voice transfer experience for live banking walkthroughs.</p>
            </div>
          </div>

          <div className="topbar__status">
            <span className="status-pill status-pill--live">Built for live review</span>
            <span className="status-pill">Explainable risk, not silent automation</span>
          </div>
        </header>

        <div className="landing-hero-grid">
          <div className="landing-hero-copy">
            <p className="section-kicker">Design-forward safety layer</p>
            <h1>Voice can start a transfer, but it should never finish one alone.</h1>
            <p className="hero-copy__lead">
              AEGIS Voice Guardian listens for scam pressure, scores the request, and stops suspicious transfers behind
              a tactile confirmation card before money moves.
            </p>

            <div className="hero-actions">
              <button className="primary-button" type="button" onClick={onOpenDashboard}>
                Open the dashboard
              </button>
              <a className="secondary-button secondary-button--link" href="#how-it-works">
                See how it works
              </a>
            </div>

            <div className="proof-grid">
              {proofPoints.map((point) => (
                <article key={point.label} className="proof-card">
                  <span>{point.label}</span>
                  <strong>{point.value}</strong>
                </article>
              ))}
            </div>
          </div>

          <div className="landing-feature-stack">
            <article className="landing-signal-card">
              <p className="section-kicker">Live safety loop</p>
              <ul className="signal-list">
                <li>Risky transfer detected</li>
                <li>Confirmation card appears</li>
                <li>PIN or reject required</li>
                <li>Ledger updates with reasons</li>
              </ul>
            </article>
          </div>
        </div>
      </section>

      <section className="landing-content-grid" id="how-it-works">
        <div className="landing-column">
          <div className="landing-section-heading">
            <p className="section-kicker">What it solves</p>
            <h2>Voice-only fraud fails when the UI forces a second channel.</h2>
          </div>

          <div className="feature-grid">
            {highlights.map((item) => (
              <article key={item.title} className="feature-card feature-card--dark">
                <h3>{item.title}</h3>
                <p>{item.body}</p>
              </article>
            ))}
          </div>
        </div>

        <aside className="landing-column landing-column--rail">
          <div className="rail-card rail-card--landing">
            <p className="section-kicker">Flow</p>
            <ol className="flow-list">
              {steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </div>
        </aside>
      </section>

      <section className="landing-cta-band">
        <div>
          <p className="section-kicker">Ready for review</p>
          <h2>Open the dashboard and trigger a risky transfer.</h2>
        </div>

        <button className="primary-button" type="button" onClick={onOpenDashboard}>
          Launch dashboard
        </button>
      </section>
    </main>
  );
}