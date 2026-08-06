"""Shared isolation for backend tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Endpoint tests intentionally exercise the documented in-memory fallback.
os.environ["DATABASE_URL"] = ""


@pytest.fixture(autouse=True)
def reset_demo_state():
    from app.routers.transfers import reset_memory_ledger
    from app.services.mock_banking_api import reset_mock_bank

    reset_mock_bank()
    reset_memory_ledger()
    yield
    reset_mock_bank()
    reset_memory_ledger()
