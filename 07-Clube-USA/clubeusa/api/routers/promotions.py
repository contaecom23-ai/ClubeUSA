# api/routers/promotions.py — Fase 1.1 (Promoções/Achados, carro-chefe)
#
# Membros submetem promoções locais (mercado, gasolina, restaurante, etc.).
# Admin aprova/rejeita. Comunidade vê e upvota as aprovadas.
#
# Endpoints:
#   POST   /promotions              — submeter promoção
#   GET    /promotions              — listar aprovadas
#   GET    /promotions/mine         — minhas promoções
#   GET    /promotions/{id}         — detalhe
#   POST   /promotions/{id}/upvote  — upvote
#   DELETE /promotions/{id}         — cancelar pendente

import os
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from supabase import create_client

from deps import get_current_member

log = logging.getLogger("api")
router = APIRouter(prefix="/promotions", tags=["promotions"])

_VALID_CATEGORIES = {"grocery", "gas", "restaurant", "services", "electronics", "fashion", "other"}
_DAILY_SUBMIT_LIMIT = 5


def _sb():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


# ============================================================
#  SCHEMA
# ============================================================

class PromotionSubmit(BaseModel):
    title:       str
    description: Optional[str] = None
    store_name:  str
    url:         Optional[str] = None
    price_now:   Optional[float] = None
    price_was:   Optional[float] = None
    zip_code:    Optional[str] = None
    state:       Optional[str] = None
    category:    str = "other"
    expires_at:  Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        v = v.strip()
        if not (5 <= len(v) <= 200):
            raise ValueError("Título deve ter entre 5 e 200 caracteres.")
        return v

    @field_validator("store_name")
    @classmethod
    def validate_store(cls, v):
        v = v.strip()
        if not (2 <= len(v) <= 100):
            raise ValueError("Nome da loja deve ter entre 2 e 100 caracteres.")
        return v

    @field_validator("description")
    @classmethod
    def validate_desc(cls, v):
        if v is None:
            return v
        v = v.strip()
        if len(v) > 1000:
            raise ValueError("Descrição deve ter no máximo 1000 caracteres.")
        return v or None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v):
        if v not in _VALID_CATEGORIES:
            raise ValueError(f"Categoria inválida. Use: {', '.join(sorted(_VALID_CATEGORIES))}")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v):
        import re
        if v is None:
            return v
        v = v.strip()
        if not re.match(r'^\d{5}(-\d{4})?$', v):
            raise ValueError("ZIP inválido. Use formato: 12345 ou 12345-6789.")
        return v

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        if v is None:
            return v
        v = v.strip()
        if len(v) > 500:
            raise ValueError("URL muito longa (máx 500 chars).")
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL deve começar com http:// ou https://")
        return v

    @field_validator("price_now", "price_was")
    @classmethod
    def validate_price(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Preço deve ser maior que zero.")
        return v

    @field_validator("expires_at")
    @classmethod
    def validate_expiry(cls, v):
        if v is not None and v.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
            raise ValueError("Data de validade deve ser no futuro.")
        return v


# ============================================================
#  ENDPOINTS
# ============================================================

@router.post("", status_code=201)
async def submit_promotion(body: PromotionSubmit, member: dict = Depends(get_current_member)):
    """Submete uma promoção para curadoria. Máximo 5 por dia por membro."""
    sb = _sb()
    member_id = member["sub"]

    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).isoformat()
    count_res = (
        sb.table("promotions")
        .select("id", count="exact")
        .eq("submitted_by", member_id)
        .gte("created_at", today_start)
        .execute()
    )
    if (count_res.count or 0) >= _DAILY_SUBMIT_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Limite de {_DAILY_SUBMIT_LIMIT} promoções por dia atingido."
        )

    data = {
        "submitted_by": member_id,
        "title":        body.title,
        "store_name":   body.store_name,
        "category":     body.category,
        "status":       "pending",
    }
    if body.description:
        data["description"] = body.description
    if body.url:
        data["url"] = body.url
    if body.price_now is not None:
        data["price_now"] = body.price_now
    if body.price_was is not None:
        data["price_was"] = body.price_was
    if body.zip_code:
        data["zip_code"] = body.zip_code
    if body.state:
        data["state"] = body.state
    if body.expires_at:
        data["expires_at"] = body.expires_at.isoformat()

    result = sb.table("promotions").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Erro ao salvar promoção.")

    return {
        "id":      result.data[0]["id"],
        "status":  "pending",
        "message": "Promoção enviada. Aparecerá após aprovação.",
    }


