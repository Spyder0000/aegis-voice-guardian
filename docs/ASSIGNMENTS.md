# Task Assignments — AEGIS Voice Guardian (72-Hour Build)

**Assignment logic:** the critical path (Sahara integration + the agent loop that everything else depends on) goes to the most active person, since it's the highest-risk, highest-blocking piece. Work that has the fewest downstream dependents — and can be picked up by someone else if it stalls — goes to the least active person, so the team isn't exposed if that work slips.

---

## 1. Agoro Oluwatimilehin — Lead / Core Agent Loop
**Why this task:** most active, group lead. This is the hardest and most important piece — if it's late or broken, nothing else has anything to plug into. It also requires the most cross-cutting decisions (API contracts, Sahara auth/quota handling), which the lead is best placed to make unilaterally without waiting on consensus.

- [ ] Sahara ASR v2 integration (`backend/app/services/sahara_asr.py`) — streaming transcription, entity extraction (amount, recipient, urgency phrases)
- [ ] Sahara TTS integration (`backend/app/services/sahara_tts.py`) — spoken clarifying question generation
- [ ] Agent Orchestrator (`backend/app/agents/orchestrator.py`) — the MCP-style ask-clarify-decide loop
- [ ] `POST /voice/intake` endpoint (`backend/app/routers/voice.py`)
- [ ] Own the API contract in `docs/ARCHITECTURE.md` — publish it by end of Hour 6 so the rest of the team can build against it
- [ ] Final integration pass on Day 3 (stitch all four modules together for the demo)

---

## 2. Toluwalase Ajiboye — Trust Score & Benchmarking
**Why this task:** 2nd most active, and this is the second-most load-bearing piece — the trust model and the benchmark numbers are what actually win the "measurable performance" scoring criteria.

- [ ] Trust Score model (`ml/trust_score/train_xgboost.py`, `features.py`) — recipient novelty, amount deviation, time-of-day, urgency-language features
- [ ] Decision Agent logic (`backend/app/agents/decision_agent.py`) — risk-level → hold/release routing
- [ ] `POST /trust/score` endpoint
- [ ] Benchmark harness (`ml/benchmarks/run_asr_benchmark.py`) — WER, entity-F1, FP/FN rate, latency, vs. Whisper + one more ASR model
- [ ] Own the final "Benchmark Potential" numbers for the pitch deck

---

## 3. David Akhabue ([@Eaglet001](https://github.com/orgs/Spyder0000/people/Eaglet001)) — Frontend & Trust Ledger UI
**Why this task:** 3rd most active — this work depends on Agoro's and Toluwalase's API contracts being published first, so it naturally starts a few hours later, matching a slightly lower activity budget. It's also the most demo-visible piece, which matters for judging.

- [ ] Visual Confirmation Card (`frontend/src/components/ConfirmationCard.jsx`) — amount + recipient re-display, tactile/PIN confirm
- [ ] Trust Ledger view (`frontend/src/components/TrustLedgerView.jsx`) — explainable log of every hold/decision
- [ ] Dashboard page wiring (`frontend/src/pages/Dashboard.jsx`)
- [ ] Consume `/voice/intake`, `/trust/score`, `/transfers/decision` endpoints once published (Hour 6+)

---

## 4. Okoh Darius — Infra, Mock Banking API & Synthetic Data
**Why this task:** least active so far. These tasks are deliberately **low-dependency and non-blocking** — they don't sit on the critical path, can be done independently of everyone else's schedule, and if they slip, any other team member can pick them up in an hour or two without derailing the demo. This also means if Darius does show up and moves fast, there's room to pull him into supporting Toluwalase on benchmarking data generation.

- [ ] Mock banking API (`backend/app/services/mock_banking_api.py`) — soft hold / release / escalate stub endpoints
- [ ] Postgres schema (`backend/app/db/schema.sql`) — Trust Profile + Trust Ledger tables
- [ ] Synthetic scam/genuine call scripts + audio generation (`ml/data/synthetic/generate_scam_calls.py`, `generate_genuine_calls.py`) — feeds directly into Toluwalase's benchmark harness
- [ ] `infra/docker-compose.yml` + `.env.example` — one-command local spin-up for the whole team
- [ ] **Fallback plan:** if Darius is unavailable, Agoro reassigns the banking API stub (small, ~2hr task) and Toluwalase absorbs the synthetic data generation, since she needs that data anyway for benchmarking.

---

## Suggested Timeline (72 Hours)

| Hours | Agoro | Toluwalase | David | Darius |
|---|---|---|---|---|
| 0–6 | Sahara ASR setup + API contract draft | Trust feature design | Repo/UI scaffolding, wireframe | DB schema + docker-compose |
| 6–24 | Orchestrator + intake endpoint | XGBoost model v1 | Confirmation Card (against mocked API) | Mock banking API + synthetic scam scripts |
| 24–40 | Sahara TTS + ask-clarify loop | Decision Agent + `/trust/score` | Trust Ledger view | Synthetic audio generation for benchmark set |
| 40–56 | Wire orchestrator ↔ decision agent ↔ mock bank | Run first benchmark pass | Wire Dashboard end-to-end | Support wherever blocked |
| 56–68 | Full integration + bug fixes | Finalize benchmark numbers | Polish UI for demo | Support wherever blocked |
| 68–72 | Demo dry run, pitch deck | Demo dry run, benchmark slide | Demo dry run | Demo dry run |

**Standing rule:** anyone blocked for more than 30 minutes posts in the team channel immediately — don't wait for standup. With one contributor at lower activity, the team can't afford silent blockers.
