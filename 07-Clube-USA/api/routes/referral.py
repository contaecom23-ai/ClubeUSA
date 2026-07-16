from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from supabase import Client

from config import settings
from deps import get_current_user_id, get_db
from models import ReferralStats
from security import generate_referral_code

# Redirect de short-link — sem prefixo /api (montado separadamente no main.py)
redirect_router = APIRouter()

# Rotas de API protegidas
router = APIRouter(prefix="/referral", tags=["referral"])


@redirect_router.get("/i/{code}", include_in_schema=False)
async def referral_redirect(code: str) -> RedirectResponse:
    """Redireciona link de indicação para a página de cadastro."""
    safe_code = quote(code, safe="")
    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/register.html?ref={safe_code}",
        status_code=302,
    )


@router.get("/stats", response_model=ReferralStats)
async def get_referral_stats(
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[Client, Depends(get_db)],
) -> ReferralStats:
    """Retorna código de indicação e estatísticas do usuário logado."""
    user_result = (
        db.table("users").select("referral_code").eq("id", user_id).execute()
    )
    if not user_result.data:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    referral_code = user_result.data[0].get("referral_code")

    # Geração lazy: usuários cadastrados antes da Fase 0.2 não têm código
    if not referral_code:
        for _ in range(10):
            candidate = generate_referral_code()
            collision = (
                db.table("users").select("id").eq("referral_code", candidate).execute()
            )
            if not collision.data:
                referral_code = candidate
                db.table("users").update(
                    {"referral_code": referral_code}
                ).eq("id", user_id).execute()
                break

    referred_result = (
        db.table("users").select("id").eq("referred_by_user_id", user_id).execute()
    )
    referral_count = len(referred_result.data) if referred_result.data else 0

    return ReferralStats(
        referral_code=referral_code,
        referral_count=referral_count,
        referral_url=(
            f"{settings.FRONTEND_URL}/i/{referral_code}" if referral_code else None
        ),
    )
