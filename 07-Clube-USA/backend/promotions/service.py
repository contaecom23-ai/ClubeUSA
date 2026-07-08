from datetime import datetime, timezone
from typing import Optional
from supabase import Client

from geo.haversine import haversine_miles
from promotions.schemas import (
    PromotionCreate,
    PromotionListResponse,
    PromotionResponse,
    PromotionSearchResponse,
    PromotionWithDistanceResponse,
)


def _lookup_zip_coords(supabase: Client, zip_code: str) -> Optional[tuple[float, float]]:
    """Retorna (latitude, longitude) para um ZIP code, ou None se não encontrado."""
    result = (
        supabase.table("zip_codes")
        .select("latitude,longitude")
        .eq("zip", zip_code)
        .maybe_single()
        .execute()
    )
    if not result.data:
        return None
    return result.data["latitude"], result.data["longitude"]


def list_promotions(
    supabase: Client,
    page: int = 1,
    page_size: int = 20,
) -> PromotionListResponse:
    offset = (page - 1) * page_size
    now_iso = datetime.now(timezone.utc).isoformat()

    result = (
        supabase.table("promotions")
        .select("*", count="exact")
        .eq("active", True)
        .or_(f"expires_at.is.null,expires_at.gt.{now_iso}")
        .order("created_at", desc=True)
        .range(offset, offset + page_size - 1)
        .execute()
    )

    items = [PromotionResponse(**row) for row in (result.data or [])]
    total = result.count or 0

    return PromotionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + page_size) < total,
    )


def search_promotions_by_zip(
    supabase: Client,
    zip_code: str,
    radius_miles: float,
    page: int = 1,
    page_size: int = 20,
) -> PromotionSearchResponse:
    """
    Retorna promoções dentro de `radius_miles` do centro do ZIP informado.

    Estratégia MVP (até ~10k promoções): filtragem Haversine em Python.
    - Promoções sem zip_code (nacionais): sempre inclusas, sem distância.
    - Promoções com zip_code mas sem coordenadas no lookup: inclusas como nacionais.
    - Promoções com coordenadas: filtradas por distância; ordenadas pela mais próxima.

    Migrar para PostGIS (extension do Supabase) quando promos ativas > 10k.
    """
    origin = _lookup_zip_coords(supabase, zip_code)
    if origin is None:
        raise ValueError(
            f"ZIP {zip_code!r} não encontrado. "
            "Verifique se o seed de zip_codes foi executado no Supabase."
        )
    origin_lat, origin_lng = origin
    now_iso = datetime.now(timezone.utc).isoformat()

    # Busca todas as promos ativas não-expiradas de uma vez.
    # Aceitável para MVP (<10k linhas); revisar ao escalar.
    result = (
        supabase.table("promotions")
        .select("*")
        .eq("active", True)
        .or_(f"expires_at.is.null,expires_at.gt.{now_iso}")
        .execute()
    )

    local_items: list[PromotionWithDistanceResponse] = []
    national_items: list[PromotionWithDistanceResponse] = []

    for row in result.data or []:
        promo_lat = row.get("latitude")
        promo_lng = row.get("longitude")

        if promo_lat is not None and promo_lng is not None:
            dist = haversine_miles(origin_lat, origin_lng, promo_lat, promo_lng)
            if dist > radius_miles:
                continue
            local_items.append(
                PromotionWithDistanceResponse(**row, distance_miles=round(dist, 2))
            )
        else:
            national_items.append(PromotionWithDistanceResponse(**row, distance_miles=None))

    local_items.sort(key=lambda p: p.distance_miles or 0)
    national_items.sort(key=lambda p: p.created_at, reverse=True)

    sorted_all = local_items + national_items
    total = len(sorted_all)
    offset = (page - 1) * page_size
    page_items = sorted_all[offset : offset + page_size]

    return PromotionSearchResponse(
        items=page_items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + page_size) < total,
        search_zip=zip_code,
        radius_miles=radius_miles,
    )


def get_promotion(supabase: Client, promotion_id: str) -> Optional[PromotionResponse]:
    result = (
        supabase.table("promotions")
        .select("*")
        .eq("id", promotion_id)
        .eq("active", True)
        .maybe_single()
        .execute()
    )
    if not result.data:
        return None
    return PromotionResponse(**result.data)


def create_promotion(supabase: Client, data: PromotionCreate) -> PromotionResponse:
    payload = data.model_dump(exclude_none=True)
    if "expires_at" in payload and payload["expires_at"] is not None:
        payload["expires_at"] = payload["expires_at"].isoformat()

    # Auto-preencher lat/lng a partir do zip_code, se disponível no lookup.
    if data.zip_code:
        coords = _lookup_zip_coords(supabase, data.zip_code)
        if coords:
            payload["latitude"], payload["longitude"] = coords

    result = supabase.table("promotions").insert(payload).execute()
    return PromotionResponse(**result.data[0])


def deactivate_promotion(supabase: Client, promotion_id: str) -> bool:
    result = (
        supabase.table("promotions")
        .update({"active": False})
        .eq("id", promotion_id)
        .execute()
    )
    return bool(result.data)
