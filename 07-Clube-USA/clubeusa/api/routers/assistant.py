# clubeusa/api/routers/assistant.py
import os
import logging
import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from deps import get_current_member
from supabase import create_client

router = APIRouter(prefix="/assistant", tags=["assistant"])
log = logging.getLogger("assistant")

MAX_HISTORY_MESSAGES = 10

AI_SYSTEM_PROMPT = (
    "Você é o Assistente Clube USA, especializado em ajudar imigrantes brasileiros nos EUA. "
    "Responda em português (ou espanhol se o usuário escrever em espanhol). "
    "Seja direto, prático e acolhedor. "
    "Temas que você domina: imigração, vistos, green card, documentos, SSN, ITIN, "
    "emprego, currículo, direitos trabalhistas, moradia, aluguel, saúde, plano de saúde, "
    "finanças, conta bancária, crédito, impostos, compras nos EUA, vida cotidiana. "
    "IMPORTANTE: Nunca dê conselhos jurídicos formais. Para casos complexos de imigração, "
    "sempre sugira consultar um advogado de imigração. "
    "Seja empático — o imigrante enfrenta desafios reais e merece respeito."
)


def _sb():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def _get_or_create_session(member_id: str) -> str:
    """Retorna session_id ativa do membro (ou cria uma nova)."""
    sb = _sb()
    result = (
        sb.table("ai_sessions")
        .select("id")
        .eq("member_id", member_id)
        .order("updated_at", desc=True)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]["id"]

    new_session = sb.table("ai_sessions").insert({"member_id": member_id}).execute()
    return new_session.data[0]["id"]


def _call_groq(messages: list) -> str:
    """Chama Groq API com histórico da conversa."""
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        return "Assistente temporariamente indisponível. Tente novamente em instantes."
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.1-70b-versatile",
                "messages": [{"role": "system", "content": AI_SYSTEM_PROMPT}] + messages,
                "max_tokens": 500,
                "temperature": 0.7,
            },
            timeout=20,
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
        log.error(f"Groq error {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        log.error(f"Groq exception: {e}")
    return "Não consegui processar sua mensagem agora. Tente novamente."


# ── Schemas ────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    content: str


# ── Endpoints ──────────────────────────────────────────────────

@router.post("/chat")
async def chat(body: ChatMessage, member: dict = Depends(get_current_member)):
    sb = _sb()
    member_id = member["sub"]
    user_text = body.content.strip()[:2000]

    if not user_text:
        raise HTTPException(status_code=422, detail="Mensagem vazia.")

    session_id = _get_or_create_session(member_id)

    history = (
        sb.table("ai_messages")
        .select("role,content")
        .eq("session_id", session_id)
        .order("created_at", desc=True)
        .limit(MAX_HISTORY_MESSAGES)
        .execute()
    )
    messages = list(reversed(history.data or []))
    messages.append({"role": "user", "content": user_text})

    sb.table("ai_messages").insert({"session_id": session_id, "role": "user", "content": user_text}).execute()

    ai_response = _call_groq(messages)

    sb.table("ai_messages").insert({"session_id": session_id, "role": "assistant", "content": ai_response}).execute()

    from datetime import datetime, timezone
    sb.table("ai_sessions").update({"updated_at": datetime.now(timezone.utc).isoformat()}).eq("id", session_id).execute()

    return {"response": ai_response, "session_id": session_id}


@router.get("/history")
async def get_history(member: dict = Depends(get_current_member)):
    sb = _sb()
    session_id = _get_or_create_session(member["sub"])
    result = (
        sb.table("ai_messages")
        .select("role,content,created_at")
        .eq("session_id", session_id)
        .order("created_at")
        .limit(MAX_HISTORY_MESSAGES)
        .execute()
    )
    return {"messages": result.data or [], "session_id": session_id}


@router.delete("/history")
async def clear_history(member: dict = Depends(get_current_member)):
    """Apaga histórico e cria nova sessão."""
    sb = _sb()
    sb.table("ai_sessions").delete().eq("member_id", member["sub"]).execute()
    new_session = sb.table("ai_sessions").insert({"member_id": member["sub"]}).execute()
    return {"ok": True, "session_id": new_session.data[0]["id"]}
