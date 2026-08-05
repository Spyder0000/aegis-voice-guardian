"""Transfer decisions, mock-bank execution, and explainable ledger access."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, PositiveFloat
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.repository import (
    LedgerConflictError,
    list_ledger_entries,
    record_ledger_entry,
)
from app.db.session import get_db
from app.services import mock_banking_api as bank

router = APIRouter()

# Used only when DATABASE_URL is intentionally absent (quick local/demo mode).
_MEMORY_LEDGER: list[dict] = []


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ConfirmationData(BaseModel):
    # This flag represents a result from a mock verification service. A real
    # deployment must never accept raw PIN material or trust a browser claim.
    verified_pin: bool = False
    security_question_answer: str | None = Field(default=None, max_length=256)


class TransferDecisionRequest(BaseModel):
    user_id: str = Field(default="usr_default", min_length=1, max_length=128)
    amount: PositiveFloat
    recipient: str = Field(min_length=1, max_length=256)
    risk_level: RiskLevel
    transaction_id: str | None = Field(default=None, min_length=1, max_length=128)
    transcript: str | None = Field(default=None, max_length=10_000)
    reasons: list[str] = Field(default_factory=list, max_length=25)
    user_confirmation: ConfirmationData | None = None


DbSession = Annotated[Session | None, Depends(get_db)]


@router.get("/ledger")
def get_ledger(
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[dict]:
    """Return the most recent explainable decisions first."""
    if db is None:
        return list(_MEMORY_LEDGER[:limit])

    try:
        return list_ledger_entries(db, limit=limit)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Trust ledger storage is temporarily unavailable.",
        ) from exc


@router.post("/decision")
def transfer_decision(request: TransferDecisionRequest, db: DbSession) -> dict:
    """Execute the risk decision through the mock bank and record its rationale.

    LOW risk releases immediately. MEDIUM/HIGH risk is held first; a verified
    confirmation releases it, MEDIUM without verification remains held, and
    HIGH without verification is escalated for human review.
    """
    try:
        transfer = bank.initiate_transfer(
            request.amount,
            request.recipient,
            user_id=request.user_id,
            transaction_id=request.transaction_id,
        )
        transaction_id = transfer["transaction_id"]

        if request.risk_level is RiskLevel.LOW:
            transfer = bank.release(transaction_id)
        else:
            if transfer["status"] == bank.TransferStatus.PENDING:
                transfer = bank.soft_hold(transaction_id)

            if request.user_confirmation and request.user_confirmation.verified_pin:
                transfer = bank.release(transaction_id)
            elif request.risk_level is RiskLevel.HIGH:
                transfer = bank.escalate(transaction_id)
    except bank.BankingError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    action = bank.TransferStatus(transfer["status"]).value
    ledger_id = f"led_{uuid.uuid4().hex}"
    created_at = datetime.now(timezone.utc)
    ledger_entry = {
        "id": ledger_id,
        "transaction_id": transaction_id,
        "user_id": request.user_id,
        "transcript": request.transcript,
        "amount": float(request.amount),
        "recipient": request.recipient.strip(),
        "risk_level": request.risk_level.value,
        "reasons": request.reasons,
        "action": action,
        "created_at": created_at,
    }

    if db is None:
        public_entry = next(
            (
                existing
                for existing in _MEMORY_LEDGER
                if existing["transaction_id"] == transaction_id
                and existing["action"] == action
            ),
            None,
        )
        if public_entry is None:
            public_entry = {
                **ledger_entry,
                "created_at": created_at.isoformat().replace("+00:00", "Z"),
            }
            _MEMORY_LEDGER.insert(0, public_entry)
    else:
        try:
            public_entry = record_ledger_entry(db, ledger_entry)
        except LedgerConflictError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The bank action completed, but the trust ledger could not be written.",
            ) from exc

    message_map = {
        "released": "Transfer released successfully.",
        "held": "Transfer remains on soft hold pending identity verification.",
        "escalated": "Transfer escalated for manual review.",
    }
    return {
        "status": action,
        "transfer_id": transaction_id,
        "ledger_entry_id": public_entry["id"],
        "message": message_map[action],
        "ledger_entry": public_entry,
    }


def reset_memory_ledger() -> None:
    """Clear fallback state for isolated tests."""
    _MEMORY_LEDGER.clear()
