# api/routers/businesses.py — Fase 2.1: assinatura de empresas locais
import os
import logging
from typing import Optional
from datetime import datetime, timedelta, timezone

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator
from supabase import create_client

from deps import get_current_business, require_admin

router = APIRouter(tags=["businesses"])
log = logging.getLogger("businesses")

_STRIPE_BUSINESS_BASIC_PRICE_ID   = lambda: os.environ.get("STRIPE_BUSINESS_BASIC_PRICE_ID", "")
_STRIPE_BUSINESS_PREMIUM_PRICE_ID = lambda: os.environ.get("STRIPE_BUSINESS_PREMIUM_PRICE_ID", "")
_APP_URL = lambda: os.environ.get("APP_URL", "https://clubeusa.com")


def _sb():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def _otp_save(phone_hash: str, otp: str, ttl_sec: int = 600):
    sb = _sb()
    sb.table("otp_codes").delete().eq("phone_hash", phone_hash).execute()
    sb.table("otp_codes").insert({
        "phone_hash": phone_hash,
        "otp":        otp,
        "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=ttl_sec)).isoformat(),
    }).execute()


def _otp_verify(phone_hash: str, otp: str) -> tuple:
    sb = _sb()
    result = sb.table("otp_codes").select("*").eq("phone_hash", phone_hash).execute()
    if not result.data:
        return False, "Código inválido ou expirado."

    record = result.data[0]
    expires = datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00"))
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires:
        sb.table("otp_codes").delete().eq("phone_hash", phone_hash).execute()
        return False, "Código expirado. Solicite um novo."

    if record["attempts"] >= 3:
        sb.table("otp_codes").delete().eq("phone_hash", phone_hash).execute()
        return False, "Muitas tentativas. Solicite novo código."

    if record["otp"] != otp:
        sb.table("otp_codes").update({"attempts": record["attempts"] + 1}).eq(
            "phone_hash", phone_hash
        ).execute()
        return False, "Código incorreto."

    sb.table("otp_codes").delete().eq("phone_hash", phone_hash).execute()
    return True, ""


# ── Schemas ──────────────────────────────────────────────────────────────────

_VALID_CATEGORIES = {
    "restaurant", "retail", "services", "healthcare", "beauty",
    "automotive", "education", "entertainment", "real_estate", "other",
}


