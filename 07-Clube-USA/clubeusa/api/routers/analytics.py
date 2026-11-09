# ============================================================
#  api/routers/analytics.py — Clube USA
#  Endpoints de analytics (admin-only) — Fase 0.3
# ============================================================

from fastapi import APIRouter, Depends, Query
from deps import require_admin

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/growth")
async def analytics_growth(
    days: int = Query(default=30, ge=1, le=90),
    _=Depends(require_admin),
):
    """Serie diaria de novos cadastros — [{date, registrations}]. Janela: 1-90 dias."""
    from services.analytics_service import get_growth
    return get_growth(days)


@router.get("/funnel")
async def analytics_funnel(_=Depends(require_admin)):
    """
    Funil de conversao:
    cadastros → logins → email confirmado → 1° clique → VIP.
    """
    from services.analytics_service import get_funnel
    return get_funnel()


@router.get("/engagement")
async def analytics_engagement(
    days: int = Query(default=7, ge=1, le=90),
    _=Depends(require_admin),
):
    """Cliques por periodo e top 5 categorias."""
    from services.analytics_service import get_engagement
    return get_engagement(days)


@router.get("/referrals")
async def analytics_referrals(_=Depends(require_admin)):
    """Performance agregada do programa de indicacao."""
    from services.analytics_service import get_referral_stats
    return get_referral_stats()


@router.get("/top-referrers")
async def analytics_top_referrers(
    limit: int = Query(default=10, ge=1, le=50),
    _=Depends(require_admin),
):
    """Top indicadores por numero de indicacoes confirmadas."""
    from services.analytics_service import get_top_referrers
    return get_top_referrers(limit)


@router.get("/geographic")
async def analytics_geographic(_=Depends(require_admin)):
    """Distribuicao geografica dos membros por estado (top 10)."""
    from services.analytics_service import get_geographic_breakdown
    return get_geographic_breakdown()


@router.get("/overview")
async def analytics_overview(_=Depends(require_admin)):
    """
    Snapshot completo: funil, crescimento 30d, top referrers,
    engajamento 7d e distribuicao geografica.
    """
    from services.analytics_service import get_overview
    return get_overview()
