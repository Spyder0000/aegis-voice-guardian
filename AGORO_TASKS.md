# Agoro's Task Sheet — AEGIS Voice Guardian
**Role:** Lead / Core Agent Loop
**Owns:** Sahara ASR integration, Sahara TTS integration, Agent Orchestrator, `/voice/intake` endpoint, API contract, final integration

---

## Phase 0 — Get Access (do this first, it can take time to provision)

- [ X] Go to `voice.intron.io`, sign in with your account
- [ X] Find the **Developers** tab/section in your dashboard
- [ X] Generate/copy your **API key** — treat it like a password, never commit it to GitHub
- [ X] Confirm whether your account has **Integrator** status — both STT streaming and TTS generate require it
  - If you only see in-app usage and no API/developer access even with the $1 credit, email `voice@intron.io` right away — this is the team's #1 blocker and it's not something code can fix
- [ X ] Ask about **hackathon credits** — $1 of credit will not cover a 72-hour build; get this sorted before the team burns real money on trial-and-error

---

## Phase 1 — Prove Connectivity (before writing any app code)

### 1a. Install `wscat` on your own machine (terminal, not the Intron website)
```bash
npm install -g wscat
```
(If this fails, install Node.js from nodejs.org first.)

### 1b. Save your key as an environment variable
```bash
export SAHARA_API_KEY="paste_your_key_here"
```

### 1c. Test the STT websocket
```bash
wscat -c "wss://infer.voice.intron.io/stt/v1/stream?sample_rate=16000&bit_rate=16&num_channels=1&use_language_asr_input=en" \
  -H "Authorization: Bearer $SAHARA_API_KEY"
```
**Expected:** terminal prints a `SESSION_CREATED` message back.

**If it fails:**
| Symptom | Likely cause |
|---|---|
| 401 / connection refused | Key wrong or not activated |
| "Integrator account required" error | Account tier doesn't have streaming STT enabled |

- [x] Confirm `SESSION_CREATED` received
- [x] Send a test `INPUT_AUDIO_CHUNK` message, then `COMMIT`, confirm `AUDIO_CHUCK_ACK` received back

### 1d. Test the TTS generate endpoint
- [x] Confirm you get back a `200` with audio content from TTS generate endpoint
- [x] **Verify the correct `voice` value** for TTS generation


---

## Phase 2 — Publish the Contract (unblocks Toluwalase & David)

STT is a **persistent websocket**, not a simple request/response — this changes the API design from a plain REST call:

- Your FastAPI backend holds the Sahara websocket connection **server-side**
- Frontend streams mic audio **in** to your backend
- Your backend pushes `PARTIAL_TRANSCRIPT` / `COMMITTED_TRANSCRIPT` events **out** to the frontend (via your own websocket or SSE)

**Publish this in the team channel / `docs/ARCHITECTURE.md` before Hour 6:**
```
POST /voice/intake   → { transcript, amount, recipient, urgency_flags }
POST /trust/score    → { risk_level, score, reasons }        (Toluwalase's endpoint)
POST /transfers/decision → { status: released | held | escalated }
```

- [x] Contract published and confirmed read by Toluwalase + David

---

## Phase 3 — Build

### `sahara_asr.py` (build first — unblocks everything downstream)
Real endpoint: `wss://infer.voice.intron.io/stt/v1/stream`

Key facts:
- Max session lifetime: **300s** → reconnect/chunk if a call runs longer
- Max idle audio gap: 60s
- Chunk size: 1 KB–32 KB
- Query params: `sample_rate` (16000), `bit_rate` (16), `num_channels` (1), `use_language_asr_input` ("en")
- Flow: connect → `SESSION_CREATED` → send `INPUT_AUDIO_CHUNK` messages → `COMMIT` → receive `COMMITTED_TRANSCRIPT`
- Error frames to handle: `AUTHENTICATION_ERROR`, `QUOTA_EXCEEDED`, `RESOURCE_EXHAUSTED`, `SESSION_TIME_LIMIT_EXCEEDED`, `INSUFFICIENT_AUDIO_ACTIVITY`

