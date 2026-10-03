# ============================================================
#  routers/email_confirmation.py — Clube USA
#  Confirmacao de email: envia token, valida clique no link
# ============================================================

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse

from deps import get_current_member

router = APIRouter(tags=["email"])

APP_URL = os.environ.get("APP_URL", "https://clubeusa.com")
TOKEN_TTL_HOURS = 24


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def _page(status: str, title: str, body: str) -> str:
    color = {"sucesso": "#22c55e", "erro": "#ef4444", "info": "#3b82f6"}.get(status, "#3b82f6")
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} — Clube USA</title>
  <style>
    body {{ font-family: system-ui, sans-serif; background: #0f172a; color: #f1f5f9;
            display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }}
    .card {{ background: #1e293b; border-radius: 12px; padding: 2.5rem; max-width: 420px;
             width: 90%; text-align: center; border-top: 4px solid {color}; }}
    h1 {{ color: {color}; font-size: 1.5rem; margin-bottom: 1rem; }}
    p  {{ color: #94a3b8; line-height: 1.6; }}
    a  {{ display: inline-block; margin-top: 1.5rem; padding: .75rem 2rem;
          background: {color}; color: white; border-radius: 8px;
          text-decoration: none; font-weight: 600; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>{title}</h1>
    <p>{body}</p>
    <a href="{APP_URL}/painel">Ir ao painel</a>
  </div>
</body>
</html>"""


@router.post("/auth/email/send-confirmation")
async def send_email_confirmation(member: dict = Depends(get_current_member)):
    """Envia (ou reenvia) email de confirmacao para o membro autenticado."""
    sb = _supabase()
    member_id = member["sub"]

    result = sb.table("members").select(
        "id,email_enc,email_confirmed,name_enc"
    ).eq("id", member_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Membro nao encontrado.")

    m = result.data[0]
    if not m.get("email_enc"):
        raise HTTPException(status_code=400, detail="Nenhum email cadastrado.")

    if m.get("email_confirmed"):
        raise HTTPException(status_code=400, detail="Email ja confirmado.")

    # Invalida tokens anteriores deste membro
    sb.table("email_confirmation_tokens").update(
        {"used_at": datetime.now(timezone.utc).isoformat()}
    ).eq("member_id", member_id).is_("used_at", "null").execute()

    # Cria novo token — armazena apenas o HASH
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=TOKEN_TTL_HOURS)).isoformat()

    sb.table("email_confirmation_tokens").insert({
        "member_id":  member_id,
        "token_hash": token_hash,
        "expires_at": expires_at,
    }).execute()

    confirm_url = f"{APP_URL}/auth/email/confirm/{raw_token}"

    # Descriptografa para enviar email
    from utils.security import decrypt
    email = decrypt(m["email_enc"])
    name  = decrypt(m["name_enc"]) if m.get("name_enc") else "Membro"

    from services.email_service import send_confirmation_email
    send_confirmation_email(email, name, confirm_url)

    # Retorna email mascarado (privacidade)
    local, domain = email.split("@", 1)
    masked = local[:2] + "*" * max(0, len(local) - 2) + "@" + domain

    return {"message": "Email de confirmacao enviado.", "email": masked}


@router.get("/auth/email/confirm/{token}", response_class=HTMLResponse, include_in_schema=False)
async def confirm_email(token: str):
    """Link clicado pelo usuario no email de confirmacao."""
    if not token or len(token) > 200:
        return HTMLResponse(
            _page("erro", "Link invalido", "O link de confirmacao e invalido ou expirou."),
            status_code=400
        )

    token_hash = _hash_token(token)
    sb = _supabase()
    now = datetime.now(timezone.utc)

    result = sb.table("email_confirmation_tokens").select(
        "id,member_id,expires_at,used_at"
    ).eq("token_hash", token_hash).execute()

    if not result.data:
        return HTMLResponse(
            _page("erro", "Link invalido", "Este link de confirmacao nao e valido."),
            status_code=400
        )

    rec = result.data[0]

    if rec.get("used_at"):
        return HTMLResponse(
            _page("info", "Ja confirmado", "Este link ja foi utilizado. Seu email esta confirmado."),
            status_code=200
        )

    expires = datetime.fromisoformat(rec["expires_at"].replace("Z", "+00:00"))
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if now > expires:
        return HTMLResponse(
            _page("erro", "Link expirado", "Este link expirou. Solicite um novo no painel."),
            status_code=400
        )

    # Confirma email
    member_id = rec["member_id"]
    sb.table("members").update({
        "email_confirmed":    True,
        "email_confirmed_at": now.isoformat(),
    }).eq("id", member_id).execute()

    # Marca token como usado (auditoria)
    sb.table("email_confirmation_tokens").update(
        {"used_at": now.isoformat()}
    ).eq("id", rec["id"]).execute()

    # Audit log
    sb.table("audit_logs").insert({
        "actor_type":  "member",
        "actor_id":    member_id,
        "action":      "member.email_confirmed",
        "target_type": "member",
        "target_id":   member_id,
        "metadata":    {},
    }).execute()

    return HTMLResponse(
        _page("sucesso", "Email confirmado!", "Seu email foi confirmado com sucesso. Bem-vindo ao Clube USA!"),
        status_code=200
    )
