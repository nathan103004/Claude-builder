from __future__ import annotations

import json
import os
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["chat"])

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------
_SYSTEM_EN = """\
You are SantéNav, a Quebec health navigation assistant helping users choose \
the right type of medical care.

Available care types (use EXACTLY these keys in your JSON output):
- consultation_urgente: Urgent care (need care today)
- consultation_semi_urgente: Semi-urgent care (need care within 1-2 days)
- suivi: Regular follow-up (non-urgent check-in)
- suivi_pediatrique: Pediatric follow-up (for a child)
- suivi_grossesse: Pregnancy follow-up (prenatal care)

Rules:
1. EMERGENCY: If the user describes a life-threatening situation (chest pain, \
difficulty breathing, stroke symptoms, severe bleeding, loss of consciousness), \
immediately output ONLY this JSON: \
{"service_type": "emergency", "explanation": "<brief reason in English>"}
2. For non-emergencies, ask at most 1-2 short clarifying questions.
3. When you have enough information to recommend, output ONLY this JSON on \
a new line (no other text after it): \
{"service_type": "<key>", "explanation": "<brief reason in English>"}
4. Respond in English. Keep responses brief and clear.\
"""

_SYSTEM_FR = """\
Tu es SantéNav, un assistant de navigation de santé au Québec qui aide les \
utilisateurs à choisir le bon type de soins médicaux.

Types de soins disponibles (utilise EXACTEMENT ces clés dans ta sortie JSON) :
- consultation_urgente : Consultation urgente (besoin de soins aujourd'hui)
- consultation_semi_urgente : Consultation semi-urgente (soins dans 1 à 2 jours)
- suivi : Suivi régulier (consultation non urgente)
- suivi_pediatrique : Suivi pédiatrique (pour un enfant)
- suivi_grossesse : Suivi de grossesse (soins prénataux)

Règles :
1. URGENCE : Si l'utilisateur décrit une situation mettant sa vie en danger \
(douleur thoracique, difficulté à respirer, symptômes d'AVC, saignement grave, \
perte de conscience), réponds UNIQUEMENT avec ce JSON : \
{"service_type": "emergency", "explanation": "<brève raison en français>"}
2. Pour les non-urgences, pose au maximum 1 à 2 courtes questions de clarification.
3. Quand tu as suffisamment d'informations pour recommander, écris UNIQUEMENT \
ce JSON sur une nouvelle ligne (rien d'autre après) : \
{"service_type": "<clé>", "explanation": "<brève raison en français>"}
4. Réponds en français. Sois bref et clair.\
"""

SYSTEM_PROMPTS: dict[str, str] = {"en": _SYSTEM_EN, "fr": _SYSTEM_FR}

_FINAL_DIRECTIVE_EN = (
    "\n\nThis is your final response. You MUST now output your recommendation "
    "as JSON: {\"service_type\": \"<key>\", \"explanation\": \"<reason>\"}"
)
_FINAL_DIRECTIVE_FR = (
    "\n\nC'est ta dernière réponse. Tu DOIS maintenant donner ta recommandation "
    "en JSON : {\"service_type\": \"<clé>\", \"explanation\": \"<raison>\"}"
)
FINAL_DIRECTIVES: dict[str, str] = {"en": _FINAL_DIRECTIVE_EN, "fr": _FINAL_DIRECTIVE_FR}


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------
class ChatMessage(BaseModel):
    role: str    # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    locale: str = "fr"


# ---------------------------------------------------------------------------
# Streaming generator
# ---------------------------------------------------------------------------
async def _stream_chat(messages: list[ChatMessage], locale: str) -> AsyncIterator[str]:
    """Yield SSE events: `event: token` for each text delta, then `event: result`."""
    from anthropic import AsyncAnthropic  # imported here so missing package fails at call-time

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        yield 'event: error\ndata: {"code": "API_UNAVAILABLE"}\n\n'
        return

    system = SYSTEM_PROMPTS.get(locale, SYSTEM_PROMPTS["fr"])
    user_turn_count = sum(1 for m in messages if m.role == "user")
    if user_turn_count >= 2:
        system += FINAL_DIRECTIVES.get(locale, FINAL_DIRECTIVES["fr"])

    client = AsyncAnthropic(api_key=api_key)
    full_text = ""

    try:
        async with client.messages.stream(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=system,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        ) as stream:
            async for delta in stream.text_stream:
                full_text += delta
                yield f"event: token\ndata: {json.dumps({'text': delta})}\n\n"
    except Exception as exc:
        yield f"event: error\ndata: {json.dumps({'code': 'API_ERROR', 'message': str(exc)})}\n\n"
        return

    # Extract JSON result from accumulated text
    try:
        start = full_text.index("{")
        end = full_text.rindex("}") + 1
        result = json.loads(full_text[start:end])
        if "service_type" in result:
            yield f"event: result\ndata: {json.dumps(result)}\n\n"
    except (ValueError, json.JSONDecodeError):
        pass  # No JSON found — client shows another input turn


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
@router.post("")
async def chat(body: ChatRequest) -> StreamingResponse:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=503, detail="Chatbot unavailable.")
    return StreamingResponse(
        _stream_chat(body.messages, body.locale),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
