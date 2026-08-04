# Toluwalase's Task Sheet — AEGIS Voice Guardian
**Role:** Trust Score & Benchmarking
**Owns:** Rule-based Trust Score baseline, Decision Agent, `/trust/score` endpoint, benchmark harness

**Decision log:** using a **rule-based heuristic** for the Trust Score, not XGBoost — not enough data/time to train and validate a model this early. XGBoost is a bonus task only if time allows after the baseline works end-to-end.

---

## Phase 0 — Understand What You're Building

You're the piece between Agoro's transcript and David's confirmation card. You take in details about a transfer request (is the recipient new? is the amount unusual? did they use scary/urgent language?) and output a risk level: LOW, MEDIUM, or HIGH — with reasons attached, because "explainable" is a core judging criterion.

Your function signature is the contract everyone else builds against:
```
score(features: dict, transcript: Optional[str]) -> {"risk_level": str, "score": float, "reasons": list[str]}
```
As long as this input/output shape never changes, you can rewrite the *inside* of `score()` however you want later (rules → XGBoost) without breaking Agoro's orchestrator or David's UI.

---

## Phase 1 — Drop In the Baseline Code

Create `ml/trust_score/rule_based.py` with the following:

```python
"""
Rule-based Trust Score baseline.
Owner: Toluwalase Ajiboye

DECISION LOG:
    Phase 1 (now): rule-based heuristic — no training data yet, and a
    transparent scorer is easier to validate + explain to judges.
    Phase 2 (if time allows): swap `score()` for an XGBoost model trained
    on synthetic + any real scripted-call data collected during the hackathon.
    The function signature below is the contract — orchestrator.py and
    decision_agent.py should only ever call `score()`, so switching the
    implementation later requires zero changes anywhere else.

Usage:
    from trust_score.rule_based import score

    result = score({
        "recipient_is_new": True,
        "amount": 150000,
        "avg_transfer_amount": 12000,
        "hour_of_day": 23,
        "urgency_phrases": ["customs officer", "needs it now"],
    })
    # -> {"risk_level": "HIGH", "score": 0.82, "reasons": [...]}
"""
from dataclasses import dataclass, field
from typing import Optional

# Phrases that signal authority-impersonation / urgency pressure.
# Keep this list growing as Darius's synthetic scam-call scripts get written —
# every real phrase pattern from those scripts should get added here.
URGENCY_PHRASES = [
    "customs officer",
    "needs it now",
    "your account is frozen",
    "urgent",
    "right away",
    "police",
    "immediately",
    "or you will lose",
    "verify your account",
    "package is stuck",
]

# Weights are intentionally simple and interpretable — every point maps to
# one sentence in the Trust Ledger rationale. Tune thresholds after running
# the first batch of scripted scam vs. genuine calls (Phase 3 below).
WEIGHTS = {
    "new_recipient": 0.30,
    "amount_deviation": 0.30,  # scaled 0-1 based on how far above average
    "unusual_hour": 0.10,      # e.g., very late night
    "urgency_language": 0.40,  # scaled by number of phrase hits, capped
}

RISK_THRESHOLDS = {
    "LOW": 0.30,
    "MEDIUM": 0.60,
    # anything >= 0.60 is HIGH
}


@dataclass
class TrustScoreInput:
    recipient_is_new: bool
    amount: float
    avg_transfer_amount: float
    hour_of_day: int  # 0-23
    urgency_phrases: list[str] = field(default_factory=list)


def _amount_deviation_score(amount: float, avg_amount: float) -> float:
    """0 if amount <= avg, scaling up to 1.0 as amount grows past 3x avg."""
    if avg_amount <= 0:
        return 0.5  # no history yet — treat as moderately unusual
    ratio = amount / avg_amount
    if ratio <= 1.0:
        return 0.0
    return min((ratio - 1.0) / 2.0, 1.0)  # caps at 3x average


def _unusual_hour_score(hour: int) -> float:
    """Flag late-night/early-morning transfers (11pm-5am) as moderately unusual."""
    return 1.0 if (hour >= 23 or hour <= 5) else 0.0


def _urgency_score(matched_phrases: list[str]) -> float:
    """Scales with number of urgency phrases hit, caps at 3+ hits."""
    return min(len(matched_phrases) / 3.0, 1.0)


def extract_urgency_phrases(transcript: str) -> list[str]:
    """Simple substring match against the urgency phrase list. Replace with
    something smarter (fuzzy match / embeddings) only if this proves too
    brittle against real transcripts."""
    lower = transcript.lower()
    return [p for p in URGENCY_PHRASES if p in lower]


def score(features: dict, transcript: Optional[str] = None) -> dict:
    """
    Main entry point. `features` should contain:
        recipient_is_new (bool)
        amount (float)
        avg_transfer_amount (float)
        hour_of_day (int)
        urgency_phrases (list[str])  -- pass pre-extracted, or pass `transcript`
                                        and this function will extract them

    Returns: {"risk_level": "LOW"|"MEDIUM"|"HIGH", "score": float, "reasons": [str]}
    """
    urgency_phrases = features.get("urgency_phrases")
    if urgency_phrases is None and transcript:
        urgency_phrases = extract_urgency_phrases(transcript)
    urgency_phrases = urgency_phrases or []

    inp = TrustScoreInput(
        recipient_is_new=features["recipient_is_new"],
        amount=features["amount"],
        avg_transfer_amount=features.get("avg_transfer_amount", 0),
        hour_of_day=features.get("hour_of_day", 12),
        urgency_phrases=urgency_phrases,
    )

    reasons = []
    total = 0.0

    if inp.recipient_is_new:
        total += WEIGHTS["new_recipient"]
        reasons.append("Recipient not in known transfer history")

    dev = _amount_deviation_score(inp.amount, inp.avg_transfer_amount)
    if dev > 0:
        total += WEIGHTS["amount_deviation"] * dev
        reasons.append(
            f"Amount is {inp.amount / inp.avg_transfer_amount:.1f}x the user's average"
            if inp.avg_transfer_amount
            else "No transfer history to compare amount against"
        )

    hour_score = _unusual_hour_score(inp.hour_of_day)
    if hour_score > 0:
        total += WEIGHTS["unusual_hour"] * hour_score
        reasons.append(f"Unusual transfer time ({inp.hour_of_day}:00)")

    urgency = _urgency_score(inp.urgency_phrases)
    if urgency > 0:
        total += WEIGHTS["urgency_language"] * urgency
        reasons.append(f"Urgency/pressure language detected: {inp.urgency_phrases}")

    total = min(total, 1.0)

    if total < RISK_THRESHOLDS["LOW"]:
        risk_level = "LOW"
    elif total < RISK_THRESHOLDS["MEDIUM"]:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    return {
        "risk_level": risk_level,
        "score": round(total, 3),
        "reasons": reasons or ["No risk signals detected"],
    }


if __name__ == "__main__":
    # Quick manual sanity check — run `python rule_based.py`
    example = {
        "recipient_is_new": True,
        "amount": 150000,
        "avg_transfer_amount": 12000,
        "hour_of_day": 23,
    }
    transcript = "Send 150000 to this new account for the customs officer, he says my package is stuck and needs it now"
    print(score(example, transcript=transcript))
```

