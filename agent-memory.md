# AEGIS Voice Guardian — Project Memory / Handoff Doc
**Purpose:** full context dump so a new chat/agent session can pick up exactly where this one left off, with zero lost context. Read this top to bottom before doing anything else.

**Deadline:** Aug 6, 2026, 1:00pm WAT submission. Building since Aug 3.

---

## 1. The Project

**AEGIS Voice Guardian** — voice-driven anti-scam system for African digital banking, built for the "Whose Intelligence?" hackathon (ML Collective Africa × Intron Voice AI, Deep Learning Indaba 2026).

**Core concept:** treats voice as a *behavioral trust signal*, not just a command. A customer's voice transfer request is transcribed by Sahara ASR, checked against a Trust Score, and if risky, the system soft-holds the transfer and runs a two-channel intervention — a spoken clarifying question (Sahara TTS) **and** a Visual Confirmation Card requiring tactile PIN confirmation before any money moves. Voice is never the sole authenticator or sole release mechanism.

**Category:** Fintech, Telco & Customer Experience.

---

## 2. Team & Roles
| Name | Role | Owns |
|---|---|---|
| **Agoro Oluwatimilehin (me/you, the lead)** | Core Agent Loop | Sahara ASR/TTS integration, orchestrator, `/voice/intake`, overall integration |
| **Toluwalase Ajiboye** | Trust Score & Benchmarking | Rule-based scorer, decision agent, benchmark harness |
| **David Akhabue** ([@Eaglet001](https://github.com/orgs/Spyder0000/people/Eaglet001)) | Frontend | Confirmation Card, Trust Ledger UI, Dashboard |
| **Okoh Darius** | Infra & Data | Mock banking API, DB schema, synthetic call data |

---

## 3. Repo Structure (already scaffolded)
```
aegis-voice-guardian/
├── backend/app/
│   ├── routers/ (voice.py, transfers.py)
│   ├── agents/ (orchestrator.py, decision_agent.py — this one now re-exports from ml.trust_score)
│   ├── services/ (sahara_asr.py, sahara_tts.py, mock_banking_api.py)
│   ├── db/ (schema.sql, session.py)
│   └── main.py
├── frontend/src/
│   ├── components/ (ConfirmationCard.jsx, TrustLedgerView.jsx)
│   └── pages/ (Dashboard.jsx)
├── ml/
│   ├── trust_score/ (rule_based.py, decision_agent.py, contract_adapter.py, urgency_phrases.txt, __init__.py)
│   ├── benchmarks/ (run_asr_benchmark.py = intervention benchmark; run_asr_comparison.py = real ASR benchmark; diagnose_false_positives.py)
│   ├── data/synthetic/ (labeled_calls.json — 40 calls, generate_scam_calls.py, generate_genuine_calls.py, load_afriswitch.py)
│   └── notebooks/ (whisper_asr_benchmark.ipynb — to be added after Colab work)
├── infra/ (docker-compose.yml, .env.example)
└── docs/
    ├── ARCHITECTURE.md
    ├── TRUST_SCORE_CONTRACT.md
    ├── SOLUTION_DESCRIPTION.md
    ├── BENCHMARK_REPORT.md
    ├── ETHICS_INCLUSION_NOTE.md
    └── SUBMISSION_SELF_AUDIT.md
```

---

## 4. Key Decisions Made (don't relitigate these)
- **Trust Score is rule-based, NOT XGBoost.** Deliberate scoping choice — not enough data/time to train+validate a model. XGBoost is a bonus-only item if time allows after the baseline works end-to-end. This is framed as a *strength* (transparent, explainable) in `SOLUTION_DESCRIPTION.md`, not a weakness.
- **Dropped Adaption Labs / Adaptive Data / AutoScientist entirely.** Evaluated — doesn't accept audio input, only does Translate/Localize (not freeform generation), and has real job-queue time risk (can take hours). Not worth it this close to deadline.
- **Third ASR benchmark model is Meta MMS** (`facebook/mms-1b-all`), alongside Sahara v2 and Whisper. Important: **Grok/Llama3-style text LLMs are NOT valid benchmark candidates** — they don't do speech-to-text, and the challenge explicitly requires 3+ models that transcribe audio.
- **Whisper runs via Google Colab (free GPU), not OpenAI's paid API.** No budget for the $5 minimum OpenAI billing. Also ruled out local Whisper on the dev machine (8GB RAM, no GPU, old CPU) in favor of Colab to avoid crashing/slowing the laptop. `transcribe_whisper()` in `run_asr_comparison.py` now reads a **pre-computed transcript file** (`whisper_transcripts.json`, generated in Colab and downloaded) rather than calling Whisper live from the script.
- **Two separate benchmarks exist, not one:**
  - `run_asr_benchmark.py` = **intervention benchmark** (does the risk scorer correctly flag scam vs. genuine, given already-written text transcripts) — this was built first but is NOT what the challenge requires on its own.
  - `run_asr_comparison.py` = **the actual required ASR benchmark** (Sahara vs. Whisper vs. MMS transcription accuracy on real audio, WER-based) — this is the one that was "shallow"/missing and is still being built out.
- **Real code-switched audio comes from Intron's own Afriswitch HuggingFace collection** (`huggingface.co/collections/intronhealth/code-switching`), pulled via `load_afriswitch.py`. Public dataset, no HF token needed unless a specific chosen dataset is gated.

---

## 5. Current State of Each Major Piece

### Trust Score / Decision Agent (Toluwalase) — mostly done, one active bug being chased
- `rule_based.py`: implemented, weights tuned once already (`new_recipient` lowered from 0.30 → 0.15; `urgency_phrases.txt` narrowed to remove generic words like "urgently", "now", "stranded", "before tomorrow" — keeping only scam-specific phrases like "customs officer", "your account is frozen", etc.)
- `contract_adapter.py`: implemented, translates the `/trust/score` API contract into the flat feature dict `rule_based.score()` expects.
- `/trust/score` and `/trust/decision` endpoints: wired, mounted cleanly under `/trust` prefix (earlier bug — double `include_router` + hardcoded path causing duplicate/nested routes like `/transfers/trust/score` — was flagged and should now be fixed; **needs final confirmation this is resolved**).
- **`transfer_decision()` ledger-write: confirmed working** — writes to `trust_ledger` table via `record_ledger_entry(db, ledger_entry)`.
- **ACTIVE BUG BEING DIAGNOSED:** `labeled_calls.json` has `urgency_phrases` **hardcoded directly inside each call's `features` dict** (e.g. `"urgency_phrases": ["before tomorrow"]`), which means `extract_urgency_phrases()` and the narrowed `urgency_phrases.txt` are being **bypassed entirely** for these entries — the code checks `features.get("urgency_phrases")` first and only falls back to live extraction if that key is absent. This is why removing generic words from the .txt file didn't change the benchmark results for `genuine-health-007`, `genuine-business-019`, `genuine-family-020`.
  - **Fix in progress:** strip the `urgency_phrases` key entirely from all 40 entries in `labeled_calls.json` so the scorer is forced to derive it live from the transcript instead.
  - **Last known false-positive/negative rates (STALE, from before this fix):** FP rate 26.67% (4/15 — note: dataset size confusion happened here too, actual dataset is 40 calls total, 20 genuine/20 scam, not 30/15 — **re-verify totals after next benchmark run**), FN rate 6.67% (1/15 or equivalent proportion).
  - **`genuine-savings-015`** (flagged solely for 6.2x amount deviation, no other signal) is a known, accepted edge case — a judgment call, not a bug. Leave as-is unless it becomes a bigger pattern.
- **NEXT STEP:** re-run `diagnose_false_positives.py` after stripping hardcoded `urgency_phrases` from the dataset, confirm the 3 flagged entries clear (or land reasonably), and get a final, trustworthy FP/FN rate for the Benchmark Report.

### ASR Integration (Agoro/me)
- `sahara_asr.py`, `sahara_tts.py`: real API specs confirmed from `docs.voice.intron.io` (STT is WebSocket `wss://infer.voice.intron.io/stt/v1/stream`, 300s session cap; TTS is `POST https://infer.voice.intron.io/tts/v1/generate`, 100-char sync limit). Code written, using real message flow (SESSION_CREATED → INPUT_AUDIO_CHUNK → COMMIT → COMMITTED_TRANSCRIPT).
- **Got Intron API access** — received an extra $5 free credit via email from Intron for all challenge participants (separate from the $1 initial credit that caused earlier confusion).
- `orchestrator.py`: stub exists, not yet fully wired end-to-end — **this is likely still open, confirm status**.

### ASR Benchmark — Sahara vs Whisper vs MMS (the actual required benchmark)
- `run_asr_comparison.py`: created, contains 3 stub functions (`transcribe_sahara`, `transcribe_whisper`, `transcribe_mms`) plus working WER/numeric-WER math and a comparison loop.
- `transcribe_whisper()`: **being updated right now** to read a pre-computed lookup file (`whisper_transcripts.json`) instead of calling Whisper live, since transcription is happening in **Google Colab** (free T4 GPU) using `whisper.load_model("large-v3")`, not locally.
- **IN PROGRESS:** getting real Afriswitch audio clips downloaded locally (via `load_afriswitch.py` + `soundfile`, saving ~15 clips as `.wav` to an `afriswitch_clips/` folder), then uploading that folder to Colab, transcribing with Whisper there, downloading `whisper_transcripts.json`, and dropping it into `ml/data/synthetic/`.
- Notebook should be saved as `ml/notebooks/whisper_asr_benchmark.ipynb` once downloaded from Colab.
- `transcribe_sahara()`: still a stub — needs wiring to the real `sahara_asr.py` code (adapted from live-stream to file-based transcription).
- `transcribe_mms()`: still a stub — HuggingFace `transformers` + `facebook/mms-1b-all`, not started yet.
- **`ml/data/synthetic/asr_test_set.json` does not exist yet** — this is required before `run_asr_comparison.py` can run at all: needs `[{"audio_path": ..., "ground_truth": ..., "is_code_switched": bool}, ...]` built from the real Afriswitch clips + their ground-truth transcripts.

### Frontend (David)
- Status not recently confirmed in this conversation — **check in with David directly** on `ConfirmationCard.jsx`, `TrustLedgerView.jsx`, `Dashboard.jsx` progress.

### Infra/Data (Darius)
- `labeled_calls.json` exists, 40 entries (20 genuine/20 scam) — but see the active bug above; the `urgency_phrases` hardcoding issue traces back to how this file was generated and needs fixing at the source.
- Mock banking API, DB schema — status not recently confirmed, **check in directly**.

### Submission Deliverables (Agoro/me, per last confirmed assignment)
- `docs/SOLUTION_DESCRIPTION.md`: drafted, mostly complete, needs final numbers.
- `docs/BENCHMARK_REPORT.md`: template drafted with `[FILL IN]` markers — **cannot be finalized until `run_asr_comparison.py` actually produces real Sahara/Whisper/MMS numbers**.
- `docs/ETHICS_INCLUSION_NOTE.md`: drafted, mostly complete.
- `docs/SUBMISSION_SELF_AUDIT.md`: scorecard against the 5 official judging criteria (real-world impact, code-switching performance, product quality, technical execution, ethics/safety/inclusion) — use this to check readiness before submitting.
- **Demo video: assigned to Agoro (me), not yet recorded as of last check.**

---

## 6. Official Challenge Requirements (from Intron's email)
- **Deadline:** Aug 6, 2026, 1:00pm WAT
- **Must benchmark 3+ speech models** (Sahara + 2 others, global/local/open-source/commercial) **on real code-switched audio input** — this is the part that was "shallow"/missing and is currently being built (`run_asr_comparison.py`)
- **5 required submission items:**
  1. Solution Description
  2. Demo video (unlisted/public YouTube link) — **still needs recording**
  3. Docs (code/technical documentation)
  4. Benchmark Report (3+ models, pros/cons)
  5. Ethics/Inclusion Note
  6. (Optional) Benchmark Audios — consented, de-identified — skip unless real samples are ready
- **5 judging criteria:** real-world impact, code-switching performance, product quality, technical execution, ethics/safety/inclusion
- Real code-switching datasets available at `huggingface.co/collections/intronhealth/code-switching` (Afriswitch, AfriswitchCare, LyngualLabs)
- Benchmarking guidance repo: `github.com/intron-innovation/Intron-Multimodal-Benchmarking`

---

## 7. Immediate Next Steps, In Priority Order
1. **Fix the `urgency_phrases` hardcoding bug** — strip that key from all 40 entries in `labeled_calls.json`, re-run `diagnose_false_positives.py`, confirm the 3 known false positives clear or land reasonably.
2. **Finish the Afriswitch → Colab → Whisper pipeline** — download real audio clips locally, upload to Colab, transcribe with `large-v3`, download `whisper_transcripts.json`, drop into `ml/data/synthetic/`, save the notebook to `ml/notebooks/whisper_asr_benchmark.ipynb`.
3. **Build `ml/data/synthetic/asr_test_set.json`** — pairs of `{audio_path, ground_truth, is_code_switched}` from the Afriswitch clips, required before `run_asr_comparison.py` can run.
4. **Wire `transcribe_sahara()`** in `run_asr_comparison.py` — adapt the real Sahara ASR code from `sahara_asr.py` to work on a file instead of a live stream.
5. **Wire `transcribe_mms()`** — HuggingFace `facebook/mms-1b-all`, lowest priority of the 3, skip if time runs out (2-model comparison with Sahara + Whisper is still valid, just weaker than 3).
6. **Run `run_asr_comparison.py` for real**, get actual WER numbers, fill into `docs/BENCHMARK_REPORT.md`.
7. **Confirm frontend and infra status** with David and Darius directly — not recently checked in this thread.
8. **Confirm `orchestrator.py` end-to-end wiring status** — likely still incomplete.
9. **Record the demo video** (Agoro's responsibility).
10. **Run through `docs/SUBMISSION_SELF_AUDIT.md`** as a final check before submitting.

---

## 8. How to Use This Doc in a New Chat
Paste this entire file as your first message in a new chat, then say what you want to work on next (e.g. "let's fix the urgency_phrases bug" or "let's build the asr_test_set.json file"). No need to re-explain any of the above context — it's all here.