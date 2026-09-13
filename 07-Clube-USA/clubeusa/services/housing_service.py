# ============================================================
#  services/housing_service.py — Clube USA — Fase 1.5
#  Moradia: quartos, roommates, apartamentos, casas (seed manual)
# ============================================================

import os
import logging
from datetime import datetime, timezone
from typing import Optional

log = logging.getLogger("housing_service")

LISTING_TYPES = ("room", "roommate", "apartment", "house")
GENDER_PREFS  = ("any", "male", "female")
MAX_LIMIT     = 100


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


# ============================================================
#  LEITURA
# ============================================================

def list_housing(
    zip_code: Optional[str] = None,
    listing_type: Optional[str] = None,
    location_state: Optional[str] = None,
    max_price: Optional[float] = None,
    limit: int = 20,
    offset: int = 0,
) -> list:
    sb = _supabase()
    limit = min(limit, MAX_LIMIT)

    query = (
        sb.table("housing_listings")
        .select(
            "id,title,listing_type,price_monthly,utilities_included,"
            "location_city,location_state,zip_code,bedrooms,bathrooms,"
            "gender_preference,pets_allowed,move_in_date,created_at"
        )
        .eq("is_active", True)
        .order("created_at", desc=True)
        .limit(limit)
        .offset(offset)
    )

    if zip_code:
        query = query.eq("zip_code", zip_code.strip()[:10])
    if listing_type and listing_type in LISTING_TYPES:
        query = query.eq("listing_type", listing_type)
    if location_state:
        query = query.eq("location_state", location_state.upper()[:2])
    if max_price is not None and max_price > 0:
        query = query.lte("price_monthly", max_price)

    now_iso = datetime.now(timezone.utc).isoformat()
    query = query.or_(f"expires_at.is.null,expires_at.gt.{now_iso}")

    result = query.execute()
    return result.data or []


def get_housing(listing_id: str) -> Optional[dict]:
    sb = _supabase()
    result = (
        sb.table("housing_listings")
        .select("*")
        .eq("id", listing_id)
        .eq("is_active", True)
        .execute()
    )
    if not result.data:
        return None
    listing = result.data[0]
    if listing.get("expires_at"):
        expires = datetime.fromisoformat(listing["expires_at"].replace("Z", "+00:00"))
        if expires < datetime.now(timezone.utc):
            return None
    return listing


# ============================================================
#  ESCRITA (admin only)
# ============================================================

def create_housing(
    title: str,
    description: str,
    listing_type: str = "room",
    price_monthly: float = 0,
    utilities_included: bool = False,
    location_city: Optional[str] = None,
    location_state: Optional[str] = None,
    zip_code: Optional[str] = None,
    bedrooms: Optional[int] = None,
    bathrooms: Optional[float] = None,
    gender_preference: str = "any",
    pets_allowed: bool = False,
    move_in_date: Optional[str] = None,
    contact_email: Optional[str] = None,
    contact_phone: Optional[str] = None,
    contact_whatsapp: Optional[str] = None,
    posted_by: Optional[str] = None,
    expires_at: Optional[str] = None,
) -> dict:
    if listing_type not in LISTING_TYPES:
        raise ValueError(f"listing_type inválido: {listing_type}. Use: {', '.join(LISTING_TYPES)}.")
    if gender_preference not in GENDER_PREFS:
        raise ValueError(f"gender_preference inválido. Use: {', '.join(GENDER_PREFS)}.")
    if price_monthly < 0:
        raise ValueError("price_monthly não pode ser negativo.")

    sb = _supabase()
    data = {
        "title":              title.strip()[:200],
        "description":        description.strip()[:5000],
        "listing_type":       listing_type,
        "price_monthly":      price_monthly,
        "utilities_included": utilities_included,
        "location_city":      location_city.strip()[:100] if location_city else None,
        "location_state":     location_state.upper()[:2] if location_state else None,
        "zip_code":           zip_code.strip()[:10] if zip_code else None,
        "bedrooms":           bedrooms,
        "bathrooms":          bathrooms,
        "gender_preference":  gender_preference,
        "pets_allowed":       pets_allowed,
        "move_in_date":       move_in_date,
        "contact_email":      contact_email.strip()[:200] if contact_email else None,
        "contact_phone":      contact_phone.strip()[:30] if contact_phone else None,
        "contact_whatsapp":   contact_whatsapp.strip()[:30] if contact_whatsapp else None,
        "posted_by":          posted_by,
        "expires_at":         expires_at,
        "is_active":          True,
    }
    result = sb.table("housing_listings").insert(data).execute()
    if not result.data:
        raise RuntimeError("Falha ao criar listagem de moradia.")
    log.info(f"Moradia criada: {result.data[0]['id']} — {title}")
    return result.data[0]


def update_housing(listing_id: str, **kwargs) -> Optional[dict]:
    """Atualiza campos permitidos. Campos não mapeados são ignorados."""
    allowed = {
        "title", "description", "listing_type", "price_monthly", "utilities_included",
        "location_city", "location_state", "zip_code", "bedrooms", "bathrooms",
        "gender_preference", "pets_allowed", "move_in_date",
        "contact_email", "contact_phone", "contact_whatsapp",
        "is_active", "expires_at",
    }
    update_data = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not update_data:
        return get_housing(listing_id)

    sb = _supabase()
    result = sb.table("housing_listings").update(update_data).eq("id", listing_id).execute()
    return result.data[0] if result.data else None


def deactivate_housing(listing_id: str) -> bool:
    """Soft-delete: marca listagem como inativa sem apagar do banco."""
    sb = _supabase()
    result = (
        sb.table("housing_listings")
        .update({"is_active": False})
        .eq("id", listing_id)
        .execute()
    )
    return bool(result.data)
