import React from "react";

export default function Landing({ onOpenDashboard }) {
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
              <p className="brand-subtitle">Your voice, verified before it moves your money.</p>
            </div>
          </div>

          <div className="topbar__status">
            <span className="status-pill status-pill--live">Live Guardrails</span>
            <span className="status-pill">Explainable Risk Engine</span>
          </div>
        </header>

        <div className="landing-hero-grid">
          <div className="landing-hero-copy">
            <p className="section-kicker">Voice Security Layer</p>
            <h1>AEGIS Voice Guardian</h1>
            <p className="hero-copy__lead">
              Your voice, verified before it moves your money. Intercepting zero-day social engineering and urgent voice scams with explainable risk scoring and a tactile visual confirmation gate.
            </p>

            <div className="hero-actions">
              <button className="primary-button" type="button" onClick={onOpenDashboard}>
                Enter Dashboard
              </button>
              <a className="secondary-button secondary-button--link" href="#how-it-works">
                See How It Works
              </a>
            </div>

            <div className="proof-grid">
              <article className="proof-card">
                <span>Risk Gate</span>
                <strong>Tactile PIN Confirm</strong>
              </article>
              <article className="proof-card">
                <span>Audit Trail</span>
                <strong>Explainable Ledger</strong>
              </article>
              <article className="proof-card">
                <span>ASR Engine</span>
                <strong>Intron Sahara STT</strong>
              </article>
              <article className="proof-card">
                <span>Protection</span>
                <strong>Soft-Hold Security</strong>
              </article>
            </div>
          </div>

          <div className="landing-feature-stack">
            <article className="landing-signal-card">
              <p className="section-kicker">Live Security Flow</p>
              <ul className="signal-list">
                <li>1. Voice Request Evaluated</li>
                <li>2. Scam Urgency Detected</li>
                <li>3. Visual Confirmation Card Pops Up</li>
                <li>4. Tactile PIN Verified</li>
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
            <article className="feature-card feature-card--dark">
              <h3>Voice is allowed to start the flow</h3>
              <p>
                Sahara ASR hears the request, but a tactile confirmation card must approve any risky transfer before money moves.
              </p>
            </article>
            <article className="feature-card feature-card--dark">
              <h3>Risk stays explainable</h3>
              <p>
                Every hold records the amount, recipient, risk level, and the exact reasons behind the decision.
              </p>
            </article>
          </div>
        </div>
      </section>

      <section className="landing-cta-band">
        <div>
          <p className="section-kicker">Ready for review</p>
          <h2>Open the dashboard and trigger a risky transfer.</h2>
        </div>

        <button className="primary-button" type="button" onClick={onOpenDashboard}>
          Enter Dashboard
        </button>
      </section>
    </main>
  );
}
