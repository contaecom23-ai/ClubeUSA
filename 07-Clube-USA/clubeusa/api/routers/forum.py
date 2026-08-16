# clubeusa/api/routers/forum.py
import os
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from deps import get_current_member, require_admin
from supabase import create_client

router = APIRouter(prefix="/forum", tags=["forum"])
log = logging.getLogger("forum")

POST_POINTS  = 20
REPLY_POINTS = 10

AI_SYSTEM_PROMPT = (
    "Você é o Assistente Clube USA, especializado em ajudar imigrantes brasileiros nos EUA. "
    "Responda em português, seja direto e prático. Temas: imigração, vistos, documentos, "
    "emprego, moradia, saúde, finanças, compras nos EUA. "
    "Nunca dê conselhos jurídicos formais — sugira consultar um advogado para casos complexos. "
    "Seja acolhedor e empático — o imigrante enfrenta desafios reais."
)


def handle_vote_conflict() -> dict:
    return {"ok": False, "reason": "already_voted"}


def _sb():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def _sanitize_for_prompt(text: str, max_len: int = 500) -> str:
    """Remove patterns that could be used for prompt injection."""
    lines = text[:max_len].splitlines()
    clean = []
    for line in lines:
        stripped = line.strip().lower()
        if any(stripped.startswith(p) for p in ("ignore", "system:", "assistant:", "[inst", "<<sys")):
            continue
        clean.append(line)
    return "\n".join(clean)


def _groq_reply(question_title: str, question_body: str) -> str:
    """Gera resposta da IA via Groq para uma pergunta do fórum."""
    import requests
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        return ""
    safe_title = _sanitize_for_prompt(question_title, max_len=200)
    safe_body  = _sanitize_for_prompt(question_body,  max_len=500)
    prompt = (
        f"Um membro do Clube USA fez esta pergunta no fórum:\n\n"
        f"Título: {safe_title}\n\nDetalhes: {safe_body}\n\n"
        f"Responda de forma direta, prática e acolhedora. Máximo 3 parágrafos."
    )
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.1-70b-versatile",
                "messages": [
                    {"role": "system", "content": AI_SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
                "max_tokens": 400,
                "temperature": 0.6,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        log.warning(f"Groq forum reply error: {e}")
    return ""


# ── Schemas ────────────────────────────────────────────────────

class PostCreate(BaseModel):
    category_id: str
    title: str
    body: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if len(v.strip()) < 10:
            raise ValueError("Título deve ter pelo menos 10 caracteres.")
        return v.strip()[:200]

    @field_validator("body")
    @classmethod
    def validate_body(cls, v):
        if len(v.strip()) < 20:
            raise ValueError("Conteúdo deve ter pelo menos 20 caracteres.")
        return v.strip()[:5000]


class ReplyCreate(BaseModel):
    body: str

    @field_validator("body")
    @classmethod
    def validate_body(cls, v):
        if len(v.strip()) < 5:
            raise ValueError("Resposta muito curta.")
        return v.strip()[:3000]


# ── Endpoints ──────────────────────────────────────────────────

@router.get("/categories")
async def list_forum_categories():
    sb = _sb()
    result = (
        sb.table("forum_categories")
        .select("id,name,slug,description,icon,sort_order")
        .eq("active", True)
        .order("sort_order")
        .execute()
    )
    return {"categories": result.data or []}


@router.get("/posts")
async def list_posts(
    category_slug: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    member: dict = Depends(get_current_member),
):
    sb = _sb()
    limit = min(limit, 50)
    query = (
        sb.table("forum_posts")
        .select("id,title,vote_count,reply_count,created_at,category_id")
        .eq("is_deleted", False)
        .order("created_at", desc=True)
        .limit(limit)
        .offset(offset)
    )
    if category_slug:
        cat = sb.table("forum_categories").select("id").eq("slug", category_slug).execute()
        if cat.data:
            query = query.eq("category_id", cat.data[0]["id"])

    result = query.execute()
    return {"posts": result.data or []}


@router.post("/posts", status_code=201)
async def create_post(body: PostCreate, member: dict = Depends(get_current_member)):
    sb = _sb()

    cat = sb.table("forum_categories").select("id").eq("id", body.category_id).eq("active", True).execute()
    if not cat.data:
        raise HTTPException(status_code=400, detail="Categoria inválida.")

    result = sb.table("forum_posts").insert({
        "member_id":   member["sub"],
        "category_id": body.category_id,
        "title":       body.title,
        "body":        body.body,
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Erro ao criar post.")

    post = result.data[0]
    post_id = post["id"]

    sb.rpc("increment_points", {"p_member_id": member["sub"], "p_points": POST_POINTS}).execute()

    import threading
    def ai_reply():
        try:
            ai_text = _groq_reply(body.title, body.body)
            if ai_text:
                sb2 = _sb()
                sb2.table("forum_replies").insert({
                    "post_id":  post_id,
                    "body":     ai_text,
                    "is_ai":    True,
                }).execute()
                sb2.table("forum_posts").update({"reply_count": 1}).eq("id", post_id).execute()
        except Exception as e:
            log.warning(f"AI reply failed for post {post_id}: {e}")

    threading.Thread(target=ai_reply, daemon=True).start()

    return post


@router.get("/posts/{post_id}")
async def get_post(post_id: str, member: dict = Depends(get_current_member)):
    sb = _sb()
    post = sb.table("forum_posts").select("*").eq("id", post_id).eq("is_deleted", False).execute()
    if not post.data:
        raise HTTPException(status_code=404, detail="Post não encontrado.")

    replies = (
        sb.table("forum_replies")
        .select("id,body,is_ai,vote_count,created_at,member_id")
        .eq("post_id", post_id)
        .eq("is_deleted", False)
        .order("is_ai", desc=True)
        .order("vote_count", desc=True)
        .execute()
    )
    return {"post": post.data[0], "replies": replies.data or []}


@router.post("/posts/{post_id}/reply", status_code=201)
async def reply_post(post_id: str, body: ReplyCreate, member: dict = Depends(get_current_member)):
    sb = _sb()
    post = sb.table("forum_posts").select("id,reply_count").eq("id", post_id).eq("is_deleted", False).execute()
    if not post.data:
        raise HTTPException(status_code=404, detail="Post não encontrado.")

    result = sb.table("forum_replies").insert({
        "post_id":   post_id,
        "member_id": member["sub"],
        "body":      body.body,
        "is_ai":     False,
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Erro ao criar resposta.")

    new_count = (post.data[0].get("reply_count") or 0) + 1
    sb.table("forum_posts").update({"reply_count": new_count}).eq("id", post_id).execute()

    sb.rpc("increment_points", {"p_member_id": member["sub"], "p_points": REPLY_POINTS}).execute()

    return result.data[0]


@router.post("/posts/{post_id}/vote")
async def vote_post(post_id: str, member: dict = Depends(get_current_member)):
    sb = _sb()
    try:
        sb.table("forum_votes").insert({
            "member_id":   member["sub"],
            "target_type": "post",
            "target_id":   post_id,
        }).execute()
        post = sb.table("forum_posts").select("vote_count").eq("id", post_id).execute()
        if post.data:
            sb.table("forum_posts").update({"vote_count": (post.data[0]["vote_count"] or 0) + 1}).eq("id", post_id).execute()
        return {"ok": True}
    except Exception:
        return handle_vote_conflict()


@router.delete("/admin/posts/{post_id}", dependencies=[Depends(require_admin)])
async def admin_delete_post(post_id: str):
    sb = _sb()
    sb.table("forum_posts").update({"is_deleted": True}).eq("id", post_id).execute()
    return {"ok": True}
