"""Transfer decisions, mock-bank execution, and explainable ledger access."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, PositiveFloat
try:
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.orm import Session
except ImportError:
    SQLAlchemyError = Exception
    Session = Any

from ml.trust_score.contract_adapter import score_from_contract
from ml.trust_score.decision_agent import finalize_decision

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


class EntitiesModel(BaseModel):
    urgency_phrases: list[str] = Field(default_factory=list)
    authority_claim: bool = False
    bank_keywords: list[str] = Field(default_factory=list)


class UserProfileModel(BaseModel):
    average_transfer: float = 0.0
    largest_transfer: float = 0.0
    recipient_seen_before: bool = False
    transfer_count_to_recipient: int = 0


class TrustScoreContractRequest(BaseModel):
    transcript: str | None = None
    recipient: str | None = None
    amount: float | None = None
    currency: str = "NGN"
    timestamp: str | None = None
    intent: str | None = None
    language: str | None = None
    entities: EntitiesModel = Field(default_factory=EntitiesModel)
    user_profile: UserProfileModel = Field(default_factory=UserProfileModel)


class DecisionFinalizeRequest(BaseModel):
    risk_level: str | None = None
    user_confirmed: bool | None = None
    # Optional transaction fields
    user_id: str = "usr_default"
    amount: float | None = None
    recipient: str | None = None
    transaction_id: str | None = None
    transcript: str | None = None
    reasons: list[str] = Field(default_factory=list)
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


@router.post("/score")
def compute_trust_score(request: TrustScoreContractRequest) -> dict:
    """Compute trust score using contract payload schema."""
    if request.amount is None or request.recipient is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required field: 'recipient' and 'amount' must be provided.",
        )
    payload = request.model_dump()
    return score_from_contract(payload)


@router.post("/decision")
def transfer_decision(
    request: DecisionFinalizeRequest,
    db: DbSession = None,
) -> dict:
    """Execute risk decision routing and record rationale to the trust ledger."""
    if request.risk_level is None or request.user_confirmed is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required field: 'risk_level' and 'user_confirmed' must be provided.",
        )

    final_status = finalize_decision(request.risk_level, request.user_confirmed)

    amount = float(request.amount or 0.0)
    recipient = (request.recipient or "N/A").strip()
    transaction_id = request.transaction_id or f"tx_{uuid.uuid4().hex[:12]}"

    if request.amount is not None and request.recipient is not None:
        try:
            transfer = bank.initiate_transfer(
                request.amount,
                request.recipient,
                user_id=request.user_id,
                transaction_id=transaction_id,
            )
            transaction_id = transfer["transaction_id"]

            if final_status == "released":
                transfer = bank.release(transaction_id)
            elif final_status == "escalated":
                transfer = bank.escalate(transaction_id)
            else:
                transfer = bank.soft_hold(transaction_id)
        except bank.BankingError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc

    ledger_id = f"led_{uuid.uuid4().hex}"
    created_at = datetime.now(timezone.utc)
    ledger_entry = {
        "id": ledger_id,
        "transaction_id": transaction_id,
        "user_id": request.user_id,
        "transcript": request.transcript,
        "amount": amount,
        "recipient": recipient,
        "risk_level": request.risk_level,
        "reasons": request.reasons,
        "action": final_status,
        "created_at": created_at,
    }

    if db is None:
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
                detail="The decision completed, but the trust ledger could not be written.",
            ) from exc

    message_map = {
        "released": "Transfer released successfully.",
        "held": "Transfer remains on soft hold pending identity verification.",
        "escalated": "Transfer escalated for manual review.",
    }
    return {
        "status": final_status,
        "transfer_id": transaction_id,
        "ledger_entry_id": public_entry["id"],
        "message": message_map.get(final_status, "Transfer decision completed."),
        "ledger_entry": public_entry,
    }


def reset_memory_ledger() -> None:
    """Clear fallback state for isolated tests."""
    _MEMORY_LEDGER.clear()
