# clubeusa/api/routers/news.py
import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from deps import get_current_member, require_admin
from supabase import create_client

router = APIRouter(prefix="/news", tags=["news"])

NEWS_CATEGORIES = [
    {"slug": "immigration", "name": "Imigração",          "icon": "📋"},
    {"slug": "politics",    "name": "Política Americana",  "icon": "⚖️"},
    {"slug": "community",   "name": "Comunidade",          "icon": "🤝"},
    {"slug": "brazil",      "name": "Brasil",              "icon": "🇧🇷"},
    {"slug": "economy",     "name": "Economia",            "icon": "💰"},
    {"slug": "general",     "name": "Geral",               "icon": "📰"},
]


def is_relevant(score: int) -> bool:
    return score >= 40


def _sb():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


@router.get("/categories")
async def list_categories():
    return {"categories": NEWS_CATEGORIES}


@router.get("")
async def list_news(
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    member: dict = Depends(get_current_member),
):
    sb = _sb()
    limit = min(limit, 50)
    query = (
        sb.table("news_articles")
        .select("id,title_pt,summary_pt,category,relevance_score,published_at,url,image_url,source_id")
        .eq("status", "published")
        .order("published_at", desc=True)
        .limit(limit)
        .offset(offset)
    )
    if category:
        query = query.eq("category", category)

    result = query.execute()
    return {"articles": result.data or [], "offset": offset, "limit": limit}


@router.get("/{article_id}")
async def get_article(article_id: str, member: dict = Depends(get_current_member)):
    sb = _sb()
    result = sb.table("news_articles").select("*").eq("id", article_id).eq("status", "published").execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Artigo não encontrado.")

    try:
        sb.table("news_reads").insert({
            "member_id": member["sub"],
            "article_id": article_id,
        }).execute()
        sb.rpc("increment_points", {"p_member_id": member["sub"], "p_points": 5}).execute()
    except Exception:
        pass  # UNIQUE constraint — já leu antes, ignora

    return result.data[0]


# ── Admin ──────────────────────────────────────────────────────

@router.get("/admin/pending", dependencies=[Depends(require_admin)])
async def admin_pending_news(limit: int = 50):
    sb = _sb()
    result = (
        sb.table("news_articles")
        .select("id,title_original,title_pt,summary_pt,category,relevance_score,url,source_id,created_at")
        .eq("status", "ready_for_review")
        .order("relevance_score", desc=True)
        .limit(limit)
        .execute()
    )
    return {"articles": result.data or []}


@router.post("/admin/{article_id}/approve", dependencies=[Depends(require_admin)])
async def admin_approve_article(article_id: str):
    from datetime import datetime, timezone
    sb = _sb()
    result = sb.table("news_articles").update({
        "status": "published",
        "published_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", article_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Artigo não encontrado.")
    return {"ok": True}


@router.post("/admin/{article_id}/reject", dependencies=[Depends(require_admin)])
async def admin_reject_article(article_id: str):
    sb = _sb()
    result = sb.table("news_articles").update({"status": "rejected"}).eq("id", article_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Artigo não encontrado.")
    return {"ok": True}
