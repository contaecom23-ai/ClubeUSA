from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from analytics import emit_event
from deps import get_db
from models import MessageResponse, PromotionCategory, PromotionListResponse, PromotionResponse

router = APIRouter(prefix="/promotions", tags=["promotions"])

_SELECT_FIELDS = (
    "id, title, description, url, image_url, category, zip_code, state,"
    " expires_at, is_featured, is_active, created_at"
)


def _not_expired(p: dict) -> bool:
    raw = p.get("expires_at")
    if not raw:
        return True
    try:
        exp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return exp > datetime.now(timezone.utc)
    except Exception:
        return True


@router.get("", response_model=PromotionListResponse, summary="Lista promoções ativas (pública)")
async def list_promotions(
    db: Annotated[Client, Depends(get_db)],
    category: PromotionCategory | None = None,
    state: str | None = None,
    zip_code: str | None = None,
) -> PromotionListResponse:
    result = (
        db.table("promotions")
        .select(_SELECT_FIELDS)
        .eq("is_active", True)
        .order("is_featured", desc=True)
        .order("created_at", desc=True)
        .limit(500)
        .execute()
    )
    items = [p for p in (result.data or []) if _not_expired(p)]

    if category:
        items = [p for p in items if p.get("category") == category.value]
    if state:
        norm = state.upper()
        items = [p for p in items if not p.get("state") or p.get("state") == norm]
    if zip_code:
        items = [p for p in items if not p.get("zip_code") or p.get("zip_code") == zip_code]

    responses = [PromotionResponse.from_db(p) for p in items]
    return PromotionListResponse(items=responses, total=len(responses))


@router.get("/{promotion_id}", response_model=PromotionResponse, summary="Detalhes de uma promoção (pública)")
async def get_promotion(
    promotion_id: str,
    db: Annotated[Client, Depends(get_db)],
) -> PromotionResponse:
    result = (
        db.table("promotions")
        .select(_SELECT_FIELDS)
        .eq("id", promotion_id)
        .eq("is_active", True)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Promoção não encontrada")
    return PromotionResponse.from_db(result.data[0])


@router.post("/{promotion_id}/click", response_model=MessageResponse, summary="Registra clique em promoção (pública)")
async def track_click(
    promotion_id: str,
    db: Annotated[Client, Depends(get_db)],
) -> MessageResponse:
    result = (
        db.table("promotions")
        .select("id")
        .eq("id", promotion_id)
        .eq("is_active", True)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Promoção não encontrada")
    emit_event(db, "promotion_click", metadata={"promotion_id": promotion_id})
    return MessageResponse(message="ok")
