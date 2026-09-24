# ============================================================
#  api/routers/email_confirmation.py — Clube USA
#  Confirmação de email em dois passos:
#    POST /auth/email/send-confirmation — solicita envio (auth)
#    GET  /auth/email/confirm/{token}   — confirma (público, link no email)
# ============================================================

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse

from deps import get_current_member

log    = logging.getLogger("email_confirmation")
router = APIRouter(tags=["email"])

APP_URL = os.environ.get("APP_URL", "https://clubeusa.com")
TOKEN_TTL_HOURS = 24


def _sb():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


# ============================================================
#  POST /auth/email/send-confirmation
# ============================================================

@router.post("/auth/email/send-confirmation")
async def send_email_confirmation(member: dict = Depends(get_current_member)):
    """
    Envia (ou reenvio) email de confirmação para o membro autenticado.
    Requer que o membro tenha email cadastrado.
    Rate-limit herdado do middleware global (/auth = 5 req/min).
    """
    sb = _sb()
    row = sb.table("members").select(
        "id,email_enc,email_confirmed,name_enc"
    ).eq("id", member["sub"]).execute()

    if not row.data:
        raise HTTPException(status_code=404, detail="Membro nao encontrado.")

    m = row.data[0]

    if not m.get("email_enc"):
        raise HTTPException(
            status_code=400,
            detail="Nenhum email cadastrado. Atualize seu perfil primeiro.",
        )

    if m.get("email_confirmed"):
        return {"message": "Email ja confirmado."}

    from utils.security import decrypt
    email = decrypt(m["email_enc"])
    name  = decrypt(m["name_enc"]) if m.get("name_enc") else ""

    raw_token  = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=TOKEN_TTL_HOURS)).isoformat()

    # Invalida tokens anteriores do mesmo membro antes de criar novo
    sb.table("email_confirmation_tokens").delete().eq("member_id", member["sub"]).execute()

    sb.table("email_confirmation_tokens").insert({
        "member_id":  member["sub"],
        "token_hash": token_hash,
        "expires_at": expires_at,
    }).execute()

    confirm_url = f"{APP_URL}/auth/email/confirm/{raw_token}"

    from services.email_service import send_confirmation_email
    sent = send_confirmation_email(email, name, confirm_url)

    return {
        "message":         "Email de confirmacao enviado. Verifique sua caixa de entrada.",
        "email_masked":    _mask_email(email),
        "expires_in_hours": TOKEN_TTL_HOURS,
        "sent":            sent,
    }


# ============================================================
#  GET /auth/email/confirm/{token}
# ============================================================

@router.get("/auth/email/confirm/{token}", response_class=HTMLResponse, include_in_schema=False)
async def confirm_email(token: str):
    """
    Rota pública — usuário clica no link do email.
    Retorna HTML com resultado (sucesso, expirado, inválido).
    """
    if len(token) > 200:
        return _page("erro", "Link inválido.")

    sb         = _sb()
    token_hash = _hash_token(token)
    now        = datetime.now(timezone.utc)

    result = sb.table("email_confirmation_tokens").select(
        "id,member_id,expires_at,used_at"
    ).eq("token_hash", token_hash).execute()

    if not result.data:
        return _page("erro", "Link inválido ou expirado. Solicite um novo no painel.")

    rec = result.data[0]

    if rec.get("used_at"):
        return _page("info", "Este email já foi confirmado anteriormente.")

    expires = datetime.fromisoformat(rec["expires_at"].replace("Z", "+00:00"))
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if now > expires:
        sb.table("email_confirmation_tokens").delete().eq("id", rec["id"]).execute()
        return _page("erro", "Link expirado. Solicite um novo no seu painel.")

    # Confirma email
    sb.table("members").update({
        "email_confirmed":    True,
        "email_confirmed_at": now.isoformat(),
    }).eq("id", rec["member_id"]).execute()

    # Marca token como usado (mantém por rastreabilidade)
    sb.table("email_confirmation_tokens").update({
        "used_at": now.isoformat()
    }).eq("id", rec["id"]).execute()

    # Audit log
    try:
        sb.table("audit_logs").insert({
            "actor_type":  "member",
            "actor_id":    rec["member_id"],
            "action":      "member.email_confirmed",
            "target_type": "member",
            "target_id":   rec["member_id"],
        }).execute()
    except Exception as exc:
        log.warning("Audit log falhou em confirm_email: %s", exc)

    log.info("Email confirmado: membro %s", rec["member_id"])
    return _page("sucesso", "Email confirmado com sucesso! Você já pode fechar esta aba.")


# ============================================================
#  HELPERS
# ============================================================

def _mask_email(email: str) -> str:
    if "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        return email
    return local[:2] + "*" * (len(local) - 2) + "@" + domain


def _page(kind: str, message: str) -> str:
    colors = {"sucesso": "#16a34a", "erro": "#dc2626", "info": "#2563eb"}
    icons  = {"sucesso": "✅", "erro": "❌", "info": "ℹ️"}
    color  = colors.get(kind, "#374151")
    icon   = icons.get(kind, "")
    safe   = message.replace("<", "&lt;").replace(">", "&gt;")
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Clube USA — Confirmação de Email</title>
  <style>
    body{{font-family:Arial,sans-serif;display:flex;align-items:center;
          justify-content:center;min-height:100vh;margin:0;background:#f9fafb}}
    .card{{background:#fff;border-radius:12px;padding:40px 32px;
           max-width:400px;text-align:center;box-shadow:0 1px 8px rgba(0,0,0,.08)}}
    h2{{color:{color};margin:12px 0 8px}}
    p{{color:#4b5563;line-height:1.6}}
    a{{color:#1a56db;text-decoration:none}}
  </style>
</head>
<body>
  <div class="card">
    <div style="font-size:48px">{icon}</div>
    <h2>Clube USA</h2>
    <p>{safe}</p>
    <p style="margin-top:24px"><a href="/">Voltar para a plataforma →</a></p>
  </div>
</body>
</html>"""
