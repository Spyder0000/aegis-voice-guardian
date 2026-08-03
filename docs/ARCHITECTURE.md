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

## Data Flow Contract (agree on this before writing code)
1. `POST /voice/intake` (Agoro) → returns `{transcript, amount, recipient, urgency_flags}`
2. `POST /trust/score` (Toluwalase) → takes intake payload, returns `{risk_level, score, reasons}`
3. If `risk_level != LOW`: frontend renders `ConfirmationCard` (David) using the intake payload
4. `POST /transfers/decision` (Agoro + Toluwalase) → takes user confirmation, returns final status
5. Every step writes to Trust Ledger (Darius's schema, David's view, Agoro's write calls)

Lock this contract on day 1 so all four people can build in parallel against a shared interface instead of waiting on each other.
