# Trust Score Service — Input Contract
**Status:** Proposed — needs sign-off from Agoro (produces this payload) and Darius (owns `user_profile` source data) before Toluwalase builds against it as final.

**Credit where due:** this contract is Toluwalase's proposed schema, tightened in two places (see "What changed" below).

---

## The Pipeline (confirmed)

```
Audio
  ↓
Sahara ASR                              ← Agoro
  ↓
Transcript
  ↓
Entity Extraction (amount, recipient,
  urgency phrases, authority claims)    ← Agoro (part of orchestrator.py)
  ↓
+ User Profile lookup (avg transfer,
  recipient history)                    ← Darius's trust_profile table,
                                            queried by Agoro's orchestrator
  ↓
Trust Score  ←—————————————————————————— Toluwalase's module starts here
  ↓
Decision Agent                          ← Toluwalase
  ↓
Bank Action                             ← Darius's mock_banking_api.py
```

**Confirmed: Toluwalase's module receives structured features only — never raw audio, and it does not parse natural language itself.** That's Agoro's layer's job. This was the right question to ask.

---

## Finalized Input Schema

```json
{
  "transcript": "Send 500k to Chinedu immediately.",
  "recipient": "Chinedu",
  "amount": 500000,
  "currency": "NGN",
  "timestamp": "2026-08-04T23:14:00Z",
  "intent": "money_transfer",
  "language": "English + Pidgin",
  "entities": {
    "urgency_phrases": ["immediately"],
    "authority_claim": false,
    "bank_keywords": []
  },
  "user_profile": {
    "average_transfer": 25000,
    "largest_transfer": 100000,
    "recipient_seen_before": false,
    "transfer_count_to_recipient": 0
  }
}
```

### What changed from the original speculation, and why

| Field | Original proposal | Change | Why |
|---|---|---|---|
| `entities.urgency` | `true` / `false` | → `entities.urgency_phrases`: `["immediately", ...]` (list, can be empty) | The rule-based scorer's `reasons` output needs the *actual phrases matched*, not just a flag — that's what makes the Trust Ledger explainable to judges, not just "urgency: true" |
| `timestamp` | not present | → added, ISO 8601 | The scorer flags unusual hours (e.g. 11pm–5am) as a risk signal; without a timestamp this feature can't run at all |

Everything else in Toluwalase's original schema is adopted as-is.

### Who owns producing each field
| Field | Source |
|---|---|
| `transcript`, `intent`, `language` | Agoro — direct from Sahara ASR output |
| `recipient`, `amount`, `currency` | Agoro — entity extraction on the transcript |
| `entities.*` | Agoro — entity extraction / keyword matching on the transcript |
| `timestamp` | Agoro — time the call came in |
| `user_profile.*` | Darius's `trust_profile` table, **queried by Agoro's orchestrator** before it calls `/trust/score` — Toluwalase never queries the DB directly |

This confirms Toluwalase's own observation: "almost every field comes from another team member" — the contract above is what makes that explicit instead of implicit.

---

## Adapter — Translating the Contract into `rule_based.py`

Toluwalase's existing `score()` function in `rule_based.py` already expects a flatter internal shape (`recipient_is_new`, `avg_transfer_amount`, `hour_of_day`, etc.) — **no need to rewrite that function.** Add this adapter in front of it instead, so the public contract and the internal implementation can evolve independently:

```python
"""
Adapter: translates the /trust/score API contract into the internal
feature shape that rule_based.score() already expects.
Owner: Toluwalase Ajiboye

Keeping this as a separate function means:
- the external API contract (what Agoro sends) can change without
  touching the scoring logic itself
- swapping rule_based.score() for an XGBoost model later only requires
  changing what's inside `score()`, not this adapter
"""
from datetime import datetime
from trust_score.rule_based import score as rule_based_score


def score_from_contract(payload: dict) -> dict:
    """
    payload: the full /trust/score request body, matching the
    finalized contract in TRUST_SCORE_CONTRACT.md
    """
    entities = payload.get("entities", {})
    profile = payload.get("user_profile", {})

    timestamp = payload.get("timestamp")
    hour_of_day = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).hour \
        if timestamp else 12  # default to a neutral hour if missing

    features = {
        "recipient_is_new": not profile.get("recipient_seen_before", False),
        "amount": payload["amount"],
        "avg_transfer_amount": profile.get("average_transfer", 0),
        "hour_of_day": hour_of_day,
        "urgency_phrases": entities.get("urgency_phrases", []),
    }

    return rule_based_score(features, transcript=payload.get("transcript"))
```

- [ ] `score_from_contract()` added to `ml/trust_score/` — this is what the `/trust/score` FastAPI endpoint should actually call, not `rule_based.score()` directly
- [ ] Test with the example payload above — confirm it returns a sensible risk level

---

## Next Step: Get Sign-Off

Send this doc to Agoro and Darius specifically asking:
1. **Agoro:** does your entity extraction produce `urgency_phrases` as a list (not a boolean), and can you attach a `timestamp`?
2. **Darius:** does your `trust_profile` schema currently store `average_transfer`, `largest_transfer`, `recipient_seen_before`, and `transfer_count_to_recipient` — or does the schema need a small update to match?

Once both confirm, this stops being "speculation" and becomes the locked contract in `docs/ARCHITECTURE.md`.