- [ ] File created, `python rule_based.py` runs and prints a sensible HIGH-risk result for the example scam transcript

---

## Phase 2 — Build the Decision Agent

`backend/app/agents/decision_agent.py` is what Agoro's orchestrator actually calls. It wraps your scorer and turns a risk level into an action:

```python
"""
Decision Agent — risk-level routing + final release/escalate call.
Owner: Toluwalase Ajiboye
"""
from trust_score.rule_based import score

# Simple routing table — tune as you see real results.
ACTION_BY_RISK = {
    "LOW": "release",
    "MEDIUM": "hold",
    "HIGH": "hold",
}


def evaluate_transfer(features: dict, transcript: str = None) -> dict:
    """
    Called by orchestrator.py right after ASR produces a transcript.
    Returns everything the orchestrator needs to decide what happens next.
    """
    result = score(features, transcript=transcript)
    result["action"] = ACTION_BY_RISK[result["risk_level"]]
    return result


def finalize_decision(risk_level: str, user_confirmed: bool) -> str:
    """
    Called after the user responds to the TTS question / Confirmation Card.
    Returns the final status to write to the Trust Ledger.
    """
    if risk_level == "LOW":
        return "released"
    if user_confirmed:
        return "released"
    if risk_level == "HIGH":
        return "escalated"
    return "held"  # medium risk, not confirmed — stays on hold pending human review
```

