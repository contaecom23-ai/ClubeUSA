# api/routers/analytics.py — Fase 0.3: GET /admin/analytics
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from deps import require_admin
from services.analytics_service import get_funnel, get_growth, get_top_referrers, get_engagement

router = APIRouter(prefix="/admin", tags=["analytics"])


@router.get("/analytics")
async def analytics_dashboard(_=Depends(require_admin)):
    """Retorna funil de conversao, crescimento e engajamento para o painel admin."""
    funnel     = get_funnel()
    growth     = get_growth(days=30)
    referrers  = get_top_referrers(limit=10)
    engagement = get_engagement(days=7)
    return {
        **funnel,
        "growth_last_30d": growth,
        "top_referrers":   referrers,
        "engagement":      engagement,
        "generated_at":    datetime.now(timezone.utc).isoformat(),
    }
