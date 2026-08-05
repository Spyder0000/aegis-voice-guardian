"""
Trains the rules + XGBoost hybrid Trust Score classifier on synthetic data.
Decides the risk level of a transfer request based on the json feeding it 
Owner: Toluwalase Ajiboye
"""
"""
{
    "id": "genuine-social-011",
    "category": "shared_expense",
    "language": "English",
    "transcript": "I just met Chika at dinner, send her 5000 naira for my half of the bill",
    "features": {
      "recipient_is_new": true,
      "amount": 5000,
      "avg_transfer_amount": 6000,
      "hour_of_day": 22,
      "urgency_phrases": []
    },
    "is_scam": false
  }

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
from pathlib import Path

# Phrases that signal authority-impersonation / urgency pressure.
# Keep this list growing as Darius's synthetic scam-call scripts get written —
# every real phrase pattern from those scripts should get added here.
# Resolve the phrases file relative to this module so imports succeed
# regardless of the current working directory.
urgency_phrases_file = Path(__file__).resolve().parent / 'urgency_phrases.txt'

try:
    with open(urgency_phrases_file, 'r', encoding='utf-8') as f:
        URGENCY_PHRASES = f.read().splitlines()
except FileNotFoundError:
    URGENCY_PHRASES = []

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

# uncomment if needed for manual testing
# if __name__ == "__main__":
#     # Quick manual sanity check — run `python rule_based.py`
#     example = {
#         "recipient_is_new": True,
#         "amount": 150000,
#         "avg_transfer_amount": 12000,
#         "hour_of_day": 23,
#         "urgency_phrases": ["customs officer", "needs it now"],
#     }
#     transcript = "Send 150000 to this new account for the customs officer, he says my package is stuck and needs it now"
#     print(score(example, transcript=transcript))