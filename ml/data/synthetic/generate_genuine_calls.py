"""Generate genuine-transfer counterexamples for false-positive testing."""

from __future__ import annotations

from pathlib import Path

try:
    from .dataset_utils import make_case, write_json
except ImportError:  # Supports direct execution from the repository root.
    from dataset_utils import make_case, write_json


GENUINE_CALLS = [
    make_case(
        "genuine-family-001",
        "family",
        "Send 20000 naira to my sister Ada for her birthday gift",
        is_scam=False,
        recipient_is_new=False,
        amount=20000,
        avg_transfer_amount=18000,
        hour_of_day=15,
    ),
    make_case(
        "genuine-housing-002",
        "housing",
        "Pay my usual rent transfer of 45000 naira to Mr Bello",
        is_scam=False,
        recipient_is_new=False,
        amount=45000,
        avg_transfer_amount=45000,
        hour_of_day=9,
    ),
    make_case(
        "genuine-family-003",
        "family",
        "Abeg send 12000 to Mama for weekend market groceries",
        is_scam=False,
        recipient_is_new=False,
        amount=12000,
        avg_transfer_amount=10000,
        hour_of_day=10,
        language="Nigerian Pidgin + English",
    ),
    make_case(
        "genuine-utility-004",
        "utilities",
        "Pay 8500 naira to EKEDC for this month's electricity token",
        is_scam=False,
        recipient_is_new=False,
        amount=8500,
        avg_transfer_amount=8500,
        hour_of_day=14,
    ),
    make_case(
        "genuine-utility-005",
        "utilities",
        "Renew my monthly fibre internet with 15000 naira to the saved provider",
        is_scam=False,
        recipient_is_new=False,
        amount=15000,
        avg_transfer_amount=15000,
        hour_of_day=11,
    ),
    make_case(
        "genuine-school-006",
        "education",
        "Send 60000 naira to Greenfield School for the second-term instalment",
        is_scam=False,
        recipient_is_new=False,
        amount=60000,
        avg_transfer_amount=55000,
        hour_of_day=12,
    ),
    make_case(
        "genuine-health-007",
        "health",
        "The clinic needs a 70000 naira deposit before my scheduled surgery tomorrow",
        is_scam=False,
        recipient_is_new=True,
        amount=70000,
        avg_transfer_amount=30000,
        hour_of_day=20,
        urgency_phrases=["before tomorrow"],
    ),
    make_case(
        "genuine-transport-008",
        "transport",
        "Pay 18000 naira to the new mechanic who replaced my brake pads today",
        is_scam=False,
        recipient_is_new=True,
        amount=18000,
        avg_transfer_amount=15000,
        hour_of_day=17,
    ),
    make_case(
        "genuine-subscription-009",
        "subscription",
        "Transfer 10000 naira for my regular gym membership",
        is_scam=False,
        recipient_is_new=False,
        amount=10000,
        avg_transfer_amount=10000,
        hour_of_day=7,
    ),
    make_case(
        "genuine-social-010",
        "shared_expense",
        "Send 3500 naira to Tobi for my share of the team lunch",
        is_scam=False,
        recipient_is_new=False,
        amount=3500,
        avg_transfer_amount=5000,
        hour_of_day=13,
    ),
    make_case(
        "genuine-social-011",
        "shared_expense",
        "I just met Chika at dinner, send her 5000 naira for my half of the bill",
        is_scam=False,
        recipient_is_new=True,
        amount=5000,
        avg_transfer_amount=6000,
        hour_of_day=22,
    ),
    make_case(
        "genuine-personal-012",
        "personal_care",
        "Pay 7500 naira to my saved salon stylist for tomorrow's appointment",
        is_scam=False,
        recipient_is_new=False,
        amount=7500,
        avg_transfer_amount=8000,
        hour_of_day=15,
    ),
    make_case(
        "genuine-business-013",
        "small_business",
        "Pay 35000 naira to our freelance designer for the completed logo",
        is_scam=False,
        recipient_is_new=False,
        amount=35000,
        avg_transfer_amount=30000,
        hour_of_day=18,
    ),
    make_case(
        "genuine-health-014",
        "health",
        "Please send 4200 naira to the pharmacy for my prescription refill",
        is_scam=False,
        recipient_is_new=False,
        amount=4200,
        avg_transfer_amount=5000,
        hour_of_day=10,
    ),
    make_case(
        "genuine-savings-015",
        "savings",
        "Move 250000 naira into my verified high-yield savings account",
        is_scam=False,
        recipient_is_new=False,
        amount=250000,
        avg_transfer_amount=40000,
        hour_of_day=9,
    ),
    make_case(
        "genuine-clothing-016",
        "small_business",
        "Send a 12000 naira deposit to the new tailor for my native wear",
        is_scam=False,
        recipient_is_new=True,
        amount=12000,
        avg_transfer_amount=10000,
        hour_of_day=11,
    ),
    make_case(
        "genuine-transport-017",
        "transport",
        "Pay 15000 naira to the fuel station for filling the delivery van",
        is_scam=False,
        recipient_is_new=False,
        amount=15000,
        avg_transfer_amount=12000,
        hour_of_day=8,
    ),
    make_case(
        "genuine-community-018",
        "community",
        "Send my regular 10000 naira monthly contribution to the church account",
        is_scam=False,
        recipient_is_new=False,
        amount=10000,
        avg_transfer_amount=10000,
        hour_of_day=10,
    ),
    make_case(
        "genuine-business-019",
        "small_business",
        "Our freezer failed; urgently pay 180000 naira to the supplier before the morning delivery",
        is_scam=False,
        recipient_is_new=True,
        amount=180000,
        avg_transfer_amount=45000,
        hour_of_day=1,
        urgency_phrases=["urgently", "before the morning delivery"],
    ),
    make_case(
        "genuine-family-020",
        "family",
        "Send 30000 naira now to my son Kunle; he is stranded at the bus terminal",
        is_scam=False,
        recipient_is_new=False,
        amount=30000,
        avg_transfer_amount=22000,
        hour_of_day=23,
        urgency_phrases=["now", "stranded"],
    ),
]


def generate() -> Path:
    # The class-only generator validates structure; combined generation applies
    # the stronger cross-class shortcut checks.
    if len(GENUINE_CALLS) < 15:
        raise ValueError("At least 15 genuine calls are required.")
    output_path = Path(__file__).with_name("genuine_calls.json")
    write_json(output_path, GENUINE_CALLS)
    return output_path


if __name__ == "__main__":
    generated_path = generate()
    print(f"Wrote {len(GENUINE_CALLS)} genuine calls to {generated_path}")
