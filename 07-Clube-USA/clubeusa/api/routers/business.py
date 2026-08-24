"""
api/routers/business.py — Diretorio de Empresas Brasileiras nos EUA
Fase 2.1: cadastro de empresa, perfil, diretorio publico, assinatura premium
"""
import os
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
import stripe

from deps import get_current_member

router = APIRouter(prefix="/business", tags=["business"])

VALID_CATEGORIES = frozenset({
    "restaurant", "beauty", "healthcare", "legal", "financial",
    "education", "automotive", "construction", "cleaning", "retail",
    "technology", "transportation", "real_estate", "other",
})

APP_URL = os.environ.get("APP_URL", "https://clubeusa.com")
STRIPE_BUSINESS_PRICE_ID = os.environ.get("STRIPE_BUSINESS_PRICE_ID", "")


# ============================================================
#  SCHEMAS
# ============================================================

class BusinessRegister(BaseModel):
    name:        str
    description: Optional[str] = None
    category:    str
    zip_code:    str
    city:        Optional[str] = None
    state:       Optional[str] = None
    website:     Optional[str] = None
    phone:       Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if not (2 <= len(v) <= 100):
            raise ValueError("Nome deve ter entre 2 e 100 caracteres.")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v):
        if v is not None and len(v) > 1000:
            raise ValueError("Descricao deve ter no maximo 1000 caracteres.")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v):
        if v not in VALID_CATEGORIES:
            raise ValueError(f"Categoria invalida. Opcoes: {sorted(VALID_CATEGORIES)}")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip_code(cls, v):
        cleaned = re.sub(r"[^0-9]", "", v)
        if len(cleaned) != 5:
            raise ValueError("ZIP code deve ter 5 digitos numericos.")
        return cleaned

    @field_validator("website")
    @classmethod
    def validate_website(cls, v):
        if v is None:
            return v
        v = v.strip()
        if v and not v.startswith(("http://", "https://")):
            v = "https://" + v
        return v


class BusinessUpdate(BaseModel):
    name:        Optional[str] = None
    description: Optional[str] = None
    category:    Optional[str] = None
    zip_code:    Optional[str] = None
    city:        Optional[str] = None
    state:       Optional[str] = None
    website:     Optional[str] = None
    phone:       Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if v is not None:
            v = v.strip()
            if not (2 <= len(v) <= 100):
                raise ValueError("Nome deve ter entre 2 e 100 caracteres.")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v):
        if v is not None and len(v) > 1000:
            raise ValueError("Descricao deve ter no maximo 1000 caracteres.")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v):
        if v is not None and v not in VALID_CATEGORIES:
            raise ValueError(f"Categoria invalida. Opcoes: {sorted(VALID_CATEGORIES)}")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip_code(cls, v):
        if v is not None:
            cleaned = re.sub(r"[^0-9]", "", v)
            if len(cleaned) != 5:
                raise ValueError("ZIP code deve ter 5 digitos numericos.")
            return cleaned
        return v

    @field_validator("website")
    @classmethod
    def validate_website(cls, v):
        if v is not None and v.strip() and not v.startswith(("http://", "https://")):
            v = "https://" + v.strip()
        return v


# ============================================================
#  HELPERS
# ============================================================

def _get_supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def _get_business_for_owner(sb, owner_id: str) -> dict:
    """Returns business or raises 404 — never leaks existence to wrong owner."""
    result = sb.table("businesses").select("*").eq("owner_id", owner_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Empresa nao encontrada.")
    return result.data[0]


# ============================================================
#  ENDPOINTS
# ============================================================

@router.post("", status_code=201)
async def register_business(body: BusinessRegister, member: dict = Depends(get_current_member)):
    """Cadastra empresa para o membro autenticado (1 empresa por membro)."""
    from utils.security import encrypt
    sb = _get_supabase()

    existing = sb.table("businesses").select("id").eq("owner_id", member["sub"]).execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="Voce ja possui uma empresa cadastrada.")

    phone_enc = encrypt(body.phone) if body.phone else None

    data = {
        "owner_id":    member["sub"],
        "name":        body.name,
        "description": body.description,
        "category":    body.category,
        "zip_code":    body.zip_code,
        "city":        body.city,
        "state":       body.state,
        "website":     body.website,
        "phone_enc":   phone_enc,
        "plan":        "free",
    }

    result = sb.table("businesses").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Erro ao cadastrar empresa.")

    created = result.data[0]
    return {
        "id":       created["id"],
        "name":     created["name"],
        "plan":     created["plan"],
        "category": created["category"],
    }


