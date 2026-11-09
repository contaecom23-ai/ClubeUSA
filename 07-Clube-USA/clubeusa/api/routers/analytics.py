# ============================================================
#  routers/analytics.py — Clube USA
#  Endpoints de analytics básico (admin-only)
#
#  GET /admin/analytics              — overview completo
#  GET /admin/analytics/registrations?days=30   — série temporal cadastros
#  GET /admin/analytics/engagement?days=30      — série temporal cliques
#  GET /admin/analytics/funnel                  — funil de conversão
#  GET /admin/analytics/top-deals?limit=10      — top deals por cliques
#  GET /admin/analytics/distribution            — estados + categorias
#  GET /admin/analytics/referrals               — stats do programa de indicações
# ============================================================

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

log = logging.getLogger("analytics_router")

router = APIRouter(prefix="/admin/analytics", tags=["analytics"])


def _require_admin():
    from deps import require_admin
    return require_admin


@router.get("")
async def analytics_overview(admin=Depends(_require_admin())):
    """Snapshot ampliado com funil, engajamento e referrals."""
    try:
        from services.analytics_service import get_overview
        return get_overview()
    except Exception as e:
        log.error("analytics_overview falhou: %s", e)
        raise HTTPException(status_code=500, detail="Erro ao calcular analytics.")


@router.get("/registrations")
async def analytics_registrations(
    days: Annotated[int, Query(ge=1, le=90)] = 30,
    admin=Depends(_require_admin()),
):
    """Cadastros por dia nos últimos `days` dias (máx. 90)."""
    try:
        from services.analytics_service import get_registrations_by_day
        return {"series": get_registrations_by_day(days), "days": days}
    except Exception as e:
        log.error("analytics_registrations falhou: %s", e)
        raise HTTPException(status_code=500, detail="Erro ao calcular cadastros por dia.")


@router.get("/engagement")
async def analytics_engagement(
    days: Annotated[int, Query(ge=1, le=90)] = 30,
    admin=Depends(_require_admin()),
):
    """Cliques por dia nos últimos `days` dias (máx. 90)."""
    try:
        from services.analytics_service import get_clicks_by_day
        return {"series": get_clicks_by_day(days), "days": days}
    except Exception as e:
        log.error("analytics_engagement falhou: %s", e)
        raise HTTPException(status_code=500, detail="Erro ao calcular engajamento por dia.")


@router.get("/funnel")
async def analytics_funnel(admin=Depends(_require_admin())):
    """Funil de conversão: cadastro → email confirmado → ação → VIP."""
    try:
        from services.analytics_service import get_funnel
        return get_funnel()
    except Exception as e:
        log.error("analytics_funnel falhou: %s", e)
        raise HTTPException(status_code=500, detail="Erro ao calcular funil.")


@router.get("/top-deals")
async def analytics_top_deals(
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    admin=Depends(_require_admin()),
):
    """Top deals ordenados por número de cliques."""
    try:
        from services.analytics_service import get_top_deals
        return {"deals": get_top_deals(limit), "limit": limit}
    except Exception as e:
        log.error("analytics_top_deals falhou: %s", e)
        raise HTTPException(status_code=500, detail="Erro ao calcular top deals.")


@router.get("/distribution")
async def analytics_distribution(admin=Depends(_require_admin())):
    """Distribuição geográfica e por categoria (sem PII)."""
    try:
        from services.analytics_service import get_members_by_state, get_members_by_category
        return {
            "by_state":    get_members_by_state(),
            "by_category": get_members_by_category(),
        }
    except Exception as e:
        log.error("analytics_distribution falhou: %s", e)
        raise HTTPException(status_code=500, detail="Erro ao calcular distribuição.")


@router.get("/referrals")
async def analytics_referrals(admin=Depends(_require_admin())):
    """Estatísticas do programa de indicações."""
    try:
        from services.analytics_service import get_referral_stats
        return get_referral_stats()
    except Exception as e:
        log.error("analytics_referrals falhou: %s", e)
        raise HTTPException(status_code=500, detail="Erro ao calcular referrals.")
