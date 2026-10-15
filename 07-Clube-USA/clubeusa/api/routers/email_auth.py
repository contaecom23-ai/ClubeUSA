# ============================================================
#  api/routers/email_auth.py — Clube USA — Fase 0.1
#
#  POST /auth/register-email   — cadastro com email + senha
#  GET  /auth/confirm-email    — confirmacao do email (token)
#  POST /auth/login            — login email + senha → JWT
#  PUT  /member/profile        — atualizar perfil minimo
# ============================================================

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator

from deps import get_current_member
from utils.security import (
    validate_email, sanitize,
    hash_pii, encrypt,
    generate_referral_code,
    hash_password, verify_password,
    generate_email_token, create_web_token,
)

log = logging.getLogger("email_auth")

router = APIRouter()

_ZIP_RE = __import__("re").compile(r"^\d{5}(-\d{4})?$")
_PASSWORD_MIN = 8


# ── Schemas ─────────────────────────────────────────────────

class EmailRegisterRequest(BaseModel):
    email:         str
    password:      str
    name:          Optional[str] = None
    language:      str = "pt"
    state:         Optional[str] = None
    zip_code:      Optional[str] = None
    referral_code: Optional[str] = None

    @field_validator("language")
    @classmethod
    def validate_language(cls, v):
        if v not in ("pt", "es"):
            raise ValueError("Idioma invalido. Use 'pt' ou 'es'.")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < _PASSWORD_MIN:
            raise ValueError(f"Senha deve ter ao menos {_PASSWORD_MIN} caracteres.")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v):
        if v and not _ZIP_RE.match(v.strip()):
            raise ValueError("ZIP code invalido. Use formato 12345 ou 12345-6789.")
        return v.strip() if v else None


class EmailLoginRequest(BaseModel):
    email:    str
    password: str


class ProfileUpdateRequest(BaseModel):
    name:      Optional[str] = None
    state:     Optional[str] = None
    zip_code:  Optional[str] = None
    language:  Optional[str] = None
    categories: Optional[list[str]] = None

    @field_validator("language")
    @classmethod
    def validate_language(cls, v):
        if v and v not in ("pt", "es"):
            raise ValueError("Idioma invalido. Use 'pt' ou 'es'.")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v):
        if v and not _ZIP_RE.match(v.strip()):
            raise ValueError("ZIP code invalido.")
        return v.strip() if v else None

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, v):
        if v is None:
            return v
        valid = {"all","electronics","kitchen","baby","fitness",
                 "beauty","tools","pets","fashion","automotive","books"}
        cleaned = [c for c in v if c in valid]
        return cleaned or ["all"]


# ── Helpers ──────────────────────────────────────────────────

def _sb():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def _audit(action: str, target_id: str, metadata: dict = None, ip: str = None):
    from utils.security import hash_ip
    try:
        sb = _sb()
        sb.table("audit_logs").insert({
            "actor_type":  "system",
            "action":      action,
            "target_type": "member",
            "target_id":   target_id,
            "ip_hash":     hash_ip(ip) if ip else None,
            "metadata":    metadata or {},
        }).execute()
    except Exception as e:
        log.warning(f"Audit log falhou: {e}")


# ── Endpoints ────────────────────────────────────────────────

@router.post("/auth/register-email", status_code=201)
async def register_email(body: EmailRegisterRequest, request: Request):
    """
    Cadastro via email + senha.
    Envia email de confirmacao. Conta so ativa apos confirmar.
    """
    sb = _sb()

    # Validar e normalizar email
    try:
        email = validate_email(body.email)
    except ValueError:
        raise HTTPException(status_code=422, detail="Email invalido.")

    email_hash = hash_pii(email)

    # Verificar duplicata
    existing = sb.table("members").select("id,email_confirmed").eq("email_hash", email_hash).execute()
    if existing.data:
        m = existing.data[0]
        if m.get("email_confirmed"):
            raise HTTPException(status_code=409, detail="Email ja cadastrado.")
        # Conta existe mas email nao confirmado — reenviar confirmacao
        return _resend_confirmation(sb, m["id"], email, body.name, request)

    # Processar indicacao
    referrer_id = None
    if body.referral_code:
        ref = sb.table("members").select("id").eq(
            "referral_code", body.referral_code.upper().strip()
        ).execute()
        if ref.data:
            referrer_id = ref.data[0]["id"]

    # Hash de senha
    pw_hash = hash_password(body.password)

    # Gerar token de confirmacao
    token = generate_email_token()
    token_expires = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()

    # Preparar dados do membro
    name    = sanitize(body.name or "", 80)
    state   = sanitize(body.state or "", 50)
    ref_code = generate_referral_code()

    member_data = {
        "phone_hash":                  f"email:{email_hash}",  # placeholder unico
        "phone_enc":                   encrypt(f"email:{email}"),
        "email_hash":                  email_hash,
        "email_enc":                   encrypt(email),
        "name_enc":                    encrypt(name) if name else None,
        "language":                    body.language,
        "state":                       state or None,
        "zip_code":                    body.zip_code,
        "referral_code":               ref_code,
        "referred_by":                 referrer_id,
        "password_hash":               pw_hash,
        "email_confirmed":             False,
        "email_confirmation_token":    token,
        "email_token_expires_at":      token_expires,
    }

    try:
        result = sb.table("members").insert(member_data).execute()
    except Exception as e:
        err_str = str(e).lower()
        if "unique" in err_str or "duplicate" in err_str:
            raise HTTPException(status_code=409, detail="Email ja cadastrado.")
        log.error(f"Erro ao criar membro: {e}")
        raise HTTPException(status_code=500, detail="Erro interno. Tente novamente.")

    member_id = result.data[0]["id"]
    _audit("email_register", member_id, ip=request.client.host if request.client else None)

    # Enviar email de confirmacao
    from services.email_service import send_confirmation_email
    send_confirmation_email(email, name, token)

    return {
        "message":    "Cadastro realizado! Verifique seu email para confirmar sua conta.",
        "member_id":  member_id,
        "email_confirmed": False,
    }


