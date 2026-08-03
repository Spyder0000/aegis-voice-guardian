"""
Transfer decision + confirmation endpoints.
Owner: Agoro Oluwatimilehin (routing) + Toluwalase Ajiboye (decision logic)

Contract:
POST /trust/score        -> { risk_level, score, reasons }
POST /transfers/decision -> { status: released | held | escalated }
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/decision")
def transfer_decision():
    # TODO: call app.agents.decision_agent
    raise NotImplementedError