- [ ] `decision_agent.py` created
- [ ] `/trust/score` endpoint wired to `evaluate_transfer()` (coordinate with Agoro on exact request/response format — his `orchestrator.py` calls this)

---

## Phase 3 — Get Test Data From Darius, Tune Your Weights

You can't validate the scorer without realistic examples. Darius owns generating these, but **you should tell him exactly what you need**:
- 15-20 scam call transcripts (varied: "customs officer," "account frozen," fake investment, romance scam pressure)
- 15-20 genuine, everyday transfer transcripts (so you can check you're not over-flagging normal transfers)

Once you have them:
- [ ] Run every transcript through `score()`, log the results
- [ ] Check: does every real scam call come back MEDIUM/HIGH? Does every genuine call come back LOW?
- [ ] If not, adjust `WEIGHTS` and `RISK_THRESHOLDS` in `rule_based.py`, or add missing phrases to `URGENCY_PHRASES`
- [ ] Write down your false-positive rate (genuine calls wrongly flagged) and false-negative rate (scams wrongly missed) — this is a direct benchmark number for the pitch

---

## Phase 4 — Build the Benchmark Harness

`ml/benchmarks/run_asr_benchmark.py` — this produces the concrete numbers judges will actually look at:

```python
"""
Benchmark harness: measures ASR quality + downstream risk-detection quality.
Owner: Toluwalase Ajiboye

Run against Darius's synthetic scam/genuine call sets.
"""
import json
from pathlib import Path
from trust_score.rule_based import score

def word_error_rate(reference: str, hypothesis: str) -> float:
    """Basic WER via edit distance on word sequences."""
    ref_words = reference.lower().split()
    hyp_words = hypothesis.lower().split()
    m, n = len(ref_words), len(hyp_words)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    return dp[m][n] / max(m, 1)


def run_intervention_benchmark(labeled_calls: list[dict]) -> dict:
    """
    labeled_calls: [{"transcript": ..., "features": ..., "is_scam": bool}, ...]
    Returns false-positive rate, false-negative rate, and per-call results.
    """
    results = []
    false_positives = 0  # genuine flagged as risky
    false_negatives = 0  # scam not flagged as risky

    for call in labeled_calls:
        result = score(call["features"], transcript=call["transcript"])
        flagged = result["risk_level"] in ("MEDIUM", "HIGH")

        if flagged and not call["is_scam"]:
            false_positives += 1
        if not flagged and call["is_scam"]:
            false_negatives += 1

        results.append({**result, "is_scam": call["is_scam"], "flagged": flagged})

    total = len(labeled_calls)
    return {
        "total_calls": total,
        "false_positive_rate": false_positives / total if total else 0,
        "false_negative_rate": false_negatives / total if total else 0,
        "per_call_results": results,
    }


if __name__ == "__main__":
    # Point this at whatever Darius's generator scripts produce
    data_path = Path("ml/data/synthetic/labeled_calls.json")
    labeled_calls = json.loads(data_path.read_text())
    print(run_intervention_benchmark(labeled_calls))
```

- [ ] Harness runs against Darius's generated call set
- [ ] False-positive rate and false-negative rate recorded — this is your pitch-deck number
- [ ] (Optional, if Agoro's ASR is ready) also run transcripts through actual Sahara output vs. the "ground truth" script text to get a real WER number

---

## Phase 5 — Only If Time Allows: XGBoost

Do not start this until Phases 1-4 above are done and demoed working end-to-end. If there's genuinely spare time:
- [ ] Use the labeled call set from Phase 3/4 as training data (it'll be small — treat this as a proof-of-concept, not production-grade)
- [ ] Train in `ml/trust_score/train_xgboost.py`, keeping the same `score()` input/output contract
- [ ] Compare its false-positive/false-negative rate against the rule-based baseline — if it's not clearly better, **stick with the rule-based version for the demo**, since it's more explainable anyway

---

## You're Done With Your Core Part When:
- `rule_based.py` correctly scores a scam transcript as HIGH and a genuine transcript as LOW
- `decision_agent.py` is wired into Agoro's orchestrator via `/trust/score`
- You have real false-positive/false-negative numbers from Darius's test data
- Every risk decision comes with human-readable `reasons` that David's Trust Ledger view can display directly
