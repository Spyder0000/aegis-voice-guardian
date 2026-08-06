import React, { useMemo, useState } from "react";

const riskMeta = {
  LOW: { label: "LOW RISK", tone: "low" },
  MEDIUM: { label: "MEDIUM RISK", tone: "medium" },
  HIGH: { label: "HIGH RISK", tone: "high" },
};

export default function ConfirmationCard({
  amount,
  recipient,
  riskLevel = "HIGH",
  reasons = [],
  transactionId,
  onConfirm,
  onReject,
}) {
  const [pin, setPin] = useState("");
  const [error, setError] = useState("");

  const formattedAmount = useMemo(
    () =>
      new Intl.NumberFormat("en-NG", {
        style: "currency",
        currency: "NGN",
        maximumFractionDigits: 0,
      }).format(amount || 0),
    [amount],
  );

  const riskLabel = riskMeta[riskLevel] || riskMeta.HIGH;

  function handleConfirm() {
    if (pin.length < 4) {
      setError("Enter a 4-digit PIN to confirm this transfer.");
      return;
    }

    setError("");
    onConfirm?.({ pin, transactionId });
  }

  function handlePinChange(event) {
    const nextValue = event.target.value.replace(/\D/g, "").slice(0, 4);
    setPin(nextValue);
    if (error) {
      setError("");
    }
  }

  return (
    <section className="confirmation-card" aria-labelledby="confirm-transfer-heading">
      <div className={`risk-badge risk-${riskLabel.tone}`}>{riskLabel.label}</div>

      <div className="confirmation-card__header">
        <div>
          <p className="section-kicker">Action required</p>
          <h2 id="confirm-transfer-heading">Confirm this transfer</h2>
        </div>
        {transactionId ? <span className="transaction-chip">{transactionId}</span> : null}
      </div>

      <div className="transfer-details">
        <div className="transfer-details__amount">{formattedAmount}</div>
        <div className="transfer-details__recipient">to {recipient}</div>
      </div>

      <div className="confirmation-card__note">
        Voice alone cannot release this payment. Confirm with your PIN or cancel it now.
      </div>

      {reasons.length > 0 && (
        <div className="reason-stack" aria-label="Risk reasons">
          <h3>Why it was flagged</h3>
          <ul className="risk-reasons">
            {reasons.map((reason, index) => (
              <li key={`${reason}-${index}`}>{reason}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="pin-field">
        <label htmlFor="transfer-pin">Enter PIN to confirm</label>
        <input
          id="transfer-pin"
          type="password"
          inputMode="numeric"
          autoComplete="off"
          maxLength={4}
          value={pin}
          onChange={handlePinChange}
          placeholder="••••"
        />
        <p className="pin-help">4 digits required before the confirmation button activates.</p>
      </div>

      {error ? <p className="error-message">{error}</p> : null}

      <div className="actions">
        <button className="confirm" type="button" onClick={handleConfirm}>
          Confirm transfer
        </button>
        <button className="reject" type="button" onClick={onReject}>
          Cancel this transfer
        </button>
      </div>
    </section>
  );
}
