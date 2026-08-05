# Darius's Task Sheet — AEGIS Voice Guardian
**Role:** Infra, Mock Banking API & Synthetic Data
**Owns:** Mock banking API, DB schema, synthetic scam/genuine call data, docker-compose

**Note:** none of your tasks block anyone else — build in whatever order makes sense, but the synthetic call data (Phase 3) is the highest-value thing you can hand off, since Toluwalase can't test or tune her risk scorer without it.

> **Implementation update (2026-08-05):** The code tasks below are complete and
> covered by automated tests. PostgreSQL schema + seed execution was verified
> against a temporary local database (1 profile, 2 ledger rows). The generated
> benchmark contains 20 scam and 20 genuine calls, including new/known-recipient
> counterexamples for both labels. Docker configuration is structurally validated;
> the final `docker compose up` smoke test still requires Docker Desktop WSL
> integration on this workstation. The dataset is ready for Toluwalase, but the
> external handoff remains a team communication step.

> The code blocks below are the original hackathon baseline. The linked source
> files are now authoritative and include validation, persistence, idempotency,
> health checks, and automated tests beyond those starter snippets.

---

## Phase 1 — Mock Banking API

`backend/app/services/mock_banking_api.py` — a fake bank that just needs to hold, release, or escalate a transfer. No real money, no real bank integration:

```python
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
```

- [x] File created, functions tested with a quick manual script (create a transfer, hold it, release it, check status)
- [x] Calls aligned with the published orchestrator contract: LOW releases; MEDIUM/HIGH soft-hold; verified confirmation releases; unverified HIGH escalates

---

## Phase 2 — Database Schema

`backend/app/db/schema.sql` — two tables: one tracking each customer's normal transfer history, one logging every decision:

```sql
-- AEGIS Voice Guardian schema
-- Owner: Okoh Darius

CREATE TABLE IF NOT EXISTS trust_profile (
    user_id UUID PRIMARY KEY,
    known_recipients JSONB DEFAULT '[]',
    avg_transfer_amount NUMERIC,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS trust_ledger (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES trust_profile(user_id),
    transcript TEXT,
    amount NUMERIC,
    recipient TEXT,
    risk_level TEXT,
    reasons JSONB,
    action TEXT, -- released | held | escalated
    created_at TIMESTAMP DEFAULT now()
);
```

- [x] Schema created with constraints, indexes, profile statistics, and explainable ledger fields
- [x] Load fake data and verify it with `psql` (`backend/app/db/seed.sql`)
- [x] Add SQLAlchemy sessions, models, repository operations, durable ledger writes, and in-memory fallback when `DATABASE_URL` is intentionally absent

```python
# backend/app/db/session.py
"""
DB session setup.
Owner: Okoh Darius
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://aegis:aegis@localhost:5432/aegis")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## Phase 3 — Synthetic Call Data (your highest-value task)

Toluwalase cannot test or tune her risk scorer without this. Write 15-20 scam scripts and 15-20 genuine scripts. Structure them so they can feed directly into her benchmark harness.

`ml/data/synthetic/generate_scam_calls.py`:

```python
"""
Generates scripted scam-call transcripts for testing/benchmarking.
Owner: Okoh Darius

Output feeds directly into Toluwalase's benchmark harness
(ml/benchmarks/run_asr_benchmark.py expects a labeled_calls.json file
shaped like the SCAM_CALLS + GENUINE_CALLS lists below, merged and labeled).
"""
import json
from pathlib import Path

