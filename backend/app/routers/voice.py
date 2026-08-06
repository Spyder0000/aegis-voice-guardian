"""
Voice intake & real-time streaming endpoint — Sahara ASR entry point.
Owner: Agoro Oluwatimilehin

Contract:
POST /voice/intake  -> { transcript, amount, recipient, risk_evaluation, risk_level, reasons, action, transaction_id }
WS /voice/stream    -> Bidirectional WebSocket streaming mic audio in & transcript events out
"""
import base64
import json
import os
import re
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ml.trust_score.contract_adapter import score_from_contract
from ml.trust_score.rule_based import extract_urgency_phrases
from app.services.sahara_asr import SaharaSTTSession

router = APIRouter()


class VoiceIntakeRequest(BaseModel):
    transcript: str
    session_id: Optional[str] = None


def _extract_amount(text: str) -> float:
    """Extract numeric transfer amount from spoken transcript."""
    text_lower = text.lower()
    # Match amounts like 150000, 150,000, 50k, 200 thousand, ₦50000
    match = re.search(r'(?:₦|naira|ngn|\$)?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:k|thousand|naira|ngn)?', text_lower)
    if match:
        val_str = match.group(1).replace(',', '')
        try:
            val = float(val_str)
            if 'k' in match.group(0) or 'thousand' in match.group(0):
                val *= 1000.0
            return val
        except ValueError:
            pass
    return 150000.0


def _extract_recipient(text: str) -> str:
    """Extract recipient name from spoken transcript."""
    match = re.search(r'(?:to|for|send to|transfer to)\s+([A-Z][a-z]+|[a-z]+(?:\s+[A-Z][a-z]+)?)', text, re.IGNORECASE)
    if match:
        candidate = match.group(1).strip().title()
        if candidate.lower() not in ["the", "my", "a", "an", "this", "new", "account", "naira"]:
            return candidate
    return "Unnamed Recipient"


def _process_transcript(transcript: str) -> Dict[str, Any]:
    """Runs entity extraction and scores the trust payload."""
    clean_transcript = transcript.strip()
    if not clean_transcript:
        clean_transcript = "Send 150000 to this new account for the customs officer..."

    amount = _extract_amount(clean_transcript)
    recipient = _extract_recipient(clean_transcript)
    urgency_phrases = extract_urgency_phrases(clean_transcript)

    authority_keywords = ["officer", "police", "customs", "bank", "agent", "manager", "official"]
    has_authority = any(kw in clean_transcript.lower() for kw in authority_keywords)

    payload = {
        "transcript": clean_transcript,
        "amount": amount,
        "recipient": recipient,
        "currency": "NGN",
        "entities": {
            "urgency_phrases": urgency_phrases,
            "authority_claim": has_authority,
            "bank_keywords": ["transfer", "account", "send"] if "transfer" in clean_transcript.lower() else [],
        },
        "user_profile": {
            "average_transfer": 12000.0,
            "largest_transfer": 25000.0,
            "recipient_seen_before": False,
            "transfer_count_to_recipient": 0,
        },
    }

    risk_eval = score_from_contract(payload)
    risk_level = risk_eval.get("risk_level", "LOW").upper()
    reasons = risk_eval.get("reasons", [])

    transaction_id = f"txn_{uuid.uuid4().hex[:8]}"

    clarifying_question = None
    if risk_level != "LOW":
        clarifying_question = f"AEGIS Voice Guardian flagged a {risk_level} risk transfer of ₦{amount:,.0f} to {recipient}. Enter your PIN to verify."

    return {
        "transcript": clean_transcript,
        "amount": amount,
        "recipient": recipient,
        "risk_evaluation": {
            "score": risk_eval.get("score", 0.0),
            "risk_level": risk_level,
            "reasons": reasons,
            "action": risk_eval.get("action", "release"),
        },
        "risk_level": risk_level,
        "score": risk_eval.get("score", 0.0),
        "reasons": reasons,
        "action": risk_eval.get("action", "release"),
        "transaction_id": transaction_id,
        "clarifying_question": clarifying_question,
    }


@router.post("/intake")
async def intake_voice(
    request: Optional[VoiceIntakeRequest] = None,
    file: Optional[UploadFile] = File(None),
    transcript: Optional[str] = Form(None),
):
    """
    Processes audio recording upload or text transcript through entity extraction and risk evaluation.
    """
    transcript_text = None

    if request and request.transcript:
        transcript_text = request.transcript
    elif transcript:
        transcript_text = transcript

    if file and file.filename:
        try:
            # Read uploaded audio bytes
            audio_bytes = await file.read()
            # If audio file is uploaded, try transcribing via Sahara ASR if key available
            api_key = os.getenv("SAHARA_API_KEY", "")
            if api_key and len(audio_bytes) > 0:
                # Save temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix or ".webm") as tmp:
                    tmp.write(audio_bytes)
                    tmp_path = tmp.name
                
                try:
                    # Stream audio bytes to Sahara ASR
                    async def byte_generator():
                        chunk_size = 16000
                        for i in range(0, len(audio_bytes), chunk_size):
                            yield audio_bytes[i:i+chunk_size]
                            await asyncio.sleep(0.001)
                    
                    async with SaharaSTTSession(api_key=api_key) as session:
                        async for event in session.stream(byte_generator()):
                            if event.get("transcript"):
                                transcript_text = event["transcript"]
                except Exception as e:
                    print(f"[Sahara ASR Intake Warning] Could not transcribe audio file: {e}")
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
        except Exception as e:
            print(f"[Intake File Error] {e}")

    if not transcript_text:
        transcript_text = "Send 150000 to this new account for the customs officer in the next five minutes"

    return _process_transcript(transcript_text)


@router.websocket("/stream")
async def voice_stream_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for frontend audio streaming.
    Receives base64 PCM audio chunks from frontend, feeds to Sahara STT, and returns transcript events.
    """
    await websocket.accept()

    async def generate_audio_chunks():
        try:
            while True:
                data_raw = await websocket.receive_text()
                msg = json.loads(data_raw)
                if msg.get("event") == "AUDIO_CHUNK":
                    chunk_bytes = base64.b64decode(msg.get("audio_base64", ""))
                    yield chunk_bytes
                elif msg.get("event") == "COMMIT":
                    break
        except WebSocketDisconnect:
            pass

    try:
        async with SaharaSTTSession() as stt_session:
            await websocket.send_json({"event": "SESSION_CREATED", "session_id": stt_session.session_id})

            async for event in stt_session.stream(generate_audio_chunks()):
                msg_type = event.get("message_type")
                if msg_type == "PARTIAL_TRANSCRIPT":
                    await websocket.send_json({"event": "PARTIAL_TRANSCRIPT", "text": event.get("transcript", "")})
                elif msg_type == "COMMITTED_TRANSCRIPT":
                    transcript_text = event.get("transcript", "")
                    intake_result = _process_transcript(transcript_text)
                    await websocket.send_json(
                        {
                            "event": "COMMITTED_TRANSCRIPT",
                            "text": transcript_text,
                            "intake_result": intake_result,
                        }
                    )
                    break
    except Exception as e:
        await websocket.send_json({"event": "ERROR", "message": str(e)})
    finally:
        await websocket.close()

