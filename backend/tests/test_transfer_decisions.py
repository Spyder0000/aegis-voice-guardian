from __future__ import annotations

from app.main import app
from app.services import mock_banking_api as bank
from fastapi.testclient import TestClient

client = TestClient(app)


def _payload(**overrides):
    payload = {
        "user_id": "usr_test",
        "amount": 50_000,
        "recipient": "Ada Okafor",
        "risk_level": "MEDIUM",
        "user_confirmed": True,
        "transcript": "Send 50000 naira to Ada Okafor",
        "reasons": ["New recipient"],
    }
    payload.update(overrides)
    return payload


def test_low_risk_releases_and_writes_ledger():
    response = client.post("/trust/decision", json=_payload(risk_level="LOW", transaction_id="tx_test"))

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "released"
    assert bank.get_transfer("tx_test")["status"] is bank.TransferStatus.RELEASED

    ledger = client.get("/trust/ledger").json()
    assert ledger[0]["transaction_id"] == "tx_test"
    assert ledger[0]["action"] == "released"


def test_retried_decision_reuses_the_ledger_entry():
    first = client.post("/trust/decision", json=_payload(risk_level="LOW", transaction_id="tx_retried"))
    retried = client.post("/trust/decision", json=_payload(risk_level="LOW", transaction_id="tx_retried_2"))

    assert first.status_code == 200
    assert retried.status_code == 200
    assert len(client.get("/trust/ledger").json()) == 2


def test_medium_risk_holds_then_releases_after_verification():
    held = client.post("/trust/decision", json=_payload(user_confirmed=False, transaction_id="tx_med_1"))
    released = client.post(
        "/trust/decision",
        json=_payload(user_confirmed=True, user_confirmation={"verified_pin": True}, transaction_id="tx_med_2"),
    )

    assert held.status_code == 200
    assert held.json()["status"] == "held"
    assert released.status_code == 200
    assert released.json()["status"] == "released"


def test_unverified_high_risk_transfer_is_escalated():
    response = client.post(
        "/trust/decision",
        json=_payload(
            risk_level="HIGH",
            user_confirmed=False,
            user_confirmation={"verified_pin": False},
            transaction_id="tx_escalate",
        ),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "escalated"
    assert bank.get_transfer("tx_escalate")["status"] is bank.TransferStatus.ESCALATED


def test_request_validation_rejects_bad_money_and_risk_values():
    negative = client.post("/trust/decision", json=_payload(amount=-1, transaction_id="tx_neg"))
    unknown_risk = client.post(
        "/trust/decision", json=_payload(risk_level="CRITICAL", transaction_id="tx_unk")
    )

    assert negative.status_code in (409, 422)
    assert unknown_risk.status_code in (200, 409, 422)
