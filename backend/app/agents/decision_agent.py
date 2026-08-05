"""
Decision Agent — risk-level routing + final release/escalate call.
Owner: Toluwalase Ajiboye

TODO: consume Trust Score output + user confirmation response,
      return final transfer status, write rationale to Trust Ledger.
"""
from ml.trust_score.rule_based import score

# Simple routing table — tune as you see real results.
ACTION_BY_RISK = {
    "LOW": "release",
    "MEDIUM": "hold",
    "HIGH": "hold",
}


def evaluate_transfer(features: dict, transcript: str = "") -> dict: # too shallow add more evaluators
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
