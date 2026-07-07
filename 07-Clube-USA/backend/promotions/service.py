from datetime import datetime, timezone
from typing import Optional
from supabase import Client

from promotions.schemas import PromotionCreate, PromotionListResponse, PromotionResponse


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
