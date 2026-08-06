"""Persistence operations for trust profiles and decision ledger entries."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import TrustLedger, TrustProfile


class LedgerConflictError(ValueError):
    """Raised when an idempotency key is reused for different transfer details."""


def _money(value: float | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def ensure_profile(db: Session, user_id: str) -> TrustProfile:
    profile = db.get(TrustProfile, user_id)
    if profile is None:
        profile = TrustProfile(user_id=user_id)
        db.add(profile)
        db.flush()
    return profile


def _update_profile_for_release(
    profile: TrustProfile, *, amount: Decimal, recipient: str
) -> None:
    previous_count = profile.transfer_count or 0
    previous_average = profile.avg_transfer_amount or Decimal(0)
    next_count = previous_count + 1

    profile.avg_transfer_amount = (
        (previous_average * previous_count) + amount
    ) / next_count
    profile.largest_transfer_amount = max(
        profile.largest_transfer_amount or Decimal(0), amount
    )
    profile.transfer_count = next_count

    known_recipients = list(profile.known_recipients or [])
    if recipient.casefold() not in {known.casefold() for known in known_recipients}:
        known_recipients.append(recipient)
    profile.known_recipients = known_recipients

    transfer_counts = dict(profile.recipient_transfer_counts or {})
    normalized_recipient = recipient.casefold()
    transfer_counts[normalized_recipient] = (
        transfer_counts.get(normalized_recipient, 0) + 1
    )
    profile.recipient_transfer_counts = transfer_counts
    profile.updated_at = datetime.now(timezone.utc)


def record_ledger_entry(db: Session, entry: dict[str, Any]) -> dict[str, Any]:
    """Persist a decision and update the profile atomically on release."""
    amount = _money(entry["amount"])
    existing = db.scalar(
        select(TrustLedger).where(
            TrustLedger.transaction_id == entry["transaction_id"],
            TrustLedger.action == entry["action"],
        )
    )
    if existing is not None:
        matches = (
            existing.user_id == entry["user_id"]
            and existing.amount == amount
            and existing.recipient == entry["recipient"]
            and existing.risk_level == entry["risk_level"]
        )
        if not matches:
            raise LedgerConflictError(
                "Transaction id and action already exist with different ledger details."
            )
        return serialize_ledger(existing)

    profile = ensure_profile(db, entry["user_id"])

    if entry["action"] == "released":
        _update_profile_for_release(
            profile, amount=amount, recipient=entry["recipient"]
        )

    row = TrustLedger(
        id=entry["id"],
        transaction_id=entry["transaction_id"],
        user_id=entry["user_id"],
        transcript=entry.get("transcript"),
        amount=amount,
        recipient=entry["recipient"],
        risk_level=entry["risk_level"],
        reasons=list(entry.get("reasons") or []),
        action=entry["action"],
        created_at=entry["created_at"],
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return serialize_ledger(row)


def list_ledger_entries(db: Session, *, limit: int = 100) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(TrustLedger)
        .order_by(TrustLedger.created_at.desc())
        .limit(max(1, min(limit, 500)))
    ).all()
    return [serialize_ledger(row) for row in rows]


def serialize_ledger(row: TrustLedger) -> dict[str, Any]:
    created_at = row.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return {
        "id": row.id,
        "transaction_id": row.transaction_id,
        "user_id": row.user_id,
        "transcript": row.transcript,
        "amount": float(row.amount),
        "recipient": row.recipient,
        "risk_level": row.risk_level,
        "reasons": list(row.reasons or []),
        "action": row.action,
        "created_at": created_at.astimezone(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
    }