```python
"""
Sahara ASR v2 client — WebSocket streaming STT.
Endpoint: wss://infer.voice.intron.io/stt/v1/stream
Requires an Integrator Account API key.
"""
import asyncio
import base64
import json
import os
from typing import AsyncGenerator, Optional

import websockets

SAHARA_API_KEY = os.environ["SAHARA_API_KEY"]
SAHARA_WS_URL = "wss://infer.voice.intron.io/stt/v1/stream"


class SaharaSTTSession:
    """
    Wraps one Sahara streaming session.
    Usage:
        async with SaharaSTTSession() as session:
            async for event in session.stream(audio_chunks):
                ...
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        bit_rate: int = 16,
        num_channels: int = 1,
        language: str = "en",
    ):
        self.params = {
            "sample_rate": sample_rate,
            "bit_rate": bit_rate,
            "num_channels": num_channels,
            "use_language_asr_input": language,
        }
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.session_id: Optional[str] = None

    async def __aenter__(self):
        query = "&".join(f"{k}={v}" for k, v in self.params.items())
        url = f"{SAHARA_WS_URL}?{query}"
        self.ws = await websockets.connect(
            url,
            extra_headers={"Authorization": f"Bearer {SAHARA_API_KEY}"},
        )
        first = json.loads(await self.ws.recv())
        if first.get("message_type") == "AUTHENTICATION_ERROR":
            raise RuntimeError(f"Sahara auth failed: {first.get('message')}")
        if first.get("message_type") != "SESSION_CREATED":
            raise RuntimeError(f"Unexpected first message: {first}")
        self.session_id = first["session_id"]
        return self

    async def __aexit__(self, *exc):
        if self.ws:
            await self.ws.close()

    async def stream(
        self, audio_chunks: AsyncGenerator[bytes, None]
    ) -> AsyncGenerator[dict, None]:
        """
        Feed raw PCM16LE audio bytes in via `audio_chunks`; yields every
        server event (PARTIAL_TRANSCRIPT, COMMITTED_TRANSCRIPT, errors, etc.)
        so the caller can decide what to do with partials vs. the final.
        """
        send_task = asyncio.create_task(self._send_audio(audio_chunks))

        try:
            async for raw in self.ws:
                event = json.loads(raw)
                yield event

                if event.get("message_type") == "COMMITTED_TRANSCRIPT":
                    break

                if event.get("message_type") in (
                    "AUTHENTICATION_ERROR",
                    "QUOTA_EXCEEDED",
                    "SESSION_TIME_LIMIT_EXCEEDED",
                ):
                    # server closes the connection after these
                    break
        finally:
            send_task.cancel()

    async def _send_audio(self, audio_chunks: AsyncGenerator[bytes, None]):
        ack_id = 0
        async for chunk in audio_chunks:
            ack_id += 1
            await self.ws.send(
                json.dumps(
                    {
                        "message_type": "INPUT_AUDIO_CHUNK",
                        "audio_base_64": base64.b64encode(chunk).decode(),
                        "ack_id": ack_id,
                    }
                )
            )
        await self.ws.send(json.dumps({"message_type": "COMMIT"}))


async def transcribe(audio_chunks: AsyncGenerator[bytes, None]) -> dict:
    """
    Convenience wrapper for the orchestrator: consumes a full stream,
    returns the final COMMITTED_TRANSCRIPT payload.
    """
    async with SaharaSTTSession() as session:
        async for event in session.stream(audio_chunks):
            if event.get("message_type") == "COMMITTED_TRANSCRIPT":
                return event
            if event.get("message_type") in (
                "AUTHENTICATION_ERROR",
                "QUOTA_EXCEEDED",
                "ERROR",
                "INPUT_ERROR",
            ):
                raise RuntimeError(f"Sahara STT error: {event}")
    raise RuntimeError("Stream ended without a COMMITTED_TRANSCRIPT")
```

- [x] `sahara_asr.py` implemented and tested against a real audio file

---

### `sahara_tts.py` (build second)
Real endpoint: `POST https://infer.voice.intron.io/tts/v1/generate`

