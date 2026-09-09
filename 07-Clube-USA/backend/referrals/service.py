import logging
import re
import secrets
import unicodedata

from fastapi import HTTPException, status
from supabase import Client

logger = logging.getLogger(__name__)

_MAX_SLUG_ATTEMPTS = 5


def _normalize_name(name: str) -> str:
    """'João' -> 'joao'; remove acentos e chars não-alfanuméricos."""
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", ascii_str.lower())


def generate_unique_slug(supabase: Client, first_name: str) -> str:
    """Gera slug único para referral. Formato: '<nome>-<4 chars aleatórios>'."""
    base = _normalize_name(first_name)[:12] or "user"
    for _ in range(_MAX_SLUG_ATTEMPTS):
        # token_urlsafe(3) produz 4 chars base64url — suficiente para ~16M combinações por base
        candidate = f"{base}-{secrets.token_urlsafe(3)}"
        result = (
            supabase.table("profiles")
            .select("id")
            .eq("referral_slug", candidate)
            .execute()
        )
        if not result.data:
            return candidate
    # Fallback extremamente improvável: slug totalmente aleatório
    return secrets.token_urlsafe(8)


def get_referral_stats(supabase: Client, user_id: str) -> dict:
    try:
        profile_result = (
            supabase.table("profiles")
            .select("referral_slug")
            .eq("id", user_id)
            .single()
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado",
        )

    if not profile_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado",
        )

    slug = profile_result.data.get("referral_slug")

    if not slug:
        return {"slug": None, "referral_url": None, "signup_count": 0, "click_count": 0}

    try:
        signups_result = (
            supabase.table("profiles")
            .select("id", count="exact")
            .eq("referred_by_slug", slug)
            .execute()
        )
        signup_count = signups_result.count or 0
    except Exception as e:
        logger.error("referral stats signup count error: %s", type(e).__name__)
        signup_count = 0

    try:
        clicks_result = (
            supabase.table("referral_clicks")
            .select("id", count="exact")
            .eq("slug", slug)
            .execute()
        )
        click_count = clicks_result.count or 0
    except Exception as e:
        logger.error("referral stats click count error: %s", type(e).__name__)
        click_count = 0

    return {
        "slug": slug,
        "referral_url": f"/i/{slug}",
        "signup_count": signup_count,
        "click_count": click_count,
    }


def record_click(supabase: Client, slug: str) -> bool:
    """Registra um clique no link de referral. Retorna False se slug não existe."""
    try:
        result = (
            supabase.table("profiles")
            .select("id")
            .eq("referral_slug", slug)
            .execute()
        )
        if not result.data:
            return False
        supabase.table("referral_clicks").insert({"slug": slug}).execute()
        return True
    except Exception as e:
        logger.error("record_click error: %s", type(e).__name__)
        return False