@router.get("/mine")
async def list_my_promotions(
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    member: dict = Depends(get_current_member),
):
    """Minhas promoções (todos os status)."""
    sb = _sb()
    result = (
        sb.table("promotions")
        .select("id,title,store_name,category,status,upvotes,created_at,expires_at")
        .eq("submitted_by", member["sub"])
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return {"promotions": result.data or [], "limit": limit, "offset": offset}


@router.get("")
async def list_promotions(
    category: Optional[str] = None,
    zip_code: Optional[str] = None,
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    member: dict = Depends(get_current_member),
):
    """Promoções aprovadas. Filtra por categoria e/ou ZIP."""
    if category and category not in _VALID_CATEGORIES:
        raise HTTPException(status_code=422, detail="Categoria inválida.")

    sb = _sb()
    query = (
        sb.table("promotions")
        .select("id,title,description,store_name,url,price_now,price_was,zip_code,state,category,expires_at,upvotes,created_at")
        .eq("status", "approved")
        .order("upvotes", desc=True)
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
    )
    if category:
        query = query.eq("category", category)
    if zip_code:
        query = query.eq("zip_code", zip_code)

    result = query.execute()
    return {"promotions": result.data or [], "limit": limit, "offset": offset}


@router.get("/{promotion_id}")
async def get_promotion(promotion_id: str, member: dict = Depends(get_current_member)):
    """Detalhe: aprovada (pública) ou do próprio membro (qualquer status)."""
    sb = _sb()
    result = sb.table("promotions").select("*").eq("id", promotion_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Promoção não encontrada.")
    p = result.data[0]
    if p["status"] != "approved" and p["submitted_by"] != member["sub"]:
        raise HTTPException(status_code=404, detail="Promoção não encontrada.")
    return p


@router.post("/{promotion_id}/upvote", status_code=200)
async def upvote_promotion(promotion_id: str, member: dict = Depends(get_current_member)):
    """Upvota uma promoção aprovada. Não pode ser a própria; sem duplo voto."""
    sb = _sb()
    member_id = member["sub"]

    p_res = (
        sb.table("promotions")
        .select("id,submitted_by,upvotes")
        .eq("id", promotion_id)
        .eq("status", "approved")
        .execute()
    )
    if not p_res.data:
        raise HTTPException(status_code=404, detail="Promoção não encontrada.")

    p = p_res.data[0]
    if p["submitted_by"] == member_id:
        raise HTTPException(status_code=400, detail="Não é possível votar na própria promoção.")

    try:
        sb.table("promotion_upvotes").insert({
            "promotion_id": promotion_id,
            "member_id":    member_id,
        }).execute()
    except Exception:
        raise HTTPException(status_code=409, detail="Você já votou nesta promoção.")

    new_count = p["upvotes"] + 1
    sb.table("promotions").update({"upvotes": new_count}).eq("id", promotion_id).execute()
    return {"upvotes": new_count}


@router.delete("/{promotion_id}", status_code=204)
async def delete_promotion(promotion_id: str, member: dict = Depends(get_current_member)):
    """Cancela uma promoção PENDENTE do próprio membro."""
    sb = _sb()
    result = sb.table("promotions").select("id,submitted_by,status").eq("id", promotion_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Promoção não encontrada.")
    p = result.data[0]
    if p["submitted_by"] != member["sub"]:
        raise HTTPException(status_code=404, detail="Promoção não encontrada.")
    if p["status"] != "pending":
        raise HTTPException(status_code=400, detail="Só é possível cancelar promoções pendentes.")
    sb.table("promotions").delete().eq("id", promotion_id).execute()
