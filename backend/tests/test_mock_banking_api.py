from __future__ import annotations

import pytest
from app.services import mock_banking_api as bank


def test_hold_then_release_lifecycle_is_idempotent():
    pending = bank.initiate_transfer(25_000, "Ada Okafor", user_id="usr_1")
    held = bank.soft_hold(pending["transaction_id"])
    held_again = bank.soft_hold(pending["transaction_id"])
    released = bank.release(pending["transaction_id"])

    assert pending["status"] is bank.TransferStatus.PENDING
    assert held["status"] is bank.TransferStatus.HELD
    assert held_again == held
    assert released["status"] is bank.TransferStatus.RELEASED
    assert (
        bank.get_transfer(pending["transaction_id"])["status"]
        is bank.TransferStatus.RELEASED
    )


def test_snapshots_cannot_mutate_internal_bank_state():
    transfer = bank.initiate_transfer(10_000, "Chidi")
    transfer["amount"] = 1

    assert bank.get_transfer(transfer["transaction_id"])["amount"] == 10_000


def test_terminal_transition_is_rejected():
    transfer = bank.initiate_transfer(10_000, "Chidi")
    bank.release(transfer["transaction_id"])

    with pytest.raises(bank.InvalidTransitionError, match="Cannot move"):
        bank.escalate(transfer["transaction_id"])


@pytest.mark.parametrize("amount", [0, -1, float("inf"), float("nan")])
def test_invalid_amounts_are_rejected(amount):
    with pytest.raises(bank.BankingError):
        bank.initiate_transfer(amount, "Ada")


def test_reusing_id_with_different_details_is_rejected():
    bank.initiate_transfer(10_000, "Ada", transaction_id="tx_stable")

    with pytest.raises(bank.BankingError, match="different details"):
        bank.initiate_transfer(11_000, "Ada", transaction_id="tx_stable")
