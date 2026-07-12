from datetime import datetime, timezone
from typing import Optional

from supabase import Client

from geo.haversine import haversine_miles
from housing.schemas import (
    HousingCreate,
    HousingListResponse,
    HousingResponse,
    HousingSearchResponse,
    HousingWithDistanceResponse,
)


def _lookup_zip_coords(supabase: Client, zip_code: str) -> Optional[tuple[float, float]]:
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


def list_housing(
    supabase: Client,
    page: int = 1,
    page_size: int = 20,
    listing_type: Optional[str] = None,
    state: Optional[str] = None,
) -> HousingListResponse:
    offset = (page - 1) * page_size
    now_iso = datetime.now(timezone.utc).isoformat()

    query = (
        supabase.table("housing")
        .select("*", count="exact")
        .eq("active", True)
        .or_(f"expires_at.is.null,expires_at.gt.{now_iso}")
    )
    if listing_type:
        query = query.eq("listing_type", listing_type)
    if state:
        query = query.eq("state", state.upper())

    result = (
        query
        .order("created_at", desc=True)
        .range(offset, offset + page_size - 1)
        .execute()
    )

    items = [HousingResponse(**row) for row in (result.data or [])]
    total = result.count or 0

    return HousingListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + page_size) < total,
    )


def search_housing_by_zip(
    supabase: Client,
    zip_code: str,
    radius_miles: float,
    page: int = 1,
    page_size: int = 20,
    listing_type: Optional[str] = None,
) -> HousingSearchResponse:
    """Retorna listagens dentro de radius_miles do ZIP informado.

    Listagens sem zip_code são sempre incluídas sem distância (ex: "qualquer região do estado").
    """
    origin = _lookup_zip_coords(supabase, zip_code)
    if origin is None:
        raise ValueError(
            f"ZIP {zip_code!r} não encontrado. "
            "Verifique se o seed de zip_codes foi executado no Supabase."
        )
    origin_lat, origin_lng = origin
    now_iso = datetime.now(timezone.utc).isoformat()

    query = (
        supabase.table("housing")
        .select("*")
        .eq("active", True)
        .or_(f"expires_at.is.null,expires_at.gt.{now_iso}")
    )
    if listing_type:
        query = query.eq("listing_type", listing_type)

    result = query.execute()

    local_items: list[HousingWithDistanceResponse] = []
    no_zip_items: list[HousingWithDistanceResponse] = []

    for row in result.data or []:
        lat = row.get("latitude")
        lng = row.get("longitude")

        if lat is not None and lng is not None:
            dist = haversine_miles(origin_lat, origin_lng, lat, lng)
            if dist > radius_miles:
                continue
            local_items.append(
                HousingWithDistanceResponse(**row, distance_miles=round(dist, 2))
            )
        else:
            no_zip_items.append(HousingWithDistanceResponse(**row, distance_miles=None))

    local_items.sort(key=lambda h: h.distance_miles or 0)
    no_zip_items.sort(key=lambda h: h.created_at, reverse=True)

    sorted_all = local_items + no_zip_items
    total = len(sorted_all)
    offset = (page - 1) * page_size
    page_items = sorted_all[offset: offset + page_size]

    return HousingSearchResponse(
        items=page_items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + page_size) < total,
        search_zip=zip_code,
        radius_miles=radius_miles,
    )


def get_housing(supabase: Client, housing_id: str) -> Optional[HousingResponse]:
    result = (
        supabase.table("housing")
        .select("*")
        .eq("id", housing_id)
        .eq("active", True)
        .maybe_single()
        .execute()
    )
    if not result.data:
        return None
    return HousingResponse(**result.data)


def create_housing(supabase: Client, data: HousingCreate) -> HousingResponse:
    payload = data.model_dump(exclude_none=True)

    for dt_field in ("expires_at", "available_from"):
        if dt_field in payload and payload[dt_field] is not None:
            payload[dt_field] = payload[dt_field].isoformat()
    if "contact_email" in payload and payload["contact_email"] is not None:
        payload["contact_email"] = str(payload["contact_email"])

    if data.zip_code:
        coords = _lookup_zip_coords(supabase, data.zip_code)
        if coords:
            payload["latitude"], payload["longitude"] = coords

    result = supabase.table("housing").insert(payload).execute()
    return HousingResponse(**result.data[0])


def deactivate_housing(supabase: Client, housing_id: str) -> bool:
    result = (
        supabase.table("housing")
        .update({"active": False})
        .eq("id", housing_id)
        .execute()
    )
    return bool(result.data)
