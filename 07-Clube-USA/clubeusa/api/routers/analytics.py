"""
routers/analytics.py — Fase 0.3 + 0.4

GET  /member/validation-status   — status de cadastro válido (membro autenticado)
GET  /admin/analytics            — painel de métricas (admin)
"""

from fastapi import APIRouter, Depends, HTTPException
from deps import get_current_member, require_admin

router = APIRouter()


@router.get("/member/validation-status")
async def validation_status(member: dict = Depends(get_current_member)):
    """
    Retorna se o cadastro do membro é considerado 'válido' (Fase 0.4).
    Critério: email confirmado (se fornecido) + ≥1 ação real.
    """
    from services.analytics_service import get_validation_status
    return get_validation_status(member["sub"])


@router.get("/admin/analytics")
async def admin_analytics(_=Depends(require_admin)):
    """Métricas básicas de crescimento e engajamento para o painel admin."""
    from services.analytics_service import get_admin_stats
    try:
        return get_admin_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar métricas: {e}")
