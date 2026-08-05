"""Thread-safe mock banking lifecycle used by the AEGIS demo.

The service deliberately models only bank-side transfer state. Risk decisions
belong to the orchestrator/decision endpoint, which calls these transitions.
No real funds or credentials are handled here.
"""

from __future__ import annotations

import math
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from enum import Enum
from threading import RLock
from typing import Any


class TransferStatus(str, Enum):
    PENDING = "pending"
    HELD = "held"
    RELEASED = "released"
    ESCALATED = "escalated"


class BankingError(ValueError):
    """Base class for predictable mock-bank errors."""


class TransferNotFoundError(BankingError):
    """Raised when a transaction id is unknown to the mock bank."""


class InvalidTransitionError(BankingError):
    """Raised when a terminal or otherwise illegal transition is requested."""


_transfers: dict[str, dict[str, Any]] = {}
_lock = RLock()

_ALLOWED_TRANSITIONS = {
    TransferStatus.PENDING: {
        TransferStatus.HELD,
        TransferStatus.RELEASED,
        TransferStatus.ESCALATED,
    },
    TransferStatus.HELD: {TransferStatus.RELEASED, TransferStatus.ESCALATED},
    TransferStatus.RELEASED: set(),
    TransferStatus.ESCALATED: set(),
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _snapshot(transfer: dict[str, Any]) -> dict[str, Any]:
    """Return a copy so callers cannot mutate the bank's internal state."""
    return deepcopy(transfer)


def _require_transfer(transaction_id: str) -> dict[str, Any]:
    transfer = _transfers.get(transaction_id)
    if transfer is None:
        raise TransferNotFoundError(f"Unknown transaction: {transaction_id}")
    return transfer


def initiate_transfer(
    amount: float,
    recipient: str,
    *,
    user_id: str = "usr_default",
    transaction_id: str | None = None,
) -> dict[str, Any]:
    """Create a pending transfer, or return the same matching transfer.

    Accepting an optional transaction id lets the API preserve a client/demo
    correlation id while still enforcing idempotency and immutable details.
    """
    if (
        not isinstance(amount, (int, float))
        or not math.isfinite(float(amount))
        or amount <= 0
    ):
        raise BankingError("Transfer amount must be a finite number greater than zero.")

    clean_recipient = recipient.strip() if isinstance(recipient, str) else ""
    if not clean_recipient:
        raise BankingError("Recipient cannot be empty.")

    clean_user_id = user_id.strip() if isinstance(user_id, str) else ""
    if not clean_user_id:
        raise BankingError("User id cannot be empty.")

    transfer_id = transaction_id or f"tx_{uuid.uuid4().hex}"
    now = _utc_now()

    with _lock:
        existing = _transfers.get(transfer_id)
        if existing is not None:
            matches = (
                existing["amount"] == float(amount)
                and existing["recipient"] == clean_recipient
                and existing["user_id"] == clean_user_id
            )
            if not matches:
                raise BankingError(
                    f"Transaction id {transfer_id!r} already exists with different details."
                )
            return _snapshot(existing)

        transfer = {
            "transaction_id": transfer_id,
            "user_id": clean_user_id,
            "amount": float(amount),
            "recipient": clean_recipient,
            "status": TransferStatus.PENDING,
            "created_at": now,
            "updated_at": now,
        }
        _transfers[transfer_id] = transfer
        return _snapshot(transfer)


def _transition(transaction_id: str, target: TransferStatus) -> dict[str, Any]:
    with _lock:
        transfer = _require_transfer(transaction_id)
        current = TransferStatus(transfer["status"])

        # Repeated delivery of the same command is safe.
        if current == target:
            return _snapshot(transfer)

        if target not in _ALLOWED_TRANSITIONS[current]:
            raise InvalidTransitionError(
                f"Cannot move transaction {transaction_id!r} from {current.value} "
                f"to {target.value}."
            )

        transfer["status"] = target
        transfer["updated_at"] = _utc_now()
        return _snapshot(transfer)


def soft_hold(transaction_id: str) -> dict[str, Any]:
    """Place a pending transfer on hold for additional verification."""
    return _transition(transaction_id, TransferStatus.HELD)


def release(transaction_id: str) -> dict[str, Any]:
    """Release a pending/held transfer after the decision gate passes."""
    return _transition(transaction_id, TransferStatus.RELEASED)


def escalate(transaction_id: str) -> dict[str, Any]:
    """Escalate a pending/held transfer to a human-review queue."""
    return _transition(transaction_id, TransferStatus.ESCALATED)


def get_transfer(transaction_id: str) -> dict[str, Any]:
    with _lock:
        return _snapshot(_require_transfer(transaction_id))


def list_transfers() -> list[dict[str, Any]]:
    """Return newest transfers first; useful for demos and test inspection."""
    with _lock:
        return sorted(
            (_snapshot(transfer) for transfer in _transfers.values()),
            key=lambda transfer: transfer["created_at"],
            reverse=True,
        )


def reset_mock_bank() -> None:
    """Clear all mock state. Intended for isolated automated tests only."""
    with _lock:
        _transfers.clear()
