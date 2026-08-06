"""Shared schema and validation helpers for synthetic benchmark calls."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_FEATURES = {
    "recipient_is_new",
    "amount",
    "avg_transfer_amount",
    "hour_of_day",
    "urgency_phrases",
}


def make_case(
    case_id: str,
    category: str,
    transcript: str,
    *,
    is_scam: bool,
    recipient_is_new: bool,
    amount: float,
    avg_transfer_amount: float,
    hour_of_day: int,
    urgency_phrases: list[str] | None = None,
    language: str = "English",
) -> dict[str, Any]:
    return {
        "id": case_id,
        "category": category,
        "language": language,
        "transcript": transcript,
        "features": {
            "recipient_is_new": recipient_is_new,
            "amount": amount,
            "avg_transfer_amount": avg_transfer_amount,
            "hour_of_day": hour_of_day,
            "urgency_phrases": urgency_phrases or [],
        },
        "is_scam": is_scam,
    }


def validate_dataset(
    calls: list[dict[str, Any]], *, minimum_per_class: int = 15
) -> None:
    """Fail loudly when benchmark data becomes malformed or shortcut-prone."""
    if not calls:
        raise ValueError("Synthetic dataset cannot be empty.")

    ids: set[str] = set()
    transcripts: set[str] = set()
    labels: dict[bool, list[dict[str, Any]]] = {True: [], False: []}

    for index, call in enumerate(calls):
        missing = {
            "id",
            "category",
            "language",
            "transcript",
            "features",
            "is_scam",
        } - call.keys()
        if missing:
            raise ValueError(f"Call {index} is missing keys: {sorted(missing)}")

        case_id = call["id"]
        normalized_transcript = " ".join(call["transcript"].casefold().split())
        if case_id in ids:
            raise ValueError(f"Duplicate call id: {case_id}")
        if normalized_transcript in transcripts:
            raise ValueError(f"Duplicate transcript: {call['transcript']}")
        ids.add(case_id)
        transcripts.add(normalized_transcript)

        if not isinstance(call["is_scam"], bool):
            raise TypeError(f"Call {case_id} has a non-boolean label.")
        labels[call["is_scam"]].append(call)

        features = call["features"]
        missing_features = REQUIRED_FEATURES - features.keys()
        if missing_features:
            raise ValueError(
                f"Call {case_id} is missing features: {sorted(missing_features)}"
            )
        if not isinstance(features["recipient_is_new"], bool):
            raise TypeError(f"Call {case_id} recipient_is_new must be boolean.")
        if features["amount"] <= 0 or features["avg_transfer_amount"] < 0:
            raise ValueError(f"Call {case_id} contains invalid monetary values.")
        if not 0 <= features["hour_of_day"] <= 23:
            raise ValueError(f"Call {case_id} hour_of_day must be in 0..23.")
        if not isinstance(features["urgency_phrases"], list):
            raise TypeError(f"Call {case_id} urgency_phrases must be a list.")

    for label, class_calls in labels.items():
        class_name = "scam" if label else "genuine"
        if len(class_calls) < minimum_per_class:
            raise ValueError(
                f"Need at least {minimum_per_class} {class_name} calls; got {len(class_calls)}."
            )
        if {call["features"]["recipient_is_new"] for call in class_calls} != {
            True,
            False,
        }:
            raise ValueError(
                f"{class_name.title()} calls need both new- and known-recipient examples."
            )
        if len({call["category"] for call in class_calls}) < 5:
            raise ValueError(
                f"{class_name.title()} calls need at least five categories."
            )


def write_json(path: Path, calls: list[dict[str, Any]]) -> None:
    path.write_text(
        json.dumps(calls, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
