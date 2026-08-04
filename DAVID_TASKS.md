# David's Task Sheet — AEGIS Voice Guardian
**Role:** Frontend & Trust Ledger UI
**Owns:** Visual Confirmation Card, Trust Ledger view, Dashboard wiring

---

## Phase 0 — Understand What You're Building

You're building the two things a judge will actually look at during the demo, and the one thing that makes this project safe in real life: **voice alone should never release money.** When the system flags a transfer as risky, your Confirmation Card is the physical gate — the customer has to tap/confirm, not just talk, before anything moves. Your Trust Ledger view is what proves the system is explainable, not a black box.

**Wait for Agoro to publish his API shapes before building** (should happen in the first ~6 hours) — you're consuming his endpoints, not guessing the data format. In the meantime, build against the mocked contract below so you're not blocked.

---

## Phase 1 — The Contract You're Building Against

These are the shapes Agoro and Toluwalase have committed to. Use these to build with mock data first:

```js
// What you get when a transfer is flagged risky (from /voice/intake + /trust/score)
{
  transcript: "Send 150000 to this new account for the customs officer...",
  amount: 150000,
  recipient: "Unknown Recipient (new)",
  risk_level: "HIGH",        // "LOW" | "MEDIUM" | "HIGH"
  score: 0.82,
  reasons: [
    "Recipient not in known transfer history",
    "Amount is 12.5x the user's average",
    "Urgency/pressure language detected: ['customs officer', 'needs it now']"
  ]
}

// What you send back after the user confirms/rejects on your Confirmation Card
{
  user_confirmed: true,   // or false
  transaction_id: "txn_abc123"
}

// What you get back for the Trust Ledger view (a list of these)
{
  id: 1,
  transcript: "...",
  amount: 150000,
  recipient: "...",
  risk_level: "HIGH",
  reasons: [...],
  action: "released" | "held" | "escalated",
  created_at: "2026-08-04T21:10:00Z"
}
```

- [ ] Confirmed this matches what Agoro/Toluwalase actually built (check in with them by Hour 6)

---

## Phase 2 — Build the Confirmation Card (your most important piece)

`frontend/src/components/ConfirmationCard.jsx`:

```jsx
// Visual Confirmation Card — the physical gate that stops voice-only fraud.
// Owner: David Akhabue
// Re-displays amount + recipient in large, unambiguous text.
// Transfer only releases on tactile/PIN confirm — never on voice alone.

import { useState } from "react";

export default function ConfirmationCard({ amount, recipient, riskLevel, reasons, onConfirm, onReject }) {
  const [pin, setPin] = useState("");
  const [error, setError] = useState("");

  const formattedAmount = new Intl.NumberFormat("en-NG", {
    style: "currency",
    currency: "NGN",
  }).format(amount);

  function handleConfirm() {
    if (pin.length < 4) {
      setError("Enter your PIN to confirm.");
      return;
    }
    onConfirm({ pin });
  }

  return (
    <div className="confirmation-card" role="alertdialog" aria-live="assertive">
      <div className={`risk-badge risk-${riskLevel.toLowerCase()}`}>
        {riskLevel} RISK
      </div>

      <h2>Confirm this transfer</h2>

      <div className="transfer-details">
        <div className="amount">{formattedAmount}</div>
        <div className="recipient">to {recipient}</div>
      </div>

      {reasons?.length > 0 && (
        <ul className="risk-reasons">
          {reasons.map((r, i) => (
            <li key={i}>{r}</li>
          ))}
        </ul>
      )}

      <label>
        Enter PIN to confirm
        <input
          type="password"
          inputMode="numeric"
          maxLength={4}
          value={pin}
          onChange={(e) => setPin(e.target.value)}
        />
      </label>
      {error && <p className="error">{error}</p>}

      <div className="actions">
        <button className="confirm" onClick={handleConfirm}>
          Confirm Transfer
        </button>
        <button className="reject" onClick={onReject}>
          Cancel — This Looks Wrong
        </button>
      </div>
    </div>
  );
}
```

- [ ] Component renders with mock data (amount, recipient, risk_level, reasons)
- [ ] PIN field requires input before "Confirm" does anything (no silent voice-only bypass)
- [ ] "Cancel" path works and is visually distinct (this is the customer catching a scam in real time — make it obvious and easy)
- [ ] Risk badge color-codes clearly (e.g., red for HIGH, amber for MEDIUM)

---

## Phase 3 — Build the Trust Ledger View

`frontend/src/components/TrustLedgerView.jsx`:

```jsx
// Trust Ledger view — explainable log of every hold/decision.
// Owner: David Akhabue

export default function TrustLedgerView({ entries }) {
  if (!entries?.length) {
    return <p className="empty-state">No transactions logged yet.</p>;
  }

  return (
    <table className="trust-ledger">
      <thead>
        <tr>
          <th>Time</th>
          <th>Recipient</th>
          <th>Amount</th>
          <th>Risk</th>
          <th>Action</th>
          <th>Why</th>
        </tr>
      </thead>
      <tbody>
        {entries.map((entry) => (
          <tr key={entry.id} className={`risk-row-${entry.risk_level.toLowerCase()}`}>
            <td>{new Date(entry.created_at).toLocaleTimeString()}</td>
            <td>{entry.recipient}</td>
            <td>
              {new Intl.NumberFormat("en-NG", {
                style: "currency",
                currency: "NGN",
              }).format(entry.amount)}
            </td>
            <td>
              <span className={`risk-badge risk-${entry.risk_level.toLowerCase()}`}>
                {entry.risk_level}
              </span>
            </td>
            <td>{entry.action}</td>
            <td>
              <ul>
                {entry.reasons.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

- [ ] Table renders with mock data (a handful of fake entries covering LOW, MEDIUM, HIGH)
- [ ] Every row shows *why* the decision was made, not just what the decision was — this is the "explainable AI" selling point for judges
- [ ] Handles the empty state (no entries yet) without breaking

---

## Phase 4 — Wire the Dashboard

`frontend/src/pages/Dashboard.jsx` — brings it all together:

```jsx
// Dashboard — wires ConfirmationCard + TrustLedgerView to backend endpoints.
// Owner: David Akhabue

import { useState, useEffect } from "react";
import ConfirmationCard from "../components/ConfirmationCard";
import TrustLedgerView from "../components/TrustLedgerView";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:8000";

export default function Dashboard() {
  const [pendingTransfer, setPendingTransfer] = useState(null);
  const [ledgerEntries, setLedgerEntries] = useState([]);

  useEffect(() => {
    fetchLedger();
  }, []);

  async function fetchLedger() {
    const res = await fetch(`${API_BASE}/ledger`);
    const data = await res.json();
    setLedgerEntries(data);
  }

  // Call this after Agoro's /voice/intake + /trust/score pipeline returns
  // a MEDIUM/HIGH risk result — triggers the card.
  function onRiskyTransferDetected(transferData) {
    setPendingTransfer(transferData);
  }

  async function handleConfirm({ pin }) {
    await fetch(`${API_BASE}/transfers/decision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        transaction_id: pendingTransfer.transaction_id,
        user_confirmed: true,
        pin,
      }),
    });
    setPendingTransfer(null);
    fetchLedger();
  }

  async function handleReject() {
    await fetch(`${API_BASE}/transfers/decision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        transaction_id: pendingTransfer.transaction_id,
        user_confirmed: false,
      }),
    });
    setPendingTransfer(null);
    fetchLedger();
  }

  return (
    <div className="dashboard">
      <h1>AEGIS Voice Guardian</h1>

      {pendingTransfer && (
        <ConfirmationCard
          amount={pendingTransfer.amount}
          recipient={pendingTransfer.recipient}
          riskLevel={pendingTransfer.risk_level}
          reasons={pendingTransfer.reasons}
          onConfirm={handleConfirm}
          onReject={handleReject}
        />
      )}

      <section>
        <h2>Trust Ledger</h2>
        <TrustLedgerView entries={ledgerEntries} />
      </section>
    </div>
  );
}
```

- [ ] `fetchLedger()` pulls real data once Darius's `/ledger` endpoint (or whatever Agoro names it) exists
- [ ] `onRiskyTransferDetected` is called correctly once Agoro's pipeline is wired to push events to the frontend (confirm the exact mechanism with him — websocket push vs. polling)
- [ ] Full loop works: risky transfer appears → card shows → confirm/reject → ledger updates

---

## Phase 5 — Polish (do this last, after everything works)

- [ ] Basic styling so risk levels are visually obvious at a glance (color coding)
- [ ] Make sure the Confirmation Card is impossible to miss on screen — this is your safety story, it should look serious
- [ ] Test on the actual device/browser you'll demo on

---

## You're Done With Your Part When:
- A fake high-risk transfer triggers the Confirmation Card, and it cannot be dismissed without either a PIN confirm or an explicit reject
- The Trust Ledger view shows a clear, readable history with reasons for every entry
- The whole loop (risky call → card → decision → ledger update) works live, not just with mock data
