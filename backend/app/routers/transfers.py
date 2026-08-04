"""
Transfer decision + confirmation endpoints.
Owner: Agoro Oluwatimilehin (routing) + Toluwalase Ajiboye (decision logic)

Contract:
POST /transfers/decision -> { status: released | held | escalated, message, transfer_id }
"""
import uuid
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class ConfirmationData(BaseModel):
    verified_pin: Optional[bool] = False
    security_question_answer: Optional[str] = None

class TransferDecisionRequest(BaseModel):
    user_id: str = "usr_default"
    amount: float
    recipient: str
    risk_level: str
    user_confirmation: Optional[ConfirmationData] = None

@router.post("/decision")
def transfer_decision(request: TransferDecisionRequest):
    """
    Evaluates final user confirmation and returns execution decision (released | held | escalated).
    """
    transfer_id = f"tx_{uuid.uuid4().hex[:8]}"
    ledger_id = f"led_{uuid.uuid4().hex[:8]}"

    if request.risk_level == "LOW":
        return {
            "status": "released",
            "transfer_id": transfer_id,
            "ledger_entry_id": ledger_id,
            "message": "Transfer released successfully."
        }

    # If MEDIUM/HIGH risk, evaluate user confirmation inputs
    if request.user_confirmation and request.user_confirmation.verified_pin:
        return {
            "status": "released",
            "transfer_id": transfer_id,
            "ledger_entry_id": ledger_id,
            "message": "Transfer released following successful user PIN verification."
        }
    
    return {
        "status": "held",
        "transfer_id": transfer_id,
        "ledger_entry_id": ledger_id,
        "message": "Transfer placed on soft hold pending further identity verification."
    }
