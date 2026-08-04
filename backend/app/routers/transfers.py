"""
Transfer decision + confirmation endpoints.
Owner: Agoro Oluwatimilehin (routing) + Toluwalase Ajiboye (decision logic)

Contract:
POST /transfers/decision -> { status: released | held | escalated, message, transfer_id }
"""
from datetime import datetime, timezone
import uuid
from typing import Optional, List
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

LEDGER: List[dict] = []

class ConfirmationData(BaseModel):
    verified_pin: Optional[bool] = False
    security_question_answer: Optional[str] = None

class TransferDecisionRequest(BaseModel):
    user_id: str = "usr_default"
    amount: float
    recipient: str
    risk_level: str
    transaction_id: Optional[str] = None
    transcript: Optional[str] = None
    reasons: Optional[List[str]] = None
    user_confirmation: Optional[ConfirmationData] = None


@router.get("/ledger")
def get_ledger():
    """
    Returns the most recent ledger entries first.
    """
    return list(LEDGER)


@router.post("/decision")
def transfer_decision(request: TransferDecisionRequest):
    """
    Evaluates final user confirmation and returns execution decision (released | held | escalated).
    """
    transfer_id = f"tx_{uuid.uuid4().hex[:8]}"
    ledger_id = f"led_{uuid.uuid4().hex[:8]}"

    risk_level = request.risk_level.upper()
    status = "held"

    if risk_level == "LOW":
        status = "released"
    elif request.user_confirmation and request.user_confirmation.verified_pin:
        status = "released"
    elif request.user_confirmation is not None and not request.user_confirmation.verified_pin:
        status = "held"
    elif risk_level == "HIGH":
        status = "escalated"

    message_map = {
        "released": "Transfer released successfully.",
        "held": "Transfer placed on soft hold pending further identity verification.",
        "escalated": "Transfer escalated for manual review.",
    }

    ledger_entry = {
        "id": len(LEDGER) + 1,
        "transaction_id": request.transaction_id or transfer_id,
        "transcript": request.transcript,
        "amount": request.amount,
        "recipient": request.recipient,
        "risk_level": risk_level,
        "reasons": request.reasons or [],
        "action": status,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    LEDGER.insert(0, ledger_entry)

    return {
        "status": status,
        "transfer_id": transfer_id,
        "ledger_entry_id": ledger_id,
        "message": message_map[status],
        "ledger_entry": ledger_entry,
    }
