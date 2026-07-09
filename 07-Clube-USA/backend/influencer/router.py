from fastapi import APIRouter, Depends, Header, HTTPException, status
from supabase import Client

from config import settings
from core.deps import get_current_user_id
from db.supabase import get_supabase
from influencer.schemas import InfluencerStats, LeaderboardResponse
from influencer.service import get_influencer_stats, get_leaderboard

router = APIRouter(prefix="/influencer", tags=["influencer"])
admin_router = APIRouter(tags=["admin"])


def _require_admin(x_admin_key: str = Header(..., alias="X-Admin-Key")) -> None:
    if not settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin não configurado — defina ADMIN_API_KEY no servidor.",
        )
    if x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin key inválida.",
        )


@router.get(
    "/me",
    response_model=InfluencerStats,
    summary="Meu dashboard de influenciador",
)
def my_influencer_stats(
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase),
) -> InfluencerStats:
    return get_influencer_stats(
        supabase,
        user_id,
        payment_per_referral_cents=settings.INFLUENCER_PAYMENT_PER_REFERRAL_CENTS,
        monthly_cap_cents=settings.INFLUENCER_MONTHLY_CAP_CENTS,
    )


@admin_router.get(
    "/admin/influencer/leaderboard",
    response_model=LeaderboardResponse,
    summary="Ranking de influenciadores (admin)",
)
def influencer_leaderboard(
    _: None = Depends(_require_admin),
    supabase: Client = Depends(get_supabase),
) -> LeaderboardResponse:
    return get_leaderboard(supabase)
