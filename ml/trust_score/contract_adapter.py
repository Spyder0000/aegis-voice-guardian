"""
Contract adapter: translates the /trust/score API payload (per docs/TRUST_SCORE_CONTRACT.md)
into the flat feature dict decision_agent.evaluate_transfer() expects.
Owner: Toluwalase Ajiboye
"""
from datetime import datetime
from ml.trust_score.decision_agent import evaluate_transfer


def score_from_contract(payload: dict) -> dict:
    entities = payload.get("entities", {})
    profile = payload.get("user_profile", {})

    timestamp = payload.get("timestamp")
    hour_of_day = (
        datetime.fromisoformat(timestamp.replace("Z", "+00:00")).hour
        if timestamp else 12
    )

    features = {
        "recipient_is_new": not profile.get("recipient_seen_before", False),
        "amount": payload["amount"],
        "avg_transfer_amount": profile.get("average_transfer", 0),
        "hour_of_day": hour_of_day,
        "urgency_phrases": entities.get("urgency_phrases", []),
    }

    return evaluate_transfer(features, transcript=payload.get("transcript"))
