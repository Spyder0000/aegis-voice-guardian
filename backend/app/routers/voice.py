"""
Voice intake & real-time streaming endpoint — Sahara ASR entry point.
Owner: Agoro Oluwatimilehin

Contract:
POST /voice/intake  -> { transcript, amount, recipient, urgency_flags, risk_evaluation, clarifying_question }
WS /voice/stream    -> Bidirectional WebSocket streaming mic audio in & transcript events out
"""
import json
import base64
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel

from app.agents.orchestrator import orchestrator
from app.services.sahara_asr import SaharaSTTSession

router = APIRouter()

class VoiceIntakeRequest(BaseModel):
    transcript: str
    session_id: Optional[str] = None

class TTSPromptRequest(BaseModel):
    prompt: str

@router.post("/intake")
def intake_voice(request: VoiceIntakeRequest):
    """
    Processes voice transcript through entity extraction and risk evaluation pipeline.
    """
    if not request.transcript.strip():
        raise HTTPException(status_code=400, detail="Transcript cannot be empty.")
    
    result = orchestrator.process_voice_transcript(request.transcript)
    return result

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
            await websocket.send_json({
                "event": "SESSION_CREATED",
                "session_id": stt_session.session_id
            })
            
            async for event in stt_session.stream(generate_audio_chunks()):
                msg_type = event.get("message_type")
                if msg_type == "PARTIAL_TRANSCRIPT":
                    await websocket.send_json({
                        "event": "PARTIAL_TRANSCRIPT",
                        "text": event.get("transcript", "")
                    })
                elif msg_type == "COMMITTED_TRANSCRIPT":
                    transcript_text = event.get("transcript", "")
                    intake_result = orchestrator.process_voice_transcript(transcript_text)
                    await websocket.send_json({
                        "event": "COMMITTED_TRANSCRIPT",
                        "text": transcript_text,
                        "intake_result": intake_result
                    })
                    break
    except Exception as e:
        await websocket.send_json({
            "event": "ERROR",
            "message": str(e)
        })
    finally:
        await websocket.close()
