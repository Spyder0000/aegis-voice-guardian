# AEGIS Voice Guardian — Solution Description
**Deep Learning Indaba 2026 — "Whose Intelligence?" Hackathon**

## The Problem
Authorized push payment (APP) and social engineering scams are the fastest-growing fraud category in African digital banking — victims are manipulated into *willingly* authorizing their own fraudulent transfers (fake "customs officer" calls, "your account is frozen" scams, romance and investment scams). Traditional fraud detection, built around stolen credentials or anomalous transactions, never catches this category because the transaction itself looks completely normal — it's the human who's been socially engineered, not the account.

Voice banking and voice-driven transfers are scaling fast across Africa, and every new voice channel is a new channel scammers can exploit through pressure, urgency, and authority-impersonation, delivered in the customer's own language and accent.

## Target Users
A retail banking customer initiating a transfer via a voice banking channel — e.g., a small business owner or salaried individual in Nigeria doing routine mobile/voice transfers, representing a large and growing population of digital banking users vulnerable to real-time social engineering pressure.

## The Solution
AEGIS Voice Guardian listens to a voice transfer request and treats the voice content itself as a **behavioral trust signal**, not just a command to execute. Sahara ASR transcribes the request and extracts amount, recipient, and urgency/authority-impersonation language. This is checked against the customer's Financial Trust Profile (new recipient, unusual amount, pressure language). If risk is elevated, the system:

1. Places a soft hold on the transfer (not a hard block — the customer isn't locked out, just paused)
2. Asks a spoken clarifying question via Sahara TTS, in the customer's own language/accent
3. Simultaneously shows a **Visual Confirmation Card** — amount and recipient re-displayed clearly, requiring a tactile PIN confirm before any release

Voice is never the sole authenticator and never the sole release mechanism — a screen-and-PIN confirmation is what actually moves the money, closing the single biggest technical risk (numeric mishearing, e.g. ₦10,000 heard as ₦100,000) by design rather than by disclaimer.

Every intervention — what was flagged, why, and what happened — is logged in an explainable Trust Ledger.

## Key Technical Decisions
- **Rule-based Trust Score, not a trained ML model, for this build.** Built over a 72-hour hackathon window with no real fraud-labeled data, a transparent rules + weighted-scoring baseline is both more honest about its confidence and easier to validate and explain to judges than an undertrained black-box classifier. XGBoost was deliberately deprioritized as a "bonus, if time allows" item rather than the core deliverable.
- **Voice as a trust signal, not an authenticator.** Voice content and behavioral context drive the risk score; identity is never verified by voice alone, mitigating voice-spoofing risk directly in the architecture rather than as an afterthought.
- **Dual-channel confirmation (spoken + visual/tactile).** A single-channel design (voice-only, or screen-only) leaves either a numeric-mishearing risk or a lower-friction bypass risk; combining both closes the gap that either channel leaves open on its own.
- **Sandboxed banking integration.** All transfer actions run against a mock banking API for this build — explicitly not connected to a live bank, to avoid overclaiming production-readiness.

## Category
Fintech, Telco & Customer Experience — voice banking / fraud prevention.

## Standout Factor
Most voice+fintech entries use Sahara for autofill or voice commands — voice as an input method. AEGIS uses voice as a behavioral trust signal that drives an autonomous, two-way agentic intervention (ask → listen → decide), closing the loop rather than just transcribing. This directly answers "Whose Intelligence?" — the system shows the user exactly why it intervened, rather than acting as an opaque fraud-blocking chatbot.
