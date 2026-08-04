"""
Agent Orchestrator — MCP-style ask-clarify-decide loop.
Owner: Agoro Oluwatimilehin

Pipeline:
voice intake -> intent/entity extraction -> trust score evaluation -> 
  low risk: release
  medium/high risk: soft hold -> Sahara TTS clarifying question + visual confirmation card -> decision agent
"""
from typing import Dict, Any, List
from app.services.sahara_asr import extract_entities
from app.services.sahara_tts import build_clarifying_prompt, speak_clarifying_question

class AgentOrchestrator:
    """
    Coordinates entity extraction, risk assessment, TTS prompt generation, and decision routing.
    """

    def process_voice_transcript(self, transcript: str, user_id: str = "default_user") -> Dict[str, Any]:
        """
        Processes spoken transcript through extraction and initial risk evaluation.
        """
        # 1. Entity & Urgency Extraction
        entities = extract_entities(transcript)
        amount = entities["amount"]
        recipient = entities["recipient"]
        urgency_flags = entities["urgency_flags"]

        # 2. Risk Evaluation Rule Engine
        reasons: List[str] = []
        risk_score = 0.1
        risk_level = "LOW"

        if amount > 100000:
            risk_score += 0.35
            reasons.append(f"Transfer amount (₦{amount:,.2f}) exceeds normal daily limit.")
        
        if urgency_flags:
            risk_score += 0.40
            reasons.append(f"Urgent/high-pressure keywords detected: {', '.join(urgency_flags)}")

        if recipient == "Unknown":
            risk_score += 0.20
            reasons.append("Recipient name could not be verified in trusted contact list.")

        if risk_score >= 0.60:
            risk_level = "HIGH"
        elif risk_score >= 0.35:
            risk_level = "MEDIUM"

        # 3. Soft Hold & Clarifying Prompt Generation for MED/HIGH Risk
        clarifying_question = None
        if risk_level != "LOW":
            risk_type = "HIGH_URGENCY" if urgency_flags else ("NEW_RECIPIENT" if recipient != "Unknown" else "GENERIC_RISK")
            clarifying_question = build_clarifying_prompt(risk_type, recipient=recipient, amount=amount)

        return {
            "transcript": transcript,
            "amount": amount,
            "currency": entities["currency"],
            "recipient": recipient,
            "urgency_flags": urgency_flags,
            "risk_evaluation": {
                "score": round(risk_score, 2),
                "risk_level": risk_level,
                "reasons": reasons,
                "action": "RELEASE" if risk_level == "LOW" else "SOFT_HOLD"
            },
            "clarifying_question": clarifying_question
        }

orchestrator = AgentOrchestrator()
