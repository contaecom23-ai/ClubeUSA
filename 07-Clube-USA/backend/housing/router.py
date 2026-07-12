from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from supabase import Client

from config import settings
from db.supabase import get_supabase
from housing.schemas import (
    HousingCreate,
    HousingListResponse,
    HousingResponse,
    HousingSearchResponse,
)
from housing.service import (
    create_housing,
    deactivate_housing,
    get_housing,
    list_housing,
    search_housing_by_zip,
)

router = APIRouter(tags=["housing"])
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
    "/housing/search",
    response_model=HousingSearchResponse,
    summary="Busca moradia por ZIP + raio (público)",
)
def search_housing(
    zip: str = Query(..., pattern=r"^\d{5}$", description="ZIP code de 5 dígitos"),
    radius: float = Query(10.0, ge=0.1, le=50.0, description="Raio em milhas (padrão 10)"),
    listing_type: str = Query(None, description="Filtrar por tipo: quarto_disponivel, precisa_quarto, casa_disponivel"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supabase: Client = Depends(get_supabase),
) -> HousingSearchResponse:
    try:
        return search_housing_by_zip(
            supabase,
            zip_code=zip,
            radius_miles=radius,
            page=page,
            page_size=page_size,
            listing_type=listing_type,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )


@router.get(
    "/housing",
    response_model=HousingListResponse,
    summary="Lista anúncios de moradia ativos (público). Use ?zip=XXXXX&radius=10 para proximidade.",
)
def list_housing_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    zip: str = Query(None, pattern=r"^\d{5}$", description="ZIP code para busca geográfica"),
    radius: float = Query(10.0, ge=0.1, le=50.0),
    listing_type: str = Query(None),
    state: str = Query(None, description="Filtrar por estado (sigla, ex: FL)"),
    supabase: Client = Depends(get_supabase),
):
    if zip:
        try:
            return search_housing_by_zip(
                supabase,
                zip_code=zip,
                radius_miles=radius,
                page=page,
                page_size=page_size,
                listing_type=listing_type,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            )
    return list_housing(supabase, page=page, page_size=page_size, listing_type=listing_type, state=state)


@router.get(
    "/housing/{housing_id}",
    response_model=HousingResponse,
    summary="Detalhes de um anúncio de moradia (público)",
)
def get_housing_endpoint(
    housing_id: str,
    supabase: Client = Depends(get_supabase),
) -> HousingResponse:
    listing = get_housing(supabase, housing_id)
    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anúncio não encontrado",
        )
    return listing


@admin_router.post(
    "/admin/housing",
    response_model=HousingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria anúncio de moradia (admin)",
)
def create_housing_endpoint(
    data: HousingCreate,
    _: None = Depends(_require_admin),
    supabase: Client = Depends(get_supabase),
) -> HousingResponse:
    return create_housing(supabase, data)


@admin_router.delete(
    "/admin/housing/{housing_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desativa anúncio de moradia (admin)",
)
def deactivate_housing_endpoint(
    housing_id: str,
    _: None = Depends(_require_admin),
    supabase: Client = Depends(get_supabase),
) -> None:
    found = deactivate_housing(supabase, housing_id)
    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anúncio não encontrado",
        )
