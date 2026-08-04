import React, { useMemo } from "react";

const actionLabels = {
  released: "Released",
  held: "Held",
  escalated: "Escalated",
};

export default function TrustLedgerView({ entries = [] }) {
  const hasEntries = entries.length > 0;

  const currencyFormatter = useMemo(
    () =>
      new Intl.NumberFormat("en-NG", {
        style: "currency",
        currency: "NGN",
        maximumFractionDigits: 0,
      }),
    [],
  );

  if (!hasEntries) {
    return (
      <div className="empty-state">
        <h3>No transactions logged yet.</h3>
        <p>When a risk decision lands, the ledger records the amount, outcome, and reasons.</p>
      </div>
    );
  }

  return (
    <div className="ledger-shell">
      <div className="ledger-shell__header">
        <div>
          <p className="section-kicker">Explainability</p>
          <h2>Trust Ledger</h2>
        </div>
        <p className="ledger-shell__subtext">Every hold, release, and escalation stays visible.</p>
      </div>

      <div className="trust-ledger__wrap">
        <table className="trust-ledger">
          <thead>
            <tr>
              <th scope="col">Time</th>
              <th scope="col">Recipient</th>
              <th scope="col">Amount</th>
              <th scope="col">Risk</th>
              <th scope="col">Action</th>
              <th scope="col">Why</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) => {
              const riskTone = (entry.risk_level || "low").toLowerCase();
              const createdAt = entry.created_at
                ? new Date(entry.created_at).toLocaleString([], {
                    hour: "numeric",
                    minute: "2-digit",
                    month: "short",
                    day: "numeric",
                  })
                : "—";

              return (
                <tr key={entry.id} className={`risk-row risk-row--${riskTone}`}>
                  <td data-label="Time">{createdAt}</td>
                  <td data-label="Recipient">{entry.recipient}</td>
                  <td data-label="Amount">{currencyFormatter.format(entry.amount || 0)}</td>
                  <td data-label="Risk">
                    <span className={`risk-badge risk-${riskTone}`}>
                      {(entry.risk_level || "LOW").toUpperCase()}
                    </span>
                  </td>
                  <td data-label="Action">
                    <span className="action-pill">{actionLabels[entry.action] || entry.action}</span>
                  </td>
                  <td data-label="Why">
                    <ul className="ledger-reasons">
                      {(entry.reasons || []).map((reason, index) => (
                        <li key={`${entry.id}-${index}`}>{reason}</li>
                      ))}
                    </ul>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
