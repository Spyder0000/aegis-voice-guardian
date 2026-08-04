import React, { useEffect, useMemo, useState } from "react";
import ConfirmationCard from "../components/ConfirmationCard";
import TrustLedgerView from "../components/TrustLedgerView";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:8000";
const SAMPLE_TRANSCRIPT = "Send 150000 to this new account for the customs officer...";

const mockLedger = [
  {
    id: 1,
    transcript: "Please move 25000 to my landlord after 5pm.",
    amount: 25000,
    recipient: "Landlord Account",
    risk_level: "LOW",
    reasons: ["Recipient known in transfer history", "Amount within normal pattern"],
    action: "released",
    created_at: "2026-08-04T18:15:00Z",
  },
  {
    id: 2,
    transcript: "Urgent payment to a supplier who called me from a new number.",
    amount: 88000,
    recipient: "Supplier Holdings",
    risk_level: "MEDIUM",
    reasons: ["New recipient", "Urgency pressure language detected"],
    action: "held",
    created_at: "2026-08-04T19:40:00Z",
  },
  {
    id: 3,
    transcript: "Send 150000 to this new account for the customs officer...",
    amount: 150000,
    recipient: "Unknown Recipient (new)",
    risk_level: "HIGH",
    reasons: [
      "Recipient not in known transfer history",
      "Amount is 12.5x the user's average",
      "Urgency/pressure language detected",
    ],
    action: "escalated",
    created_at: "2026-08-04T21:10:00Z",
  },
];

function randomTransactionId() {
  if (window.crypto?.randomUUID) {
    return `txn_${window.crypto.randomUUID().slice(0, 8)}`;
  }

  return `txn_${Math.random().toString(36).slice(2, 10)}`;
}

