from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from supabase import Client

from config import settings
from db.supabase import get_supabase
from promotions.schemas import (
    PromotionCreate,
    PromotionListResponse,
    PromotionResponse,
    PromotionSearchResponse,
)
from promotions.service import (
    create_promotion,
    deactivate_promotion,
    get_promotion,
    list_promotions,
    search_promotions_by_zip,
)

router = APIRouter(tags=["promotions"])
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
    "/promotions/search",
    response_model=PromotionSearchResponse,
    summary="Busca promoções por ZIP + raio (público)",
)
def search_promos(
    zip: str = Query(..., pattern=r"^\d{5}$", description="ZIP code de 5 dígitos"),
    radius: float = Query(5.0, ge=0.1, le=50.0, description="Raio em milhas (padrão 5)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supabase: Client = Depends(get_supabase),
) -> PromotionSearchResponse:
    try:
        return search_promotions_by_zip(
            supabase, zip_code=zip, radius_miles=radius, page=page, page_size=page_size
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )


@router.get(
    "/promotions",
    response_model=PromotionListResponse,
    summary="Lista promoções ativas (público). Use ?zip=XXXXX&radius=5 para filtrar por proximidade.",
)
def list_promos(
    page: int = Query(1, ge=1, description="Página (começa em 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por página (máx 100)"),
    zip: str = Query(None, pattern=r"^\d{5}$", description="ZIP code para filtro geográfico"),
    radius: float = Query(5.0, ge=0.1, le=50.0, description="Raio em milhas (padrão 5)"),
    supabase: Client = Depends(get_supabase),
):
    if zip:
        try:
            return search_promotions_by_zip(
                supabase, zip_code=zip, radius_miles=radius, page=page, page_size=page_size
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            )
    return list_promotions(supabase, page=page, page_size=page_size)


@router.get(
    "/promotions/{promotion_id}",
    response_model=PromotionResponse,
    summary="Detalhes de uma promoção (público)",
)
def get_promo(
    promotion_id: str,
    supabase: Client = Depends(get_supabase),
) -> PromotionResponse:
    promo = get_promotion(supabase, promotion_id)
    if promo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Promoção não encontrada",
        )
    return promo


@admin_router.post(
    "/admin/promotions",
    response_model=PromotionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria promoção (admin)",
)
def create_promo(
    data: PromotionCreate,
    _: None = Depends(_require_admin),
    supabase: Client = Depends(get_supabase),
) -> PromotionResponse:
    return create_promotion(supabase, data)


@admin_router.delete(
    "/admin/promotions/{promotion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desativa promoção (admin)",
)
def deactivate_promo(
    promotion_id: str,
    _: None = Depends(_require_admin),
    supabase: Client = Depends(get_supabase),
) -> None:
    found = deactivate_promotion(supabase, promotion_id)
    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Promoção não encontrada",
        )
