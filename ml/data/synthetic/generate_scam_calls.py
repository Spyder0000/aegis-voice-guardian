"""Generate balanced, realistic scam/genuine transcripts for benchmarking."""

from __future__ import annotations

import random
from pathlib import Path

try:
    from .dataset_utils import make_case, validate_dataset, write_json
    from .generate_genuine_calls import GENUINE_CALLS
except ImportError:  # Supports ``python ml/data/synthetic/generate_scam_calls.py``.
    from dataset_utils import make_case, validate_dataset, write_json
    from generate_genuine_calls import GENUINE_CALLS


SCAM_CALLS = [
    make_case(
        "scam-customs-001",
        "authority_impersonation",
        "Send 150000 naira to this new account for the customs officer; he says my package is stuck and needs it now",
        is_scam=True,
        recipient_is_new=True,
        amount=150000,
        avg_transfer_amount=12000,
        hour_of_day=14,
        urgency_phrases=["needs it now", "customs officer"],
    ),
    make_case(
        "scam-bank-002",
        "bank_impersonation",
        "This is urgent, the bank caller says my account is frozen and I must send 80000 naira right away to unlock it",
        is_scam=True,
        recipient_is_new=True,
        amount=80000,
        avg_transfer_amount=15000,
        hour_of_day=23,
        urgency_phrases=["urgent", "right away", "account is frozen"],
    ),
    make_case(
        "scam-police-003",
        "authority_impersonation",
        "The police called and said I must pay a 45000 naira fine immediately or lose my licence",
        is_scam=True,
        recipient_is_new=True,
        amount=45000,
        avg_transfer_amount=10000,
        hour_of_day=2,
        urgency_phrases=["immediately", "police"],
    ),
    make_case(
        "scam-romance-004",
        "romance",
        "My online boyfriend needs 120000 naira immediately for a flight to finally visit me",
        is_scam=True,
        recipient_is_new=False,
        amount=120000,
        avg_transfer_amount=15000,
        hour_of_day=22,
        urgency_phrases=["immediately"],
    ),
    make_case(
        "scam-crypto-005",
        "investment",
        "Transfer 250000 naira now to this crypto broker; he guaranteed triple returns if I invest within ten minutes",
        is_scam=True,
        recipient_is_new=True,
        amount=250000,
        avg_transfer_amount=20000,
        hour_of_day=13,
        urgency_phrases=["now", "within ten minutes"],
    ),
    make_case(
        "scam-hospital-006",
        "family_emergency",
        "A caller says my brother was in an accident and needs 200000 naira for emergency surgery before they treat him",
        is_scam=True,
        recipient_is_new=True,
        amount=200000,
        avg_transfer_amount=25000,
        hour_of_day=3,
        urgency_phrases=["emergency", "before they treat him"],
    ),
    make_case(
        "scam-tax-007",
        "authority_impersonation",
        "The tax office official demands a 95000 naira overdue penalty or police will arrest me in one hour",
        is_scam=True,
        recipient_is_new=True,
        amount=95000,
        avg_transfer_amount=18000,
        hour_of_day=16,
        urgency_phrases=["in one hour", "police"],
    ),
    make_case(
        "scam-utility-008",
        "utility_impersonation",
        "The power agent says they will disconnect me in fifteen minutes unless I pay 35000 naira to his personal wallet",
        is_scam=True,
        recipient_is_new=True,
        amount=35000,
        avg_transfer_amount=8000,
        hour_of_day=21,
        urgency_phrases=["in fifteen minutes", "unless"],
    ),
    make_case(
        "scam-prize-009",
        "advance_fee",
        "They say I won one million naira and only need a 50000 naira processing fee to release the prize",
        is_scam=True,
        recipient_is_new=True,
        amount=50000,
        avg_transfer_amount=12000,
        hour_of_day=11,
    ),
    make_case(
        "scam-support-010",
        "tech_support",
        "The laptop technician says send 65000 naira right away for security software or my files will disappear",
        is_scam=True,
        recipient_is_new=True,
        amount=65000,
        avg_transfer_amount=10000,
        hour_of_day=20,
        urgency_phrases=["right away"],
    ),
    make_case(
        "scam-kidnap-011",
        "extortion",
        "The caller claims he kidnapped my cousin and demands 300000 naira before midnight",
        is_scam=True,
        recipient_is_new=True,
        amount=300000,
        avg_transfer_amount=15000,
        hour_of_day=0,
        urgency_phrases=["before midnight"],
    ),
    make_case(
        "scam-boss-012",
        "business_email_compromise",
        "My boss sent a voice note asking for an urgent 180000 naira payment to our usual supplier account",
        is_scam=True,
        recipient_is_new=False,
        amount=180000,
        avg_transfer_amount=30000,
        hour_of_day=17,
        urgency_phrases=["urgent"],
    ),
    make_case(
        "scam-rental-013",
        "rental",
        "The landlord says send a 100000 naira holding deposit right now or another tenant gets the flat",
        is_scam=True,
        recipient_is_new=True,
        amount=100000,
        avg_transfer_amount=25000,
        hour_of_day=19,
        urgency_phrases=["right now"],
    ),
    make_case(
        "scam-loan-014",
        "advance_fee",
        "The loan agent approved 500000 naira but wants a 40000 naira collateral fee before disbursement",
        is_scam=True,
        recipient_is_new=True,
        amount=40000,
        avg_transfer_amount=14000,
        hour_of_day=10,
    ),
    make_case(
        "scam-refund-015",
        "refund",
        "A shopping agent says they over-refunded me and I must return 85000 naira to a manager's account today",
        is_scam=True,
        recipient_is_new=True,
        amount=85000,
        avg_transfer_amount=12000,
        hour_of_day=15,
        urgency_phrases=["must", "today"],
    ),
    make_case(
        "scam-visa-016",
        "authority_impersonation",
        "An immigration officer says pay a 110000 naira visa correction fee now or face deportation",
        is_scam=True,
        recipient_is_new=True,
        amount=110000,
        avg_transfer_amount=20000,
        hour_of_day=8,
        urgency_phrases=["now", "deportation"],
    ),
    make_case(
        "scam-sim-017",
        "account_takeover",
        "Send just 9000 naira to Chinedu again; the caller says this small test will restore my blocked SIM",
        is_scam=True,
        recipient_is_new=False,
        amount=9000,
        avg_transfer_amount=15000,
        hour_of_day=12,
        urgency_phrases=["blocked SIM"],
    ),
    make_case(
        "scam-safe-account-018",
        "bank_impersonation",
        "Bank security says move 400000 naira from my account into my existing savings beneficiary before the hackers take it",
        is_scam=True,
        recipient_is_new=False,
        amount=400000,
        avg_transfer_amount=35000,
        hour_of_day=2,
        urgency_phrases=["before the hackers take it"],
    ),
    make_case(
        "scam-marketplace-019",
        "marketplace",
        "The seller will reserve the phone only if I transfer 25000 naira in the next five minutes outside the marketplace",
        is_scam=True,
        recipient_is_new=True,
        amount=25000,
        avg_transfer_amount=22000,
        hour_of_day=14,
        urgency_phrases=["next five minutes"],
    ),
    make_case(
        "scam-family-chat-020",
        "account_takeover",
        "My niece's usual chat account says she needs 15000 naira immediately for an emergency data bundle",
        is_scam=True,
        recipient_is_new=False,
        amount=15000,
        avg_transfer_amount=18000,
        hour_of_day=16,
        urgency_phrases=["immediately", "emergency"],
    ),
]


def generate(*, seed: int = 20260805) -> Path:
    combined_calls = [*SCAM_CALLS, *GENUINE_CALLS]
    validate_dataset(combined_calls)

    # A deterministic shuffle avoids label-order leakage while keeping diffs reproducible.
    random.Random(seed).shuffle(combined_calls)
    output_path = Path(__file__).with_name("labeled_calls.json")
    write_json(output_path, combined_calls)
    return output_path


if __name__ == "__main__":
    generated_path = generate()
    print(
        f"Wrote {len(SCAM_CALLS)} scam and {len(GENUINE_CALLS)} genuine calls "
        f"to {generated_path}"
    )
