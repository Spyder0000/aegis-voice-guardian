# AEGIS Voice Guardian — Ethics, Safety & Inclusion Note

## Privacy & Data Use
- No live customer data is used in this build. All transaction and voice data used in development and demo is **synthetic and scripted** (see `ml/data/synthetic/`) — no real bank accounts, real names, or real recorded calls from real people.
- If real voice samples are ever collected (e.g. for future testing), consent and de-identification would be required before use, in line with the Sahara CodeSwitch Africa Challenge's own guidance on benchmark audio submissions.
- Transaction data (amount, recipient, transcript) is stored only in a sandboxed database for this build — no production banking data is touched at any point.

## Consent
- The demo uses team-generated, scripted scam and genuine call scenarios; no third-party voices or real customer interactions are recorded or used without consent.
- In a real deployment, customers would need to explicitly opt in to voice-based transaction monitoring, with clear disclosure of what's being analyzed (transaction risk signals) and what's explicitly *not* being done (voice is never used to verify identity).

## Safety Design
- **Voice is never the sole authenticator or sole release mechanism.** This is a deliberate safety choice: even if voice is spoofed or misheard, no transfer can be released without a tactile PIN confirmation on the Visual Confirmation Card. This directly limits the harm of both ASR error and voice-spoofing attacks.
- **The system is a soft-hold, not a hard block.** Flagged transactions pause for confirmation; they don't lock the customer out or make an irreversible decision autonomously. A human (the customer, or an escalated human reviewer for high-risk cases) always has the final say.
- **Every decision is logged and explainable.** The Trust Ledger records the specific reasons behind every hold, question, and outcome — this is designed so both the customer and any human reviewer can see exactly why the system intervened, rather than trusting an opaque score.

## Inclusion
- The system is designed around Nigerian-accented English and code-switching (English/Pidgin, English/Yoruba) specifically because most fraud-detection tooling is built and tuned on non-African speech data, which produces exactly the kind of false negatives (missed scam language) or false positives (unnecessary friction for genuine customers) this project is trying to avoid.
- Sahara's strength on African accents and numeric precision was the deciding factor in the architecture — using a global-only model here would systematically underserve the target population this tool is meant to protect.

## Known Limitations (disclosed, not hidden)
- The Trust Score is a **rule-based heuristic**, not a trained classifier — thresholds were tuned against a small synthetic test set, not real-world fraud data. This is a deliberate scope choice for a 72-hour build, not a claim of production-grade fraud detection.
- The banking integration is fully sandboxed/mocked; no real transfer, hold, or release action affects a real account.
- False positive/negative rates reported in the Benchmark Report are based on synthetic and scripted test data, and should be expected to shift once tested against real, diverse call patterns.

---
**[TODO before submission:]**
- [ ] Confirm no real personal data (names, numbers, voices) accidentally made it into any demo recording or dataset
- [ ] If any real audio samples are submitted as "Benchmark Audios," confirm consent and de-identification per the challenge's own submission guidance
