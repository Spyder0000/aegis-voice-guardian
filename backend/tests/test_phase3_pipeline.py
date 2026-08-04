import os
import sys
from pathlib import Path
from dotenv import load_dotenv

root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir / "backend"))
load_dotenv(dotenv_path=root_dir / ".env")

from fastapi.testclient import TestClient
from app.main import app
from app.services.sahara_asr import extract_entities
from app.services.sahara_tts import build_clarifying_prompt
from app.agents.orchestrator import orchestrator

client = TestClient(app)

def test_entity_extraction():
    transcript = "Please send 50000 naira to Chukwuma now, it is an emergency!"
    extracted = extract_entities(transcript)
    assert extracted["amount"] == 50000.0
    assert extracted["recipient"] == "Chukwuma"
    assert "FLAG_EMERGENCY" in extracted["urgency_flags"]
    print("[+] Entity extraction test passed!")

def test_clarifying_prompt_length():
    prompt = build_clarifying_prompt("HIGH_URGENCY", recipient="Chukwuma", amount=50000)
    assert len(prompt) <= 100
    print(f"[+] Clarifying prompt test passed: '{prompt}' ({len(prompt)} chars)")

def test_orchestrator_pipeline():
    result = orchestrator.process_voice_transcript("Send 150000 naira to Unknown right now emergency")
    assert result["risk_evaluation"]["risk_level"] in ("MEDIUM", "HIGH")
    assert result["clarifying_question"] is not None
    assert len(result["clarifying_question"]) <= 100
    print("[+] Orchestrator pipeline test passed!")

def test_fastapi_intake_endpoint():
    response = client.post("/voice/intake", json={"transcript": "Send 2000 naira to Blessing"})
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 2000.0
    assert data["recipient"] == "Blessing"
    print("[+] FastAPI /voice/intake endpoint test passed!")

def test_fastapi_decision_endpoint():
    response = client.post("/transfers/decision", json={
        "amount": 2000.0,
        "recipient": "Blessing",
        "risk_level": "LOW"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "released"
    print("[+] FastAPI /transfers/decision endpoint test passed!")

if __name__ == "__main__":
    test_entity_extraction()
    test_clarifying_prompt_length()
    test_orchestrator_pipeline()
    test_fastapi_intake_endpoint()
    test_fastapi_decision_endpoint()
    print("\n[🎉] All Phase 3 pipeline tests PASSED successfully!")