export default function Dashboard({ onBackHome }) {
  const [transcriptInput, setTranscriptInput] = useState(SAMPLE_TRANSCRIPT);
  const [pendingTransfer, setPendingTransfer] = useState(null);
  const [ledgerEntries, setLedgerEntries] = useState(mockLedger);
  const [statusMessage, setStatusMessage] = useState("Enter a transcript and analyze it against the backend.");
  const [lastDecision, setLastDecision] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  useEffect(() => {
    fetchLedger();
  }, []);

  async function fetchLedger() {
    try {
      const response = await fetch(`${API_BASE}/transfers/ledger`);
      if (!response.ok) {
        throw new Error("Ledger endpoint unavailable");
      }

      const data = await response.json();
      if (Array.isArray(data)) {
        setLedgerEntries(data);
        return data;
      }
    } catch (error) {
      setLedgerEntries(mockLedger);
    }

    return mockLedger;
  }

  async function postDecision(payload) {
    const response = await fetch(`${API_BASE}/transfers/decision`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error("Decision endpoint unavailable");
    }

    return response.json();
  }

  async function analyzeTranscript(transcriptOverride) {
    const transcript = (transcriptOverride ?? transcriptInput).trim();

    if (!transcript) {
      setStatusMessage("Enter a transcript before analyzing it.");
      return;
    }

    setIsAnalyzing(true);

    try {
      const response = await fetch(`${API_BASE}/voice/intake`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ transcript }),
      });

      if (!response.ok) {
        throw new Error("Voice intake failed");
      }

      const data = await response.json();
      const risk = data.risk_evaluation || {};
      const riskLevel = (risk.risk_level || "LOW").toUpperCase();

      if (riskLevel === "LOW") {
        const result = await postDecision({
          user_id: "usr_sample",
          amount: data.amount,
          recipient: data.recipient,
          risk_level: riskLevel,
          transcript: data.transcript,
          reasons: risk.reasons || [],
          user_confirmation: { verified_pin: true },
        });

        if (result.ledger_entry) {
          setLedgerEntries((currentEntries) => [result.ledger_entry, ...currentEntries]);
        } else {
          await fetchLedger();
        }

        setPendingTransfer(null);
        setLastDecision({ tone: "success", text: "Backend marked the transfer as low risk and released it." });
        setStatusMessage(data.clarifying_question || "Backend returned a low-risk decision.");
        return;
      }

      setPendingTransfer({
        transaction_id: randomTransactionId(),
        transcript: data.transcript,
        amount: data.amount,
        recipient: data.recipient,
        risk_level: riskLevel,
        score: risk.score,
        reasons: risk.reasons || [],
        clarifying_question: data.clarifying_question,
      });
      setStatusMessage(data.clarifying_question || "Backend flagged the transfer for confirmation.");
      setLastDecision(null);
    } catch (error) {
      setStatusMessage("Backend call failed. The frontend is showing the example transcript.");
      setPendingTransfer({
        transaction_id: randomTransactionId(),
        transcript,
        amount: 150000,
        recipient: "Unknown Recipient (new)",
        risk_level: "HIGH",
        score: 0.82,
        reasons: [
          "Recipient not in known transfer history",
          "Amount is 12.5x the user's average",
          "Urgency language detected: customs officer, needs it now",
        ],
        clarifying_question: "The backend is unavailable, so the UI is showing the local example transfer.",
      });
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function handleConfirm({ pin, transactionId }) {
    if (!pendingTransfer) {
      return;
    }

    try {
      const result = await postDecision({
        user_id: "usr_sample",
        transaction_id: transactionId,
        amount: pendingTransfer.amount,
        recipient: pendingTransfer.recipient,
        risk_level: pendingTransfer.risk_level,
        transcript: pendingTransfer.transcript,
        reasons: pendingTransfer.reasons,
        user_confirmation: { verified_pin: pin.length >= 4 },
      });

      if (result.ledger_entry) {
        setLedgerEntries((currentEntries) => [result.ledger_entry, ...currentEntries]);
      } else {
        await fetchLedger();
      }

      setPendingTransfer(null);
      setLastDecision({ tone: "success", text: "Transfer released after PIN confirmation." });
      setStatusMessage(result.message || "Decision recorded by the backend. Ledger updated.");
    } catch (error) {
      setStatusMessage("Could not post the confirmation to the backend.");
    }
  }

  async function handleReject() {
    if (!pendingTransfer) {
      return;
    }

    try {
      const result = await postDecision({
        user_id: "usr_sample",
        transaction_id: pendingTransfer.transaction_id,
        amount: pendingTransfer.amount,
        recipient: pendingTransfer.recipient,
        risk_level: pendingTransfer.risk_level,
        transcript: pendingTransfer.transcript,
        reasons: pendingTransfer.reasons,
        user_confirmation: { verified_pin: false },
      });

      if (result.ledger_entry) {
        setLedgerEntries((currentEntries) => [result.ledger_entry, ...currentEntries]);
      } else {
        await fetchLedger();
      }

      setPendingTransfer(null);
      setLastDecision({ tone: "warning", text: "Transfer rejected and held for review." });
      setStatusMessage(result.message || "Decision recorded by the backend. Ledger updated.");
    } catch (error) {
      setStatusMessage("Could not post the rejection to the backend.");
    }
  }

  function triggerExampleTransfer() {
    setTranscriptInput(SAMPLE_TRANSCRIPT);
    analyzeTranscript(SAMPLE_TRANSCRIPT);
  }

  const metrics = useMemo(() => {
    const highRisk = ledgerEntries.filter((entry) => entry.risk_level === "HIGH").length;
    const held = ledgerEntries.filter((entry) => entry.action === "held").length;
    const released = ledgerEntries.filter((entry) => entry.action === "released").length;

    return [
      { label: "Ledger entries", value: ledgerEntries.length },
      { label: "High risk decisions", value: highRisk },
      { label: "Transfers held", value: held },
      { label: "Released after confirm", value: released },
    ];
  }, [ledgerEntries]);

  const totalAmount = useMemo(() => {
    const formatter = new Intl.NumberFormat("en-NG", {
      style: "currency",
      currency: "NGN",
      maximumFractionDigits: 0,
    });

    return formatter.format(pendingTransfer?.amount || 0);
  }, [pendingTransfer]);

  return (
    <main className="dashboard-shell">
      <section className="hero-band">
        <div className="hero-band__glow hero-band__glow--left" />
        <div className="hero-band__glow hero-band__glow--right" />

        <header className="topbar">
          <div className="brand-lockup">
            <span className="brand-mark" aria-hidden="true" />
            <div>
              <p className="brand-eyebrow">AEGIS Voice Guardian</p>
              <p className="brand-subtitle">Voice can start the flow. Only a tactile confirm can release money.</p>
            </div>
          </div>

          <div className="topbar__status">
            <span className="status-pill status-pill--live">Live backend</span>
            {onBackHome ? (
              <button className="status-pill status-pill--button" type="button" onClick={onBackHome}>
                Back to landing
              </button>
            ) : null}
          </div>
        </header>

        <div className="hero-grid">
          <div className="hero-copy">
            <p className="section-kicker">Visual confirmation gate</p>
            <h1>Stop voice-only fraud before the transfer leaves the screen.</h1>
            <p className="hero-copy__lead">
              This interface pairs a high-friction confirmation card with an explainable trust ledger so a risky transfer
              is impossible to miss, easy to reject, and simple to audit.
            </p>

            <div className="analysis-panel">
              <label htmlFor="transcript-input" className="analysis-panel__label">
                Voice transcript to analyze
              </label>
              <textarea
                id="transcript-input"
                className="analysis-panel__input"
                rows="4"
                value={transcriptInput}
                onChange={(event) => setTranscriptInput(event.target.value)}
                placeholder="Paste or type a transfer request transcript"
              />
              <div className="hero-actions hero-actions--analysis">
                <button className="primary-button" type="button" onClick={analyzeTranscript} disabled={isAnalyzing}>
                  {isAnalyzing ? "Analyzing..." : "Analyze with backend"}
                </button>
                <button className="secondary-button" type="button" onClick={triggerExampleTransfer} disabled={isAnalyzing}>
                  Load example transfer
                </button>
                <button className="secondary-button" type="button" onClick={fetchLedger} disabled={isAnalyzing}>
                  Refresh ledger
                </button>
              </div>
            </div>

            <div className="status-message">{statusMessage}</div>

            <div className="metric-grid" aria-label="Dashboard metrics">
              {metrics.map((metric) => (
                <article key={metric.label} className="metric-card">
                  <span>{metric.label}</span>
                  <strong>{metric.value}</strong>
                </article>
              ))}
            </div>
          </div>

          <div className="hero-preview">
            <div className="hero-preview__panel">
              <p className="section-kicker">Current alert</p>
              <h2>{pendingTransfer ? "Pending transfer needs a PIN" : "No pending transfer"}</h2>
              <p className="hero-preview__amount">{pendingTransfer ? totalAmount : "No money is waiting on confirmation."}</p>
              <p className="hero-preview__recipient">{pendingTransfer ? pendingTransfer.recipient : "The ledger is calm right now."}</p>
              {pendingTransfer ? (
                <p className="hero-preview__question">{pendingTransfer.clarifying_question || "Backend asked for an explicit confirmation."}</p>
              ) : null}

              <div className="preview-checklist">
                <div>
                  <span>Risk level</span>
                  <strong>{pendingTransfer ? pendingTransfer.risk_level : "LOW"}</strong>
                </div>
                <div>
                  <span>Transaction</span>
                  <strong>{pendingTransfer ? pendingTransfer.transaction_id : "—"}</strong>
                </div>
              </div>

              <div className="preview-divider" />
              <p className="hero-preview__footnote">No voice command can bypass the confirm button or the cancel path.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="content-grid">
        <div className="content-grid__main">
          {pendingTransfer ? (
            <ConfirmationCard
              amount={pendingTransfer.amount}
              recipient={pendingTransfer.recipient}
              riskLevel={pendingTransfer.risk_level}
              reasons={pendingTransfer.reasons}
              transactionId={pendingTransfer.transaction_id}
              onConfirm={handleConfirm}
              onReject={handleReject}
            />
          ) : (
            <div className="empty-state empty-state--dark">
              <h3>No risky transfer is currently awaiting confirmation.</h3>
              <p>Use the example transcript above to bring the high-risk card back onto the screen.</p>
              <button className="primary-button" type="button" onClick={triggerExampleTransfer}>
                Reload example transfer
              </button>
            </div>
          )}

          {lastDecision ? (
            <div className={`decision-banner decision-banner--${lastDecision.tone}`}>
              {lastDecision.text}
            </div>
          ) : null}
        </div>

        <aside className="content-grid__rail">
          <div className="rail-card">
            <p className="section-kicker">Why this matters</p>
            <h2>Every decision stays explainable.</h2>
            <p>
              Judges should be able to see the amount, recipient, risk label, action, and the reason list in one glance.
            </p>
          </div>

          <div className="rail-card rail-card--compact">
            <p className="section-kicker">Flow</p>
            <ol className="flow-list">
              <li>Voice transcript is analyzed by the backend.</li>
              <li>User checks amount, recipient, and reasons.</li>
              <li>PIN confirm releases or cancel holds the payment.</li>
              <li>The backend ledger captures the outcome for review.</li>
            </ol>
          </div>

          <div className="rail-card rail-card--compact">
            <p className="section-kicker">Status</p>
            <div className="status-stack">
              <span className="status-row">
                <span className="status-dot status-dot--success" />
                Backend voice intake connected
              </span>
              <span className="status-row">
                <span className="status-dot status-dot--warning" />
                PIN is mandatory before confirm
              </span>
              <span className="status-row">
                <span className="status-dot status-dot--info" />
                Ledger updates after every decision
              </span>
            </div>
          </div>
        </aside>
      </section>

      <section className="ledger-section">
        <TrustLedgerView entries={ledgerEntries} />
      </section>
    </main>
  );
}