@router.get("/profile")
async def get_business_profile(member: dict = Depends(get_current_member)):
    """Perfil completo da empresa do membro autenticado (com telefone descriptografado)."""
    from utils.security import decrypt
    sb = _get_supabase()
    biz = _get_business_for_owner(sb, member["sub"])

    phone = None
    if biz.get("phone_enc"):
        try:
            phone = decrypt(biz["phone_enc"])
        except Exception:
            pass

    return {
        "id":                   biz["id"],
        "name":                 biz["name"],
        "description":          biz["description"],
        "category":             biz["category"],
        "zip_code":             biz["zip_code"],
        "city":                 biz["city"],
        "state":                biz["state"],
        "website":              biz["website"],
        "phone":                phone,
        "plan":                 biz["plan"],
        "premium_started_at":   biz.get("premium_started_at"),
        "premium_expires_at":   biz.get("premium_expires_at"),
        "is_active":            biz["is_active"],
        "created_at":           biz["created_at"],
    }


@router.patch("/profile")
async def update_business_profile(body: BusinessUpdate, member: dict = Depends(get_current_member)):
    """Atualiza campos da empresa. Plano e dono nao podem ser alterados aqui."""
    from utils.security import encrypt
    sb = _get_supabase()
    biz = _get_business_for_owner(sb, member["sub"])

    updates = {}
    if body.name is not None:
        updates["name"] = body.name
    if body.description is not None:
        updates["description"] = body.description
    if body.category is not None:
        updates["category"] = body.category
    if body.zip_code is not None:
        updates["zip_code"] = body.zip_code
    if body.city is not None:
        updates["city"] = body.city
    if body.state is not None:
        updates["state"] = body.state
    if body.website is not None:
        updates["website"] = body.website
    if body.phone is not None:
        updates["phone_enc"] = encrypt(body.phone)

    if not updates:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar.")

    sb.table("businesses").update(updates).eq("id", biz["id"]).execute()
    return {"ok": True}


@router.get("/directory")
async def list_businesses(
    zip_code: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 20,
):
    """Diretorio publico de empresas — nao requer autenticacao."""
    sb = _get_supabase()
    limit = min(limit, 50)

    query = (
        sb.table("businesses")
        .select("id,name,description,category,zip_code,city,state,website,plan,created_at")
        .eq("is_active", True)
        .order("plan", desc=True)
        .order("created_at", desc=False)
        .limit(limit)
    )
    if zip_code:
        cleaned = re.sub(r"[^0-9]", "", zip_code)[:5]
        if cleaned:
            query = query.eq("zip_code", cleaned)
    if category and category in VALID_CATEGORIES:
        query = query.eq("category", category)

    result = query.execute()
    return {"businesses": result.data or []}


@router.post("/subscribe")
async def subscribe_business_premium(member: dict = Depends(get_current_member)):
    """Cria sessao Stripe para assinar o plano premium da empresa ($10-30/mes)."""
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not stripe.api_key or not STRIPE_BUSINESS_PRICE_ID:
        raise HTTPException(status_code=503, detail="Pagamento nao configurado.")

    sb = _get_supabase()
    biz = _get_business_for_owner(sb, member["sub"])

    if biz["plan"] == "premium":
        raise HTTPException(status_code=400, detail="Empresa ja possui plano premium.")

    try:
        session = stripe.checkout.Session.create(
            mode                 = "subscription",
            payment_method_types = ["card"],
            line_items           = [{"price": STRIPE_BUSINESS_PRICE_ID, "quantity": 1}],
            success_url          = f"{APP_URL}/business/sucesso?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url           = f"{APP_URL}/business/cancelado",
            metadata             = {"business_id": biz["id"], "owner_id": member["sub"]},
            subscription_data    = {"metadata": {"business_id": biz["id"]}},
            locale               = "pt-BR",
        )
        return {"checkout_url": session.url, "session_id": session.id}
    except stripe.error.StripeError as e:
        import logging
        logging.getLogger("api").error(f"Stripe business subscribe erro: {e}")
        raise HTTPException(status_code=502, detail="Erro ao criar sessao de pagamento.")


@router.post("/portal")
async def business_billing_portal(member: dict = Depends(get_current_member)):
    """Portal Stripe para gerenciar assinatura premium da empresa."""
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not stripe.api_key:
        raise HTTPException(status_code=503)

    sb = _get_supabase()
    biz = _get_business_for_owner(sb, member["sub"])

    if not biz.get("stripe_customer_id"):
        raise HTTPException(status_code=400, detail="Nenhuma assinatura ativa encontrada.")

    try:
        session = stripe.billing_portal.Session.create(
            customer   = biz["stripe_customer_id"],
            return_url = f"{APP_URL}/business/painel",
        )
        return {"portal_url": session.url}
    except stripe.error.StripeError as e:
        import logging
        logging.getLogger("api").error(f"Stripe business portal erro: {e}")
        raise HTTPException(status_code=502)
