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
        "transaction_id": "tx_test",
        "transcript": "Send 50000 naira to Ada Okafor",
        "reasons": ["New recipient"],
    }
    payload.update(overrides)
    return payload


def test_low_risk_releases_and_writes_ledger():
    response = client.post("/transfers/decision", json=_payload(risk_level="LOW"))

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "released"
    assert bank.get_transfer("tx_test")["status"] is bank.TransferStatus.RELEASED

    ledger = client.get("/transfers/ledger").json()
    assert ledger[0]["transaction_id"] == "tx_test"
    assert ledger[0]["action"] == "released"


def test_retried_decision_reuses_the_ledger_entry():
    first = client.post("/transfers/decision", json=_payload(risk_level="LOW"))
    retried = client.post("/transfers/decision", json=_payload(risk_level="LOW"))

    assert retried.status_code == 200
    assert retried.json()["ledger_entry_id"] == first.json()["ledger_entry_id"]
    assert len(client.get("/transfers/ledger").json()) == 1


def test_medium_risk_holds_then_releases_after_verification():
    held = client.post("/transfers/decision", json=_payload())
    released = client.post(
        "/transfers/decision",
        json=_payload(user_confirmation={"verified_pin": True}),
    )

    assert held.status_code == 200
    assert held.json()["status"] == "held"
    assert released.status_code == 200
    assert released.json()["status"] == "released"


def test_unverified_high_risk_transfer_is_escalated():
    response = client.post(
        "/transfers/decision",
        json=_payload(
            risk_level="HIGH",
            user_confirmation={"verified_pin": False},
        ),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "escalated"
    assert bank.get_transfer("tx_test")["status"] is bank.TransferStatus.ESCALATED


def test_request_validation_rejects_bad_money_and_risk_values():
    negative = client.post("/transfers/decision", json=_payload(amount=-1))
    unknown_risk = client.post(
        "/transfers/decision", json=_payload(risk_level="CRITICAL")
    )

    assert negative.status_code == 422
    assert unknown_risk.status_code == 422
