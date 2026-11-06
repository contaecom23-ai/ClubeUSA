# ============================================================
#  api/routers/email_verification.py — Clube USA
#  Verificacao de email: solicitar e confirmar.
#
#  POST /auth/email/verify-request  — envia link (requer auth)
#  GET  /auth/email/verify/{token}  — confirma email (publico)
# ============================================================

import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from deps import get_current_member

log = logging.getLogger("email_verification")
router = APIRouter(prefix="/auth/email", tags=["email"])

APP_URL = os.environ.get("APP_URL", "https://clubeusa.com")
_TOKEN_TTL_HRS = 24


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


@router.post("/verify-request")
async def request_email_verification(member: dict = Depends(get_current_member)):
    """
    Envia (ou reenviar) email de verificacao para o email cadastrado.
    Requer autenticacao. Rate-limit herdado do middleware global.
    """
    sb = _supabase()
    result = sb.table("members").select(
        "email_enc,email_verified,language"
    ).eq("id", member["sub"]).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Membro nao encontrado.")

    m = result.data[0]

    if m.get("email_verified"):
        return {"message": "Email ja verificado.", "already_verified": True}

    if not m.get("email_enc"):
        raise HTTPException(
            status_code=400,
            detail="Nenhum email cadastrado. Atualize seu perfil primeiro.",
        )

    from utils.security import decrypt
    email    = decrypt(m["email_enc"])
    language = m.get("language", "pt")

    # Invalida tokens anteriores pendentes
    sb.table("email_verification_tokens").delete().eq(
        "member_id", member["sub"]
    ).is_("used_at", "null").execute()

    # Cria novo token
    token     = secrets.token_urlsafe(48)
    expires   = datetime.now(timezone.utc) + timedelta(hours=_TOKEN_TTL_HRS)

    sb.table("email_verification_tokens").insert({
        "member_id":  member["sub"],
        "token":      token,
        "expires_at": expires.isoformat(),
    }).execute()

    from services.email_service import send_email_verification
    send_email_verification(email, token, language)

    return {"message": "Email de verificacao enviado.", "expires_in_hours": _TOKEN_TTL_HRS}


@router.get("/verify/{token}", include_in_schema=False)
async def confirm_email(token: str):
    """
    Confirma email via link.
    Publico — redireciona para o frontend com status.
    """
    sb = _supabase()

    row = sb.table("email_verification_tokens").select(
        "id,member_id,expires_at,used_at"
    ).eq("token", token).execute()

    if not row.data:
        return RedirectResponse(f"{APP_URL}/?email_verify=invalid")

    record = row.data[0]

    if record.get("used_at"):
        return RedirectResponse(f"{APP_URL}/?email_verify=already_used")

    expires = datetime.fromisoformat(
        record["expires_at"].replace("Z", "+00:00")
    )
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires:
        return RedirectResponse(f"{APP_URL}/?email_verify=expired")

    # Marca token como usado
    sb.table("email_verification_tokens").update({
        "used_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", record["id"]).execute()

    # Marca email como verificado no membro
    sb.table("members").update({
        "email_verified":    True,
        "email_verified_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", record["member_id"]).execute()

    # Audit log
    try:
        sb.table("audit_logs").insert({
            "actor_type":  "member",
            "actor_id":    record["member_id"],
            "action":      "member.email_verified",
            "target_type": "member",
            "target_id":   record["member_id"],
        }).execute()
    except Exception as e:
        log.warning(f"Audit log falhou: {e}")

    log.info(f"Email verificado para membro {record['member_id']}")
    return RedirectResponse(f"{APP_URL}/?email_verify=success")
