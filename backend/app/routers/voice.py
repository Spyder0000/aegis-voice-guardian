"""
Voice intake endpoint — Sahara ASR entry point.
Owner: Agoro Oluwatimilehin

Contract:
POST /voice/intake
  in:  raw audio (multipart) or streaming chunk
  out: { transcript, amount, recipient, urgency_flags }
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/intake")
def intake_voice():
    # TODO: call app.services.sahara_asr, extract entities
    raise NotImplementedError
