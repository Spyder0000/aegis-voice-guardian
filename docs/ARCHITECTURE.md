# AEGIS Voice Guardian — Architecture

```
Voice Input (customer transfer request, live call/app)
   │
   ▼
Sahara ASR v2 (streaming transcription)                    ← backend/app/services/sahara_asr.py
   │  extracts → amount | recipient | urgency/authority-impersonation phrases
   ▼
Intent & Entity Extraction Layer                            ← backend/app/agents/orchestrator.py
   │
   ▼
Agent Orchestrator — FastAPI + MCP-style loop                ← backend/app/agents/orchestrator.py
   │
   ▼
Trust Score Agent (rules + XGBoost hybrid)                   ← ml/trust_score/, backend/app/agents/decision_agent.py
   features: recipient novelty, amount deviation, time-of-day, urgency-language hits
   │
   ├── LOW RISK ─────────────────────────► Release transfer → log to Trust Ledger
   │
   └── MEDIUM / HIGH RISK
          │
          ▼
     Soft Hold via banking API (sandbox/mock)                ← backend/app/services/mock_banking_api.py
          │
          ├─► Sahara TTS → spoken clarifying question         ← backend/app/services/sahara_tts.py
          └─► Visual Confirmation Card → tactile/PIN confirm   ← frontend/src/components/ConfirmationCard.jsx
          │
          ▼
     User response → Decision Agent                          ← backend/app/agents/decision_agent.py
          │
          ▼
     Release / Escalate to human reviewer
          │
          ▼
     Trust Ledger — full rationale logged                     ← backend/app/models/trust_ledger.py, frontend/src/components/TrustLedgerView.jsx
```

## Module Ownership Map
| Module | Owner |
|---|---|
| `backend/app/agents/orchestrator.py`, `services/sahara_asr.py`, `services/sahara_tts.py`, `routers/voice.py` | Agoro |
| `ml/trust_score/`, `backend/app/agents/decision_agent.py`, `ml/benchmarks/` | Toluwalase |
| `frontend/src/components/`, `frontend/src/pages/` | David |
| `backend/app/services/mock_banking_api.py`, `backend/app/db/`, `ml/data/synthetic/`, `infra/` | Darius |

## Data Flow Contract & API Schemas

### 1. Real-time Audio Stream: `WS /voice/stream`
- **Direction:** Bidirectional WebSocket (Frontend <-> Backend)
- **Frontend -> Backend (Audio Chunks):**
  ```json
  {
    "event": "AUDIO_CHUNK",
    "audio_base64": "<base64_encoded_pcm16_chunk>"
  }
  ```
- **Backend -> Frontend (Transcript Events):**
  ```json
  {
    "event": "PARTIAL_TRANSCRIPT",
    "text": "Send 50000 naira to"
  }
  ```
  ```json
  {
    "event": "COMMITTED_TRANSCRIPT",
    "text": "Send 50000 naira to Chukwuma now, it is an emergency!",
    "session_id": "sttstream_12345"
  }
  ```

---

### 2. Voice Intake: `POST /voice/intake`
- **Request Body:**
  ```json
  {
    "transcript": "Send 50000 naira to Chukwuma now, it is an emergency!",
    "session_id": "sttstream_12345"
  }
  ```
- **Response Payload (200 OK):**
  ```json
  {
    "transcript": "Send 50000 naira to Chukwuma now, it is an emergency!",
    "amount": 50000.0,
    "currency": "NGN",
    "recipient": "Chukwuma",
    "urgency_flags": ["EMERGENCY_KEYWORD", "HIGH_PRESSURE_TIMING"]
  }
  ```

---

### 3. Trust Score Calculation: `POST /trust/score` (Toluwalase's Endpoint)
- **Request Body:** (Intake payload + User context)
  ```json
  {
    "user_id": "usr_99812",
    "amount": 50000.0,
    "recipient": "Chukwuma",
    "urgency_flags": ["EMERGENCY_KEYWORD", "HIGH_PRESSURE_TIMING"]
  }
  ```
- **Response Payload (200 OK):**
  ```json
  {
    "risk_level": "HIGH",
    "score": 0.87,
    "reasons": [
      "Recipient 'Chukwuma' is a newly added contact",
      "Amount 50000 NGN exceeds 3-month daily transfer average",
      "High urgency language detected"
    ]
  }
  ```

---

### 4. Transfer Decision & Execution: `POST /transfers/decision`
- **Request Body:**
  ```json
  {
    "user_id": "usr_99812",
    "amount": 50000.0,
    "recipient": "Chukwuma",
    "risk_level": "HIGH",
    "user_confirmation": {
      "verified_pin": true,
      "security_question_answer": "Maternal grandmother name verified"
    }
  }
  ```
- **Response Payload (200 OK):**
  ```json
  {
    "status": "released",  // Options: "released" | "held" | "escalated"
    "transfer_id": "tx_881923",
    "ledger_entry_id": "led_44129",
    "message": "Transfer verified and released to recipient."
  }
  ```

---

### End-to-End Workflow & Module Alignment
1. **Frontend (David)** connects to `WS /voice/stream` for live speech-to-text.
2. Once speech is committed, **Backend (Agoro)** parses entities via `POST /voice/intake`.
3. **ML Agent (Toluwalase)** scores the transaction via `POST /trust/score`.
4. If `risk_level != LOW`: Frontend displays **Confirmation Card** and plays spoken questions via **Sahara TTS** (`/services/sahara_tts.py`).
5. Final confirmation invokes `POST /transfers/decision` which records the audit trail in **Trust Ledger (Darius)**.