class BusinessRegisterRequest(BaseModel):
    phone:       str
    name:        str
    owner_name:  Optional[str] = None
    email:       Optional[str] = None
    zip_code:    Optional[str] = None
    city:        Optional[str] = None
    state:       Optional[str] = None
    category:    str = "other"
    description: Optional[str] = None
    website:     Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nome da empresa deve ter pelo menos 2 caracteres.")
        return v[:200]

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in _VALID_CATEGORIES:
            raise ValueError(f"Categoria inválida. Use: {', '.join(sorted(_VALID_CATEGORIES))}")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return v.strip()[:500] or None

    @field_validator("website")
    @classmethod
    def validate_website(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if v and not (v.startswith("http://") or v.startswith("https://")):
            v = "https://" + v
        return v[:500] or None

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        import re
        z = v.strip()
        if not re.match(r'^\d{5}$', z):
            raise ValueError("ZIP code inválido. Use 5 dígitos.")
        return z


class BusinessOTPRequest(BaseModel):
    phone: str


class BusinessOTPVerify(BaseModel):
    phone: str
    otp:   str


class BusinessSubscribeRequest(BaseModel):
    plan: str

    @field_validator("plan")
    @classmethod
    def validate_plan(cls, v: str) -> str:
        if v not in ("basic", "premium"):
            raise ValueError("Plano inválido. Use 'basic' ($10/mês) ou 'premium' ($30/mês).")
        return v


# ── Public: Registration ──────────────────────────────────────────────────────

@router.post("/business/register", status_code=201)
async def register_business(body: BusinessRegisterRequest):
    """
    Register a new local business (status=pending until admin approval).
    Public endpoint — no JWT required.
    """
    from utils.security import validate_phone, hash_pii, encrypt, sanitize

    try:
        phone = validate_phone(body.phone)
    except ValueError:
        raise HTTPException(status_code=422, detail="Telefone inválido.")

    phone_hash = hash_pii(phone)
    sb = _sb()

    existing = sb.table("businesses").select("id,status").eq("phone_hash", phone_hash).execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="Este número já está cadastrado.")

    biz_data: dict = {
        "phone_hash": phone_hash,
        "phone_enc":  encrypt(phone),
        "name":       sanitize(body.name, 200),
        "category":   body.category,
    }
    if body.owner_name:
        biz_data["owner_name"] = sanitize(body.owner_name, 100)
    if body.email:
        from utils.security import validate_email
        try:
            email = validate_email(body.email)
            biz_data["email_hash"] = hash_pii(email)
            biz_data["email_enc"]  = encrypt(email)
        except ValueError:
            raise HTTPException(status_code=422, detail="Email inválido.")
    if body.zip_code:
        biz_data["zip_code"] = body.zip_code
    if body.city:
        biz_data["city"] = sanitize(body.city, 100)
    if body.state:
        biz_data["state"] = sanitize(body.state, 50)
    if body.description:
        biz_data["description"] = body.description
    if body.website:
        biz_data["website"] = body.website

    result = sb.table("businesses").insert(biz_data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Erro ao cadastrar empresa.")

    biz = result.data[0]
    return {
        "id":      biz["id"],
        "name":    biz["name"],
        "status":  biz["status"],
        "message": "Empresa cadastrada. Aguardando aprovação do time Clube USA.",
    }


# ── Public: Business Auth (OTP) ───────────────────────────────────────────────

@router.post("/business/otp/request")
async def business_otp_request(body: BusinessOTPRequest):
    """Send OTP to business phone for login."""
    from utils.security import validate_phone, hash_pii, generate_otp

    try:
        phone = validate_phone(body.phone)
    except ValueError:
        raise HTTPException(status_code=422, detail="Telefone inválido.")

    phone_hash = hash_pii(phone)
    sb = _sb()
    biz = sb.table("businesses").select("id,status").eq("phone_hash", phone_hash).execute()
    if not biz.data:
        raise HTTPException(status_code=404, detail="Empresa não encontrada. Cadastre-se primeiro.")
    if biz.data[0]["status"] == "rejected":
        raise HTTPException(status_code=403, detail="Acesso negado.")

    otp = generate_otp()
    _otp_save(phone_hash, otp, ttl_sec=600)

    if os.environ.get("ENVIRONMENT") == "production":
        _send_business_otp_whatsapp(phone, otp)
    else:
        log.info("[DEV] Business OTP para %s: %s", phone, otp)

    return {"message": "Código enviado para seu WhatsApp.", "expires_in": 600}


@router.post("/business/otp/verify")
async def business_otp_verify(body: BusinessOTPVerify):
    """Verify OTP and return business JWT."""
    from utils.security import validate_phone, hash_pii, create_business_token

    try:
        phone = validate_phone(body.phone)
    except ValueError:
        raise HTTPException(status_code=422, detail="Telefone inválido.")

    phone_hash = hash_pii(phone)
    ok, error_msg = _otp_verify(phone_hash, body.otp)
    if not ok:
        status = 429 if "tentativas" in error_msg else 400
        raise HTTPException(status_code=status, detail=error_msg)

    sb = _sb()
    result = sb.table("businesses").select("id,plan,status").eq("phone_hash", phone_hash).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")

    biz = result.data[0]
    if biz["status"] in ("rejected", "suspended"):
        raise HTTPException(status_code=403, detail="Acesso negado.")

    token = create_business_token(biz["id"], biz["plan"])
    return {"token": token, "business_id": biz["id"], "plan": biz["plan"], "status": biz["status"]}


# ── Business-authenticated endpoints ─────────────────────────────────────────

@router.get("/business/profile")
async def get_business_profile(biz: dict = Depends(get_current_business)):
    """Return business profile (owner-only)."""
    sb = _sb()
    result = (
        sb.table("businesses")
        .select("id,name,owner_name,zip_code,city,state,category,description,website,plan,status,created_at")
        .eq("id", biz["sub"])
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    return result.data[0]


@router.post("/business/subscribe")
async def business_subscribe(body: BusinessSubscribeRequest, biz: dict = Depends(get_current_business)):
    """Create Stripe checkout session for business plan upgrade."""
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not stripe.api_key:
        raise HTTPException(status_code=503, detail="Pagamento não configurado.")

    if biz.get("plan") == body.plan:
        raise HTTPException(status_code=400, detail=f"Você já está no plano {body.plan}.")

    price_id = (
        _STRIPE_BUSINESS_BASIC_PRICE_ID()
        if body.plan == "basic"
        else _STRIPE_BUSINESS_PREMIUM_PRICE_ID()
    )
    if not price_id:
        raise HTTPException(status_code=503, detail=f"Plano '{body.plan}' não configurado no Stripe.")

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{_APP_URL()}/business/sucesso?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{_APP_URL()}/business/cancelado",
            metadata={"business_id": biz["sub"], "plan": body.plan, "role": "business"},
            locale="pt-BR",
        )
        return {"checkout_url": session.url, "session_id": session.id}
    except stripe.error.StripeError as e:
        log.error("Stripe business checkout erro: %s", e)
        raise HTTPException(status_code=502, detail="Erro ao criar sessão de pagamento.")


@router.post("/business/portal")
async def business_billing_portal(biz: dict = Depends(get_current_business)):
    """Stripe billing portal for managing business subscription."""
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not stripe.api_key:
        raise HTTPException(status_code=503)

    sb = _sb()
    result = sb.table("businesses").select("stripe_customer_id").eq("id", biz["sub"]).execute()
    if not result.data or not result.data[0].get("stripe_customer_id"):
        raise HTTPException(status_code=400, detail="Nenhuma assinatura ativa encontrada.")

    try:
        session = stripe.billing_portal.Session.create(
            customer=result.data[0]["stripe_customer_id"],
            return_url=f"{_APP_URL()}/business/painel",
        )
        return {"portal_url": session.url}
    except stripe.error.StripeError as e:
        log.error("Stripe business portal erro: %s", e)
        raise HTTPException(status_code=502)


# ── Public: business listing for members ─────────────────────────────────────

@router.get("/public/businesses")
async def list_businesses(
    zip_code:  Optional[str] = None,
    category:  Optional[str] = None,
    limit:     int = 20,
):
    """
    Public listing of active businesses (no auth required).
    Members use this to discover local businesses.
    """
    limit = min(max(1, limit), 50)
    sb = _sb()

    query = (
        sb.table("businesses")
        .select("id,name,zip_code,city,state,category,description,website,plan")
        .eq("status", "active")
        .order("plan", desc=True)  # premium first
        .limit(limit)
    )
    if zip_code:
        import re
        if re.match(r'^\d{5}$', zip_code.strip()):
            query = query.eq("zip_code", zip_code.strip())
    if category and category in _VALID_CATEGORIES:
        query = query.eq("category", category)

    result = query.execute()
    return {"businesses": result.data or [], "total": len(result.data or [])}


# ── Admin: business management ────────────────────────────────────────────────

@router.get("/admin/businesses", dependencies=[Depends(require_admin)])
async def admin_list_businesses(
    status:   Optional[str] = None,
    category: Optional[str] = None,
    limit:    int = 50,
    offset:   int = 0,
):
    """Admin: list businesses with optional status/category filter."""
    limit = min(limit, 100)
    sb = _sb()

    query = (
        sb.table("businesses")
        .select("id,name,owner_name,zip_code,city,category,plan,status,created_at")
        .order("created_at", desc=True)
        .limit(limit)
        .offset(offset)
    )
    if status:
        query = query.eq("status", status)
    if category:
        query = query.eq("category", category)

    result = query.execute()
    return {"businesses": result.data or [], "limit": limit, "offset": offset}


@router.post("/admin/businesses/{business_id}/approve", dependencies=[Depends(require_admin)])
async def admin_approve_business(business_id: str):
    """Admin: approve a pending business (status → active)."""
    sb = _sb()
    result = (
        sb.table("businesses")
        .update({"status": "active"})
        .eq("id", business_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    return {"ok": True, "status": "active"}


@router.post("/admin/businesses/{business_id}/reject", dependencies=[Depends(require_admin)])
async def admin_reject_business(business_id: str):
    """Admin: reject a pending business (status → rejected)."""
    sb = _sb()
    result = (
        sb.table("businesses")
        .update({"status": "rejected"})
        .eq("id", business_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    return {"ok": True, "status": "rejected"}


@router.post("/admin/businesses/{business_id}/suspend", dependencies=[Depends(require_admin)])
async def admin_suspend_business(business_id: str):
    """Admin: suspend an active business."""
    sb = _sb()
    result = (
        sb.table("businesses")
        .update({"status": "suspended"})
        .eq("id", business_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    return {"ok": True, "status": "suspended"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _send_business_otp_whatsapp(phone: str, otp: str):
    import requests
    msg = (
        f"*Clube USA — Empresas*\n\n"
        f"Seu código de acesso: *{otp}*\n\n"
        f"Válido por 10 minutos. Nunca compartilhe este código."
    )
    try:
        requests.post(
            f"https://api.z-api.io/instances/{os.environ['ZAPI_INSTANCE']}/token/{os.environ['ZAPI_TOKEN']}/send-text",
            json={"phone": phone, "message": msg},
            headers={"Client-Token": os.environ["ZAPI_CLIENT_TOKEN"]},
            timeout=10,
        )
    except Exception as e:
        log.error("Falha ao enviar OTP de business: %s", e)


def handle_business_checkout_completed(session: dict):
    """Called from main.py Stripe webhook when a business subscription is confirmed."""
    business_id = session.get("metadata", {}).get("business_id")
    plan        = session.get("metadata", {}).get("plan", "basic")
    customer_id = session.get("customer")
    if not business_id:
        return

    sb = _sb()
    sb.table("businesses").update({
        "plan":               plan,
        "stripe_customer_id": customer_id,
        "status":             "active",
    }).eq("id", business_id).execute()

    sb.table("audit_logs").insert({
        "actor_type":  "system",
        "action":      "business.plan_activated",
        "target_type": "business",
        "target_id":   business_id,
        "metadata":    {"plan": plan, "stripe_customer_id": customer_id},
    }).execute()
    log.info("Business plan activated: %s → %s", business_id, plan)


def handle_business_subscription_cancelled(subscription: dict):
    """Called from main.py Stripe webhook when a business subscription is cancelled."""
    customer_id = subscription.get("customer")
    if not customer_id:
        return

    sb = _sb()
    result = sb.table("businesses").select("id").eq("stripe_customer_id", customer_id).execute()
    if not result.data:
        return

    business_id = result.data[0]["id"]
    sb.table("businesses").update({"plan": "free"}).eq("id", business_id).execute()

    sb.table("audit_logs").insert({
        "actor_type":  "system",
        "action":      "business.plan_cancelled",
        "target_type": "business",
        "target_id":   business_id,
        "metadata":    {"stripe_customer_id": customer_id},
    }).execute()
    log.info("Business plan cancelled: %s", business_id)
