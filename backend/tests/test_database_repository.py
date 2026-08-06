from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from app.db.repository import (
    LedgerConflictError,
    list_ledger_entries,
    record_ledger_entry,
)
from app.db.session import Base
from app.models import TrustProfile
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def test_released_decision_persists_and_updates_profile():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    entry = {
        "id": "led_test",
        "transaction_id": "tx_test",
        "user_id": "usr_test",
        "transcript": "Send 20000 naira to Ada",
        "amount": 20_000,
        "recipient": "Ada",
        "risk_level": "LOW",
        "reasons": ["Known recipient"],
        "action": "released",
        "created_at": datetime.now(timezone.utc),
    }

    with Session(engine) as db:
        persisted = record_ledger_entry(db, entry)
        profile = db.get(TrustProfile, "usr_test")
        ledger = list_ledger_entries(db)

        assert persisted["transaction_id"] == "tx_test"
        assert ledger[0]["action"] == "released"
        assert profile is not None
        assert profile.transfer_count == 1
        assert profile.avg_transfer_amount == Decimal("20000.00")
        assert profile.largest_transfer_amount == Decimal("20000.00")
        assert profile.known_recipients == ["Ada"]
        assert profile.recipient_transfer_counts == {"ada": 1}


def test_held_decision_does_not_train_normal_profile():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    entry = {
        "id": "led_held",
        "transaction_id": "tx_held",
        "user_id": "usr_test",
        "transcript": None,
        "amount": 200_000,
        "recipient": "Unknown",
        "risk_level": "HIGH",
        "reasons": ["Scam pressure"],
        "action": "held",
        "created_at": datetime.now(timezone.utc),
    }

    with Session(engine) as db:
        record_ledger_entry(db, entry)
        profile = db.get(TrustProfile, "usr_test")

        assert profile is not None
        assert profile.transfer_count == 0
        assert profile.known_recipients == []


def test_retried_release_is_idempotent_for_ledger_and_profile():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    entry = {
        "id": "led_first",
        "transaction_id": "tx_retry",
        "user_id": "usr_test",
        "transcript": "Send 10000 naira to Ada",
        "amount": 10_000,
        "recipient": "Ada",
        "risk_level": "LOW",
        "reasons": [],
        "action": "released",
        "created_at": datetime.now(timezone.utc),
    }

    with Session(engine) as db:
        first = record_ledger_entry(db, entry)
        retried = record_ledger_entry(db, {**entry, "id": "led_retry"})
        profile = db.get(TrustProfile, "usr_test")

        assert retried == first
        assert len(list_ledger_entries(db)) == 1
        assert profile is not None
        assert profile.transfer_count == 1


def test_reused_transaction_action_with_different_details_is_rejected():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    entry = {
        "id": "led_first",
        "transaction_id": "tx_conflict",
        "user_id": "usr_test",
        "transcript": None,
        "amount": 10_000,
        "recipient": "Ada",
        "risk_level": "LOW",
        "reasons": [],
        "action": "released",
        "created_at": datetime.now(timezone.utc),
    }

    with Session(engine) as db:
        record_ledger_entry(db, entry)
        with pytest.raises(LedgerConflictError, match="different ledger details"):
            record_ledger_entry(
                db,
                {**entry, "id": "led_second", "recipient": "Different Recipient"},
            )