SCAM_CALLS = [
    {
        "transcript": "Send 150000 to this new account for the customs officer, he says my package is stuck and needs it now",
        "features": {
            "recipient_is_new": True,
            "amount": 150000,
            "avg_transfer_amount": 12000,
            "hour_of_day": 14,
        },
        "is_scam": True,
    },
    {
        "transcript": "This is urgent, my account is frozen, I need to send 80000 right away to unlock it",
        "features": {
            "recipient_is_new": True,
            "amount": 80000,
            "avg_transfer_amount": 15000,
            "hour_of_day": 23,
        },
        "is_scam": True,
    },
    {
        "transcript": "The police called and said I need to pay a fine immediately or I will lose my license, send 45000 now",
        "features": {
            "recipient_is_new": True,
            "amount": 45000,
            "avg_transfer_amount": 10000,
            "hour_of_day": 2,
        },
        "is_scam": True,
    },
    # TODO Darius: add 12-17 more, covering:
    # - romance scam pressure ("he needs money for a flight to see me")
    # - fake investment/crypto opportunity with urgency
    # - fake "your relative is in the hospital" emergency scam
    # - fake tax/utility bill threat scam
    # Vary the phrasing, amounts, and times of day so the test set is realistic.
]

GENUINE_CALLS = [
    {
        "transcript": "Send 20000 to my sister for her birthday",
        "features": {
            "recipient_is_new": False,
            "amount": 20000,
            "avg_transfer_amount": 18000,
            "hour_of_day": 15,
        },
        "is_scam": False,
    },
    {
        "transcript": "Pay my usual rent transfer of 45000 to my landlord",
        "features": {
            "recipient_is_new": False,
            "amount": 45000,
            "avg_transfer_amount": 45000,
            "hour_of_day": 9,
        },
        "is_scam": False,
    },
    # TODO Darius: add 13-18 more everyday transfers — bills, family,
    # small business payments, recurring transfers — to check the
    # scorer doesn't over-flag normal activity.
]


def generate():
    all_calls = SCAM_CALLS + GENUINE_CALLS
    out_path = Path("ml/data/synthetic/labeled_calls.json")
    out_path.write_text(json.dumps(all_calls, indent=2))
    print(f"Wrote {len(all_calls)} labeled calls to {out_path}")


if __name__ == "__main__":
    generate()
```

- [x] Fill in the dataset — 20 scam scripts and 20 genuine scripts total
- [x] Vary language, amounts, time-of-day, urgency, category, and recipient familiarity; validate against shortcut-prone label splits
- [x] Run `python generate_scam_calls.py`, confirm `labeled_calls.json` is created reproducibly
- [ ] Hand this file to Toluwalase — this directly feeds her benchmark harness

**Optional stretch (only if time allows):** generate actual audio files (text-to-speech) from these scripts so Agoro can test real Sahara ASR transcription accuracy against known ground-truth text, not just test the risk scorer on plain text.

---

## Phase 4 — One-Command Local Setup

`infra/docker-compose.yml`:

```yaml
version: "3.9"
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: aegis
      POSTGRES_PASSWORD: aegis
      POSTGRES_DB: aegis
    ports:
      - "5432:5432"
  backend:
    build: ../backend
    env_file: .env
    ports:
      - "8000:8000"
    depends_on:
      - db
```

`infra/.env.example`:

```
SAHARA_API_KEY=
DATABASE_URL=postgresql://aegis:aegis@localhost:5432/aegis
BANKING_API_MODE=mock
```

- [ ] `docker compose up` successfully starts Postgres + backend (blocked locally until Docker Desktop enables WSL integration)
- [x] Team can copy `.env.example` to `.env`, optionally add `SAHARA_API_KEY`, and run `docker compose --env-file infra/.env -f infra/docker-compose.yml up --build`; transcript-only flows need no paid API key

---

## If You're Short on Time

Priority order: **Phase 3 (synthetic data) first** — nobody else can easily do this, and Toluwalase is blocked without it. Phases 1, 2, and 4 are all small enough that Agoro or Toluwalase can absorb them in an hour or two if you run out of time.

---

## You're Done With Your Part When:
- Toluwalase has a `labeled_calls.json` file with 30+ realistic scam/genuine examples
- `mock_banking_api.py` can hold, release, and escalate a fake transfer
- The database schema is created and can store a test row
- `docker compose up` works for a teammate who's never set up the project before
