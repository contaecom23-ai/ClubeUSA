import logging

from fastapi import APIRouter, Depends, Header, HTTPException, status
from supabase import Client

from analytics.schemas import AnalyticsSummary
from analytics.service import get_summary
from config import settings
from db.supabase import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter(tags=["admin"])


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
    "/admin/analytics/summary",
    response_model=AnalyticsSummary,
    summary="Resumo de analytics (admin)",
)
def analytics_summary(
    _: None = Depends(_require_admin),
    supabase: Client = Depends(get_supabase),
) -> AnalyticsSummary:
    return get_summary(supabase)
