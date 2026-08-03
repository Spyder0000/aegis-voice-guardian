# AEGIS Voice Guardian

**Deep Learning Indaba 2026 — "Whose Intelligence?" Hackathon (ML Collective Africa × Intron Voice AI)**

Voice-driven anti-scam guardian for African digital banking. Sahara ASR/TTS listens for authorized-push-payment (APP) scam pressure in a live transfer request, scores it against a Trust Profile, and — if risky — soft-holds the transfer and runs a two-channel confirmation (spoken clarifying question **+** a tactile Visual Confirmation Card) before any money moves.

See `/docs/ARCHITECTURE.md` for the full system diagram and `/docs/ASSIGNMENTS.md` for who owns what and why.

---

## Repo Structure

```
aegis-voice-guardian/
├── backend/           # FastAPI orchestrator, agents, Sahara integration, Trust Ledger
│   └── app/
│       ├── routers/       # API endpoints (voice intake, transfer actions)
│       ├── agents/        # Orchestrator + Decision Agent (ask-clarify-decide loop)
│       ├── models/        # Trust Profile / Trust Ledger data models
│       ├── services/      # Sahara ASR/TTS clients, mock banking API
│       └── db/            # DB session + schema
├── frontend/          # Visual Confirmation Card + Trust Ledger dashboard
│   └── src/
│       ├── components/    # ConfirmationCard, TrustLedgerView
│       └── pages/          # Dashboard
├── ml/                # Trust Score model + benchmarking
│   ├── trust_score/       # XGBoost hybrid trust classifier
│   ├── benchmarks/        # ASR + intervention benchmark harness
│   ├── data/synthetic/    # Scripted scam/genuine call generators
│   └── notebooks/         # EDA
├── infra/             # docker-compose, env config
└── docs/              # Architecture, assignments, pitch doc
```

## Quick Start (once services are stubbed in)
```bash
cp infra/.env.example infra/.env
docker compose -f infra/docker-compose.yml up --build
```

## Team
| Role | Name | GitHub |
|---|---|---|
| Lead / Core Agent Loop | Agoro Oluwatimilehin | — |
| Trust Score & Benchmarking | Toluwalase Ajiboye | — |
| Frontend & Trust Ledger UI | David Akhabue | [@Eaglet001](https://github.com/orgs/Spyder0000/people/Eaglet001) |
| Infra & Synthetic Data | Okoh Darius | — |
