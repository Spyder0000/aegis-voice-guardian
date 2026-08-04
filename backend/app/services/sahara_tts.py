"""
Sahara TTS client wrapper — spoken clarifying question generation.
Endpoint: POST https://infer.voice.intron.io/tts/v1/generate
Hard limit: text must be <= 100 characters.
"""
import os
from typing import Dict, Any, Optional
import httpx

SAHARA_API_KEY = os.getenv("SAHARA_API_KEY", "")
SAHARA_TTS_URL = "https://infer.voice.intron.io/tts/v1/generate"

# Template library strictly capped under 100 characters per Sahara TTS specs
CLARIFYING_TEMPLATES = {
    "NEW_RECIPIENT": "New recipient {recipient}, {amount} Naira. Did you verify outside this call?",
    "HIGH_URGENCY": "High pressure detected. Did someone force you to send {amount} Naira now?",
    "AUTHORITY_IMPERSONATION": "Customs or police mentioned. Did you independently verify {recipient}?",
    "GENERIC_RISK": "Suspicious transfer of {amount} Naira to {recipient}. Do you want to proceed?"
}

def build_clarifying_prompt(risk_type: str, recipient: str = "recipient", amount: float = 0.0) -> str:
    """
    Builds a clarifying prompt guaranteed to be under 100 characters.
    """
    template = CLARIFYING_TEMPLATES.get(risk_type, CLARIFYING_TEMPLATES["GENERIC_RISK"])
    formatted = template.format(recipient=recipient[:15], amount=int(amount))
    if len(formatted) > 100:
        return formatted[:97] + "..."
    return formatted

async def speak_clarifying_question(
    text: str,
    voice: str = "en-US-Neural2-F",
    voice_language: str = "en",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates spoken audio from text.
    Raises ValueError if `text` exceeds Sahara's 100-character limit.
    """
    if len(text) > 100:
        raise ValueError(
            f"TTS text length ({len(text)} chars) exceeds Sahara's 100-character limit. "
            f"Prompt: '{text}'"
        )

    key = api_key or os.getenv("SAHARA_API_KEY", "")
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "voice": voice,
        "audio_config": {
            "audio_encoding": "MP3"
        }
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(SAHARA_TTS_URL, headers=headers, json=payload)

    if resp.status_code == 503:
        raise RuntimeError(f"Sahara TTS timed out (503 Service Unavailable): {resp.text}")

    resp.raise_for_status()
    
    # Return audio content bytes and prompt metadata
    return {
        "status": "success",
        "prompt": text,
        "audio_bytes": resp.content,
        "content_type": resp.headers.get("content-type", "audio/mpeg")
    }
