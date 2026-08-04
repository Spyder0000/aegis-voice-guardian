"""
Generates scripted scam-call and genuine-call transcripts for testing/benchmarking.
Owner: Okoh Darius

Output feeds directly into Toluwalase's benchmark harness
(ml/benchmarks/run_asr_benchmark.py and run_intervention_benchmark expects a labeled_calls.json file
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
    {
        "transcript": "My online boyfriend needs 120000 immediately for a flight ticket to come see me, please send it to this account",
        "features": {
            "recipient_is_new": True,
            "amount": 120000,
            "avg_transfer_amount": 15000,
            "hour_of_day": 22,
        },
        "is_scam": True,
    },
    {
        "transcript": "Transfer 250000 right now to this crypto broker, he guaranteed triple returns if I invest within 10 minutes",
        "features": {
            "recipient_is_new": True,
            "amount": 250000,
            "avg_transfer_amount": 20000,
            "hour_of_day": 1,
        },
        "is_scam": True,
    },
    {
        "transcript": "The hospital called, my brother was in an accident and needs 200000 for emergency surgery immediately",
        "features": {
            "recipient_is_new": True,
            "amount": 200000,
            "avg_transfer_amount": 25000,
            "hour_of_day": 3,
        },
        "is_scam": True,
    },
    {
        "transcript": "Tax office official on line 2 demands 95000 overdue penalty or police will arrest me in one hour",
        "features": {
            "recipient_is_new": True,
            "amount": 95000,
            "avg_transfer_amount": 18000,
            "hour_of_day": 16,
        },
        "is_scam": True,
    },
    {
        "transcript": "Power company agent says power will be cut in 15 minutes unless I pay 35000 directly to his personal wallet",
        "features": {
            "recipient_is_new": True,
            "amount": 35000,
            "avg_transfer_amount": 8000,
            "hour_of_day": 21,
        },
        "is_scam": True,
    },
    {
        "transcript": "I won 1 million naira lottery, just need to send 50000 processing fee to release the grand prize",
        "features": {
            "recipient_is_new": True,
            "amount": 50000,
            "avg_transfer_amount": 12000,
            "hour_of_day": 11,
        },
        "is_scam": True,
    },
    {
        "transcript": "Microsoft technician detected virus on my laptop, send 65000 right away for security cleanup software",
        "features": {
            "recipient_is_new": True,
            "amount": 65000,
            "avg_transfer_amount": 10000,
            "hour_of_day": 20,
        },
        "is_scam": True,
    },
    {
        "transcript": "Callers claim they kidnapped my cousin, demand 300000 wire transfer before midnight or they hurt him",
        "features": {
            "recipient_is_new": True,
            "amount": 300000,
            "avg_transfer_amount": 15000,
            "hour_of_day": 0,
        },
        "is_scam": True,
    },
    {
        "transcript": "My boss emailed asking me to send 180000 urgent payment to a new vendor account immediately",
        "features": {
            "recipient_is_new": True,
            "amount": 180000,
            "avg_transfer_amount": 30000,
            "hour_of_day": 17,
        },
        "is_scam": True,
    },
    {
        "transcript": "Landlord says someone else wants the apartment, send 100000 holding deposit right now or I lose the flat",
        "features": {
            "recipient_is_new": True,
            "amount": 100000,
            "avg_transfer_amount": 25000,
            "hour_of_day": 19,
        },
        "is_scam": True,
    },
    {
        "transcript": "Quick loan agent approved 500k loan, pay 40000 collateral security fee first to get disbursement",
        "features": {
            "recipient_is_new": True,
            "amount": 40000,
            "avg_transfer_amount": 14000,
            "hour_of_day": 10,
        },
        "is_scam": True,
    },
    {
        "transcript": "Shopping site over-refunded me by mistake, send back 85000 to this personal account now before legal action",
        "features": {
            "recipient_is_new": True,
            "amount": 85000,
            "avg_transfer_amount": 12000,
            "hour_of_day": 15,
        },
        "is_scam": True,
    },
    {
        "transcript": "Immigration officer says my visa extension has issue, send 110000 fee right away or deportation order issued",
        "features": {
            "recipient_is_new": True,
            "amount": 110000,
            "avg_transfer_amount": 20000,
            "hour_of_day": 8,
        },
        "is_scam": True,
    },
    {
        "transcript": "Car crash caller claims I hit his vehicle, demands 75000 settlement transfer on the spot or calling police",
        "features": {
            "recipient_is_new": True,
            "amount": 75000,
            "avg_transfer_amount": 15000,
            "hour_of_day": 22,
        },
        "is_scam": True,
    },
    {
        "transcript": "Bank security helpline says my main account is compromised, move 400000 to safe holding account immediately",
        "features": {
            "recipient_is_new": True,
            "amount": 400000,
            "avg_transfer_amount": 35000,
            "hour_of_day": 2,
        },
        "is_scam": True,
    },
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
    {
        "transcript": "Transfer 12000 to mama for weekend groceries",
        "features": {
            "recipient_is_new": False,
            "amount": 12000,
            "avg_transfer_amount": 10000,
            "hour_of_day": 10,
        },
        "is_scam": False,
    },
    {
        "transcript": "Pay 8500 electricity utility bill for this month",
        "features": {
            "recipient_is_new": False,
            "amount": 8500,
            "avg_transfer_amount": 8500,
            "hour_of_day": 14,
        },
        "is_scam": False,
    },
    {
        "transcript": "Send 15000 to fiber internet service provider for monthly renewal",
        "features": {
            "recipient_is_new": False,
            "amount": 15000,
            "avg_transfer_amount": 15000,
            "hour_of_day": 11,
        },
        "is_scam": False,
    },
    {
        "transcript": "Pay 60000 for junior school fees second term installment",
        "features": {
            "recipient_is_new": False,
            "amount": 60000,
            "avg_transfer_amount": 55000,
            "hour_of_day": 12,
        },
        "is_scam": False,
    },
    {
        "transcript": "Send 25000 allowance to my mom as usual",
        "features": {
            "recipient_is_new": False,
            "amount": 25000,
            "avg_transfer_amount": 25000,
            "hour_of_day": 16,
        },
        "is_scam": False,
    },
    {
        "transcript": "Pay 18000 mechanic for replacing brake pads on the car",
        "features": {
            "recipient_is_new": False,
            "amount": 18000,
            "avg_transfer_amount": 15000,
            "hour_of_day": 17,
        },
        "is_scam": False,
    },
    {
        "transcript": "Transfer 10000 for monthly gym membership access",
        "features": {
            "recipient_is_new": False,
            "amount": 10000,
            "avg_transfer_amount": 10000,
            "hour_of_day": 7,
        },
        "is_scam": False,
    },
    {
        "transcript": "Send 3500 to Tobi to split team lunch bill from earlier",
        "features": {
            "recipient_is_new": False,
            "amount": 3500,
            "avg_transfer_amount": 5000,
            "hour_of_day": 13,
        },
        "is_scam": False,
    },
    {
        "transcript": "Pay 5000 to Chika for dinner split last night",
        "features": {
            "recipient_is_new": False,
            "amount": 5000,
            "avg_transfer_amount": 6000,
            "hour_of_day": 19,
        },
        "is_scam": False,
    },
    {
        "transcript": "Send 7500 to salon stylist for hair appointment",
        "features": {
            "recipient_is_new": False,
            "amount": 7500,
            "avg_transfer_amount": 8000,
            "hour_of_day": 15,
        },
        "is_scam": False,
    },
    {
        "transcript": "Pay 35000 to freelance designer for completed logo project",
        "features": {
            "recipient_is_new": False,
            "amount": 35000,
            "avg_transfer_amount": 30000,
            "hour_of_day": 18,
        },
        "is_scam": False,
    },
    {
        "transcript": "Send 4200 to pharmacy for prescription refill",
        "features": {
            "recipient_is_new": False,
            "amount": 4200,
            "avg_transfer_amount": 5000,
            "hour_of_day": 10,
        },
        "is_scam": False,
    },
    {
        "transcript": "Transfer 50000 into my high yield savings sub account",
        "features": {
            "recipient_is_new": False,
            "amount": 50000,
            "avg_transfer_amount": 40000,
            "hour_of_day": 9,
        },
        "is_scam": False,
    },
    {
        "transcript": "Send 12000 deposit to tailor for native wear sewing",
        "features": {
            "recipient_is_new": False,
            "amount": 12000,
            "avg_transfer_amount": 10000,
            "hour_of_day": 11,
        },
        "is_scam": False,
    },
    {
        "transcript": "Pay 15000 fuel attendant for full tank filling",
        "features": {
            "recipient_is_new": False,
            "amount": 15000,
            "avg_transfer_amount": 12000,
            "hour_of_day": 8,
        },
        "is_scam": False,
    },
    {
        "transcript": "Send 10000 monthly tithe contribution to church account",
        "features": {
            "recipient_is_new": False,
            "amount": 10000,
            "avg_transfer_amount": 10000,
            "hour_of_day": 10,
        },
        "is_scam": False,
    },
]


def generate():
    all_calls = SCAM_CALLS + GENUINE_CALLS
    out_dir = Path(__file__).parent
    out_path = out_dir / "labeled_calls.json"
    out_path.write_text(json.dumps(all_calls, indent=2))
    print(f"Wrote {len(all_calls)} labeled calls to {out_path}")


if __name__ == "__main__":
    generate()
