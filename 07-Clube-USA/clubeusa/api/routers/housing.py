# api/routers/housing.py — Clube USA — Fase 1.5
import re
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from deps import get_current_member, require_admin
from services.housing_service import (
    list_housing, get_housing, create_housing, update_housing, deactivate_housing,
    LISTING_TYPES, GENDER_PREFS,
)

router = APIRouter(prefix="/housing", tags=["housing"])
log = logging.getLogger("housing")

_ZIP_RE = re.compile(r"^\d{5}(-\d{4})?$")


# ── Schemas ──────────────────────────────────────────────────

class HousingCreate(BaseModel):
    title: str
    description: str
    listing_type: str = "room"
    price_monthly: float
    utilities_included: bool = False
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    zip_code: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    gender_preference: str = "any"
    pets_allowed: bool = False
    move_in_date: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_whatsapp: Optional[str] = None
    expires_at: Optional[str] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        v = v.strip()
        if len(v) < 5:
            raise ValueError("Título deve ter pelo menos 5 caracteres.")
        return v[:200]

    @field_validator("description")
    @classmethod
    def validate_description(cls, v):
        v = v.strip()
        if len(v) < 20:
            raise ValueError("Descrição deve ter pelo menos 20 caracteres.")
        return v[:5000]

    @field_validator("price_monthly")
    @classmethod
    def validate_price(cls, v):
        if v < 0:
            raise ValueError("price_monthly não pode ser negativo.")
        return v

    @field_validator("listing_type")
    @classmethod
    def validate_listing_type(cls, v):
        if v not in LISTING_TYPES:
            raise ValueError(f"listing_type deve ser um de: {', '.join(LISTING_TYPES)}.")
        return v

    @field_validator("gender_preference")
    @classmethod
    def validate_gender_pref(cls, v):
        if v not in GENDER_PREFS:
            raise ValueError(f"gender_preference deve ser um de: {', '.join(GENDER_PREFS)}.")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v):
        if v is None:
            return v
        if not _ZIP_RE.match(v.strip()):
            raise ValueError("ZIP inválido (use 12345 ou 12345-6789).")
        return v.strip()


class HousingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    listing_type: Optional[str] = None
    price_monthly: Optional[float] = None
    utilities_included: Optional[bool] = None
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    zip_code: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    gender_preference: Optional[str] = None
    pets_allowed: Optional[bool] = None
    move_in_date: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_whatsapp: Optional[str] = None
    is_active: Optional[bool] = None
    expires_at: Optional[str] = None


# ── Member endpoints ─────────────────────────────────────────

@router.get("")
async def list_housing_listings(
    zip_code: Optional[str] = None,
    listing_type: Optional[str] = None,
    state: Optional[str] = None,
    max_price: Optional[float] = None,
    limit: int = 20,
    offset: int = 0,
    member: dict = Depends(get_current_member),
):
    """Lista anúncios de moradia ativos. Filtra por ZIP, tipo, estado e preço máximo."""
    listings = list_housing(
        zip_code=zip_code,
        listing_type=listing_type,
        location_state=state,
        max_price=max_price,
        limit=limit,
        offset=offset,
    )
    return {"listings": listings, "count": len(listings)}


@router.get("/{listing_id}")
async def get_housing_listing(listing_id: str, member: dict = Depends(get_current_member)):
    """Retorna detalhes completos de um anúncio ativo (inclui contato)."""
    listing = get_housing(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Anúncio não encontrado.")
    return listing


# ── Admin endpoints ──────────────────────────────────────────

@router.post("/admin", status_code=201, dependencies=[Depends(require_admin)])
async def admin_create_housing(body: HousingCreate):
    """Admin: cria novo anúncio de moradia (seed manual)."""
    try:
        listing = create_housing(**body.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return listing


@router.patch("/admin/{listing_id}", dependencies=[Depends(require_admin)])
async def admin_update_housing(listing_id: str, body: HousingUpdate):
    """Admin: atualiza campos de um anúncio de moradia."""
    try:
        updated = update_housing(listing_id, **body.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not updated:
        raise HTTPException(status_code=404, detail="Anúncio não encontrado.")
    return updated


@router.delete("/admin/{listing_id}", dependencies=[Depends(require_admin)])
async def admin_deactivate_housing(listing_id: str):
    """Admin: desativa um anúncio (soft delete)."""
    ok = deactivate_housing(listing_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Anúncio não encontrado.")
    return {"ok": True}
