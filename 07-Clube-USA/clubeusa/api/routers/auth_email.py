# ============================================================
#  api/routers/auth_email.py — Clube USA
#  Confirmacao de email (Fase 0.1)
#
#  POST /auth/email/confirm/request  — solicita envio (auth necessaria)
#  GET  /auth/email/confirm/{token}  — confirma via token (publico)
# ============================================================

import os
import secrets
import logging
from datetime import datetime, timedelta, timezone

_now = lambda: datetime.now(timezone.utc)

from fastapi import APIRouter, Depends, HTTPException
from deps import get_current_member

router = APIRouter(prefix="/auth/email", tags=["auth"])
log = logging.getLogger("auth_email")

_MAX_PENDING_TOKENS = 3
_TOKEN_TTL_HRS = 24


def _sb():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


# ============================================================
#  POST /auth/email/confirm/request
# ============================================================

@router.post("/confirm/request", status_code=202)
async def request_email_confirmation(member: dict = Depends(get_current_member)):
    """
    Envia link de confirmacao para o email do membro autenticado.
    Requer que o email esteja cadastrado no perfil.
    Limite: 3 tokens pendentes simultaneos por membro.
    """
    sb = _sb()
    result = sb.table("members").select(
        "id,email_enc,email_confirmed,language,name_enc"
    ).eq("id", member["sub"]).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Membro nao encontrado.")

    m = result.data[0]

    if not m.get("email_enc"):
        raise HTTPException(
            status_code=400,
            detail="Nenhum email cadastrado. Atualize seu perfil primeiro.",
        )

    if m.get("email_confirmed"):
        raise HTTPException(status_code=400, detail="Email ja confirmado.")

    # Rate-limit: max _MAX_PENDING_TOKENS ativos por membro
    now_iso = _now().isoformat()
    pending = sb.table("email_confirm_tokens").select("id").eq(
        "member_id", member["sub"]
    ).eq("used", False).gte("expires_at", now_iso).execute()

    if len(pending.data or []) >= _MAX_PENDING_TOKENS:
        raise HTTPException(
            status_code=429,
            detail="Muitas solicitacoes pendentes. Aguarde e tente novamente.",
        )

    # Gera token seguro e persiste
    token   = secrets.token_urlsafe(32)
    expires = _now() + timedelta(hours=_TOKEN_TTL_HRS)

    sb.table("email_confirm_tokens").insert({
        "member_id":  member["sub"],
        "token":      token,
        "expires_at": expires.isoformat(),
    }).execute()

    # Envia email (ou loga em dev)
    from utils.security import decrypt
    from services.email_service import send_email_confirmation

    email = decrypt(m["email_enc"])
    name  = decrypt(m["name_enc"]) if m.get("name_enc") else ""
    lang  = m.get("language", "pt")
    app_url = os.environ.get("APP_URL", "https://clubeusa.com")
    confirm_url = f"{app_url}/auth/email/confirm/{token}"

    send_email_confirmation(email, name, confirm_url, lang)

    log.info(f"Email confirm solicitado para membro {member['sub']}")
    return {"message": "Email de confirmacao enviado.", "expires_in_hours": _TOKEN_TTL_HRS}


# ============================================================
#  GET /auth/email/confirm/{token}
# ============================================================

@router.get("/confirm/{token}", include_in_schema=False)
async def confirm_email(token: str):
    """
    Confirma email via token recebido por email.
    Rota publica — o token e o segredo, sem necessidade de JWT.
    """
    # Guarda contra tokens absurdamente longos
    if len(token) > 128:
        raise HTTPException(status_code=400, detail="Token invalido.")

    sb  = _sb()
    now = _now()

    result = sb.table("email_confirm_tokens").select(
        "id,member_id,expires_at,used"
    ).eq("token", token).execute()

    if not result.data:
        raise HTTPException(status_code=400, detail="Link invalido ou expirado.")

    record = result.data[0]

    if record["used"]:
        raise HTTPException(status_code=400, detail="Link ja utilizado.")

    expires = datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00"))
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if now > expires:
        raise HTTPException(status_code=400, detail="Link expirado. Solicite um novo.")

    # Marca token como usado (idempotente via unique constraint)
    sb.table("email_confirm_tokens").update({"used": True}).eq("id", record["id"]).execute()

    # Confirma email do membro
    sb.table("members").update({"email_confirmed": True}).eq(
        "id", record["member_id"]
    ).execute()

    # Audit log
    try:
        sb.table("audit_logs").insert({
            "actor_type":  "member",
            "actor_id":    record["member_id"],
            "action":      "member.email_confirmed",
            "target_type": "member",
            "target_id":   record["member_id"],
        }).execute()
    except Exception as exc:
        log.warning(f"Audit log falhou: {exc}")

    log.info(f"Email confirmado para membro {record['member_id']}")
    return {"message": "Email confirmado com sucesso!", "confirmed": True}