def _resend_confirmation(sb, member_id: str, email: str, name: str, request: Request) -> dict:
    """Regera e reenvia token de confirmacao para conta nao confirmada."""
    token = generate_email_token()
    token_expires = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    sb.table("members").update({
        "email_confirmation_token":  token,
        "email_token_expires_at":    token_expires,
    }).eq("id", member_id).execute()

    from services.email_service import send_confirmation_email
    send_confirmation_email(email, name or "", token)
    _audit("email_confirm_resend", member_id, ip=request.client.host if request.client else None)

    return {
        "message":    "Email de confirmacao reenviado. Verifique sua caixa de entrada.",
        "member_id":  member_id,
        "email_confirmed": False,
    }


@router.get("/auth/confirm-email")
async def confirm_email(token: str, request: Request):
    """
    Confirma email via token enviado por email.
    Redireciona para /login?confirmed=1 ou retorna JSON.
    """
    if not token or len(token) > 128:
        raise HTTPException(status_code=400, detail="Token invalido.")

    sb = _sb()
    result = sb.table("members").select(
        "id,email_confirmed,email_token_expires_at,referral_code,name_enc"
    ).eq("email_confirmation_token", token).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Token invalido ou ja utilizado.")

    member = result.data[0]

    if member.get("email_confirmed"):
        return {"message": "Email ja confirmado. Faca login.", "already_confirmed": True}

    # Verificar TTL
    expires_raw = member.get("email_token_expires_at")
    if expires_raw:
        expires = datetime.fromisoformat(expires_raw.replace("Z", "+00:00"))
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires:
            raise HTTPException(
                status_code=400,
                detail="Token expirado. Faca login novamente para receber um novo link."
            )

    # Confirmar
    sb.table("members").update({
        "email_confirmed":            True,
        "email_confirmation_token":   None,
        "email_token_expires_at":     None,
    }).eq("id", member["id"]).execute()

    _audit("email_confirmed", member["id"], ip=request.client.host if request.client else None)

    # Boas-vindas
    from utils.security import decrypt as _decrypt
    from services.email_service import send_welcome_email
    email_row = sb.table("members").select("email_enc,name_enc").eq("id", member["id"]).execute()
    if email_row.data:
        row = email_row.data[0]
        email_plain = _decrypt(row["email_enc"]) if row.get("email_enc") else ""
        name_plain  = _decrypt(row["name_enc"])  if row.get("name_enc")  else ""
        send_welcome_email(email_plain, name_plain, member["referral_code"])

    return {"message": "Email confirmado com sucesso! Faca login.", "confirmed": True}


@router.post("/auth/login")
async def login_email(body: EmailLoginRequest, request: Request):
    """
    Login via email + senha.
    Retorna JWT (7 dias) se credenciais validas e email confirmado.
    """
    try:
        email = validate_email(body.email)
    except ValueError:
        raise HTTPException(status_code=422, detail="Email invalido.")

    email_hash = hash_pii(email)
    sb = _sb()

    result = sb.table("members").select(
        "id,plan,status,password_hash,email_confirmed"
    ).eq("email_hash", email_hash).execute()

    # Resposta generica para nao vazar existencia de conta
    _generic_err = HTTPException(status_code=401, detail="Credenciais invalidas.")

    if not result.data:
        raise _generic_err

    member = result.data[0]

    if member.get("status") == "banned":
        raise HTTPException(status_code=403, detail="Acesso negado.")

    if not member.get("password_hash"):
        # Conta criada via phone — sem senha definida
        raise _generic_err

    if not verify_password(body.password, member["password_hash"]):
        _audit("login_failed", member["id"], {"reason": "wrong_password"},
               ip=request.client.host if request.client else None)
        raise _generic_err

    if not member.get("email_confirmed"):
        raise HTTPException(
            status_code=403,
            detail="Email nao confirmado. Verifique sua caixa de entrada."
        )

    token = create_web_token(member["id"], member.get("plan", "free"))
    _audit("login_success", member["id"], ip=request.client.host if request.client else None)

    return {
        "token":     token,
        "member_id": member["id"],
        "plan":      member.get("plan", "free"),
        "expires_in_days": 7,
    }


@router.put("/member/profile")
async def update_profile(
    body: ProfileUpdateRequest,
    request: Request,
    member: dict = Depends(get_current_member),
):
    """
    Atualiza perfil minimo: nome, estado, ZIP, idioma, categorias.
    Owner e sempre extraido do token (nunca do cliente).
    """
    member_id = member["sub"]
    sb = _sb()

    updates: dict = {}

    if body.name is not None:
        name = sanitize(body.name, 80)
        updates["name_enc"] = encrypt(name) if name else None

    if body.state is not None:
        updates["state"] = sanitize(body.state, 50) or None

    if body.zip_code is not None:
        updates["zip_code"] = body.zip_code

    if body.language is not None:
        updates["language"] = body.language

    if body.categories is not None:
        updates["categories"] = body.categories

    if not updates:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar.")

    try:
        sb.table("members").update(updates).eq("id", member_id).execute()
    except Exception as e:
        log.error(f"Erro ao atualizar perfil {member_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar perfil.")

    _audit("profile_update", member_id, {"fields": list(updates.keys())},
           ip=request.client.host if request.client else None)

    return {"message": "Perfil atualizado com sucesso."}
