"""
Sahara ASR v2 client — WebSocket streaming STT.
Endpoint: wss://infer.voice.intron.io/stt/v1/stream
Requires an Integrator Account API key.
"""
import asyncio
import base64
import json
import os
import re
from typing import AsyncGenerator, Dict, Any, Optional

import websockets

SAHARA_API_KEY = os.getenv("SAHARA_API_KEY", "")
SAHARA_WS_URL = "wss://infer.voice.intron.io/stt/v1/stream"

# Urgency and scam indicator keywords commonly found in fraudulent bank transfers
URGENCY_KEYWORDS = [
    "emergency", "urgent", "immediately", "right now", "police", 
    "customs", "officer", "kidnap", "accident", "hospital",
    "ransom", "jail", "arrest", "court", "secret"
]

class SaharaSTTSession:
    """
    Wraps one Sahara STT WebSocket streaming session.
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
        api_key: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("SAHARA_API_KEY", "")
        self.params = {
            "sample_rate": sample_rate,
            "bit_rate": bit_rate,
            "num_channels": num_channels,
            "use_language_asr_input": language,
        }
        self.ws: Optional[Any] = None
        self.session_id: Optional[str] = None

    async def __aenter__(self):
        query = "&".join(f"{k}={v}" for k, v in self.params.items())
        url = f"{SAHARA_WS_URL}?{query}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        # Multi-version websockets connection handling
        for param in ["additional_headers", "extra_headers", "headers"]:
            try:
                self.ws = await websockets.connect(url, **{param: headers})
                break
            except TypeError:
                continue

        if not self.ws:
            raise RuntimeError("Failed to establish WebSocket connection to Sahara STT server.")

        first_raw = await self.ws.recv()
        first = json.loads(first_raw)
        if first.get("message_type") == "AUTHENTICATION_ERROR":
            raise RuntimeError(f"Sahara ASR authentication failed: {first.get('message')}")
        if first.get("message_type") != "SESSION_CREATED":
            raise RuntimeError(f"Unexpected initial message from Sahara ASR: {first}")
        
        self.session_id = first.get("session_id")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.ws:
            await self.ws.close()

    async def stream(
        self, audio_chunks: AsyncGenerator[bytes, None]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Feeds raw PCM16LE audio bytes via `audio_chunks`; yields server events
        (PARTIAL_TRANSCRIPT, COMMITTED_TRANSCRIPT, errors) to the caller.
        """
        send_task = asyncio.create_task(self._send_audio(audio_chunks))

        try:
            async for raw in self.ws:
                event = json.loads(raw)
                yield event

                if event.get("message_type") in ("COMMITTED_TRANSCRIPT", "INSUFFICIENT_AUDIO_ACTIVITY"):
                    break

                if event.get("message_type") in (
                    "AUTHENTICATION_ERROR",
                    "QUOTA_EXCEEDED",
                    "SESSION_TIME_LIMIT_EXCEEDED",
                ):
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
                        "audio_base_64": base64.b64encode(chunk).decode("utf-8"),
                        "ack_id": ack_id,
                    }
                )
            )
        await self.ws.send(json.dumps({"message_type": "COMMIT"}))


def extract_entities(transcript: str) -> Dict[str, Any]:
    """
    Extracts transfer amount, recipient name, and urgency flags from transcript text.
    """
    text_lower = transcript.lower()
    
    # 1. Amount Extraction (Naira, ₦, "50000 naira", "fifty thousand", etc.)
    amount = 0.0
    # Match digit amounts e.g., 50000, 50,000, 50k, 100000 naira
    digit_match = re.search(r'(?:₦|naira|ngn)?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:k|thousand|naira|ngn)?', text_lower)
    if digit_match:
        raw_val = digit_match.group(1).replace(',', '')
        try:
            amount = float(raw_val)
            if 'k' in digit_match.group(0):
                amount *= 1000
        except ValueError:
            amount = 0.0

    # 2. Recipient Extraction e.g., "to Chukwuma", "transfer to Blessing", "send to John"
    recipient = "Unknown"
    recipient_match = re.search(r'(?:to|for|send to|transfer to)\s+([A-Z][a-z]+|[a-z]+)', transcript, re.IGNORECASE)
    if recipient_match:
        candidate = recipient_match.group(1).strip().capitalize()
        if candidate.lower() not in ["the", "my", "a", "an", "some", "naira"]:
            recipient = candidate

    # 3. Urgency Flags
    flags = []
    for keyword in URGENCY_KEYWORDS:
        if keyword in text_lower:
            flags.append(f"FLAG_{keyword.upper()}")

    return {
        "transcript": transcript,
        "amount": amount,
        "currency": "NGN",
        "recipient": recipient,
        "urgency_flags": flags
    }


async def transcribe(audio_chunks: AsyncGenerator[bytes, None]) -> Dict[str, Any]:
    """
    Convenience wrapper: consumes a full audio stream, returns the final COMMITTED_TRANSCRIPT payload.
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