Key facts:
- **Hard limit: text must be ≤ 100 characters** on this sync endpoint — design clarifying questions short from the start
- Rate limit: 30 requests/minute
- Required body: `text`, `voice_accent`, `voice_gender` (optional: `voice_language`, `output_audio_format`)
- Can return `503` if generation takes >120s — needs poll-status fallback (endpoint TBD, confirm at `docs.voice.intron.io/docs/tts/tts-status`)

```python
"""
Sahara TTS v2 client — synchronous generate endpoint.
Endpoint: POST https://infer.voice.intron.io/tts/v1/generate
Hard limit: text must be <= 100 characters.
"""
import os
import httpx

SAHARA_API_KEY = os.environ["SAHARA_API_KEY"]
SAHARA_TTS_URL = "https://infer.voice.intron.io/tts/v1/generate"
SAHARA_TTS_STATUS_URL = "https://infer.voice.intron.io/tts/v1/status"  # confirm path in docs/tts/tts-status


async def speak_clarifying_question(
    text: str,
    voice_accent: str = "nigerian",  # TODO: confirm valid value from supported-accents docs
    voice_gender: str = "female",
    voice_language: str = "en",
) -> str:
    """
    Returns a URL to the generated audio file.
    Raises ValueError if `text` exceeds Sahara's 100-char sync limit —
    keep clarifying questions short by design, e.g.:
        "New recipient, ₦150,000 — did you verify this outside the call?"
    """
    if len(text) > 100:
        raise ValueError(
            f"TTS text is {len(text)} chars; Sahara's sync /generate endpoint "
            "caps at 100. Shorten the prompt or switch to the async queue endpoint."
        )

    async with httpx.AsyncClient(timeout=125.0) as client:
        resp = await client.post(
            SAHARA_TTS_URL,
            headers={
                "Authorization": f"Bearer {SAHARA_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "voice_language": voice_language,
                "voice_accent": voice_accent,
                "voice_gender": voice_gender,
            },
        )

    if resp.status_code == 503:
        # Generation took >120s server-side; poll status with the returned text-id.
        # TODO: implement poll_tts_status(text_id) once confirmed on a live test call.
        raise RuntimeError(f"TTS timed out server-side, needs status polling: {resp.json()}")

    resp.raise_for_status()
    data = resp.json()["data"]
    return data["audio_path"]
```

- [x] Build a small library of clarifying-question templates, every one ≤ 100 chars, e.g.:
  - `"New recipient, large amount — did you verify this outside the call?"`
  - `"This mentions 'customs officer' — has this been confirmed independently?"`
- [x] `sahara_tts.py` implemented and tested

---

### `orchestrator.py` (build third — the ask-clarify-decide loop)
Wires everything together:
```
voice intake → sahara_asr.transcribe() → entity extraction (amount, recipient, urgency)
    → POST to Toluwalase's /trust/score
        LOW risk  → release, log to Trust Ledger
        MED/HIGH  → soft hold (Darius's mock banking API)
                     → sahara_tts.speak_clarifying_question()
                     → David's Visual Confirmation Card (frontend)
                     → user response → Toluwalase's decision agent
                     → release / escalate → log to Trust Ledger
```
- [x] `orchestrator.py` implemented
- [x] `/voice/intake` endpoint wired to orchestrator


---

## Phase 4 — Integration (Day 3 / Hours 56–72)

- [ ] Full pipeline runs end-to-end on one real test call (scam scenario)
- [ ] Full pipeline runs end-to-end on one real test call (genuine scenario, confirms no false hold)
- [ ] Demo dry run with the whole team
- [ ] Confirm Trust Ledger shows a clean, explainable log entry for both test runs

---

## Open Questions / Risks to Track

- [ ] Does the $1 credit / current account tier actually unlock Integrator-level API access, or just in-app usage?
- [ ] Confirmed valid `voice_accent` values (currently assumed `"nigerian"` — unverified)
- [ ] Confirmed shape of the TTS `503` poll-status response
- [ ] Fallback plan if STT sessions can't sustain a realistic call length under the 300s cap

wscat -c "wss://infer.voice.intron.io/stt/v1/stream?sample_rate=16000&bit_rate=16&num_channels=1&use_language_asr_input=en" -H"Authorization: Bearer $env:SAHARA_API_KEY"
