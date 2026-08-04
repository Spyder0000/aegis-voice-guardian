"""
Sandboxed mock banking API — soft hold / release / escalate.
Owner: Okoh Darius

In-memory stub simulating a real banking transfer API for the demo.
Swap for a real sandbox API only if time allows and it's genuinely useful —
for the hackathon, this stub is enough to prove the concept.
"""
import uuid
from datetime import datetime
from enum import Enum


class TransferStatus(str, Enum):
    PENDING = "pending"
    HELD = "held"
    RELEASED = "released"
    ESCALATED = "escalated"


# In-memory store — fine for a hackathon demo, swap for real DB writes
# if Darius has time to wire this into the Postgres schema below.
_transfers = {}


def initiate_transfer(amount: float, recipient: str) -> dict:
    """Called when a voice transfer request first comes in."""
    txn_id = str(uuid.uuid4())
    _transfers[txn_id] = {
        "transaction_id": txn_id,
        "amount": amount,
        "recipient": recipient,
        "status": TransferStatus.PENDING,
        "created_at": datetime.utcnow().isoformat(),
    }
    return _transfers[txn_id]


def soft_hold(txn_id: str) -> dict:
    """Called by the orchestrator when risk is MEDIUM/HIGH."""
    txn = _transfers.get(txn_id)
    if not txn:
        raise ValueError(f"Unknown transaction: {txn_id}")
    txn["status"] = TransferStatus.HELD
    return txn


def release(txn_id: str) -> dict:
    """Called when risk is LOW, or the user confirms a held transfer."""
    txn = _transfers.get(txn_id)
    if not txn:
        raise ValueError(f"Unknown transaction: {txn_id}")
    txn["status"] = TransferStatus.RELEASED
    return txn


def escalate(txn_id: str) -> dict:
    """Called when risk is HIGH and the user doesn't confirm, or rejects."""
    txn = _transfers.get(txn_id)
    if not txn:
        raise ValueError(f"Unknown transaction: {txn_id}")
    txn["status"] = TransferStatus.ESCALATED
    return txn


def get_transfer(txn_id: str) -> dict:
    txn = _transfers.get(txn_id)
    if not txn:
        raise ValueError(f"Unknown transaction: {txn_id}")
    return txn
