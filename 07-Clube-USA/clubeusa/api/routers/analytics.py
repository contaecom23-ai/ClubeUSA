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
    """
    Serie diaria de novos cadastros e total acumulado.
    Parametro `days` define a janela (1-90, padrao 30).
    """
    from services.analytics_service import get_growth
    return get_growth(days)


@router.get("/funnel")
async def analytics_funnel(_=Depends(require_admin)):
    """
    Funil de conversao:
    cadastrados → email fornecido → email confirmado → ≥1 clique
    """
    from services.analytics_service import get_funnel
    return get_funnel()


@router.get("/engagement")
async def analytics_engagement(
    days: int = Query(default=30, ge=1, le=90),
    _=Depends(require_admin),
):
    """Serie diaria de cliques e top categorias."""
    from services.analytics_service import get_engagement
    return get_engagement(days)


@router.get("/referrals")
async def analytics_referrals(_=Depends(require_admin)):
    """Performance do programa de indicacao."""
    from services.analytics_service import get_referral_stats
    return get_referral_stats()


@router.get("/geographic")
async def analytics_geographic(_=Depends(require_admin)):
    """Distribuicao geografica dos membros por estado."""
    from services.analytics_service import get_geographic_breakdown
    return get_geographic_breakdown()


@router.get("/overview")
async def analytics_overview(_=Depends(require_admin)):
    """
    Snapshot completo: crescimento (7d), funil, engajamento (7d),
    referrals e geografico. Endpoint principal do dashboard.
    """
    from services.analytics_service import get_overview
    return get_overview()
