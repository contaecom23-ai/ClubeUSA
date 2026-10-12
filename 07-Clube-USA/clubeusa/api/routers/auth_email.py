# ============================================================
#  routers/auth_email.py — Clube USA
#  Endpoints de verificacao de email
#
#  POST /auth/email/verify/request  — solicita envio do link (autenticado)
#  GET  /auth/email/verify/{token}  — confirma email via link (publico)
# ============================================================

import os
import secrets
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse

from deps import get_current_member

log = logging.getLogger("auth_email")
router = APIRouter(tags=["auth"])

_TOKEN_TTL_HOURS = 24


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


@router.post("/auth/email/verify/request", status_code=200)
async def request_email_verification(member: dict = Depends(get_current_member)):
    """
    Envia (ou reenvio) link de verificacao de email para o membro autenticado.
    Requer que o membro tenha um email cadastrado.
    Nao expoe se o email ja esta confirmado (retorna mesmo resultado).
    """
    sb = _supabase()
    result = sb.table("members").select(
        "id,email_enc,email_confirmed,language"
    ).eq("id", member["sub"]).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Membro nao encontrado.")

    m = result.data[0]

    if not m.get("email_enc"):
        raise HTTPException(status_code=400, detail="Nenhum email cadastrado. Atualize seu perfil primeiro.")

    if m.get("email_confirmed"):
        return {"message": "Email ja confirmado.", "already_confirmed": True}

    # Gera token seguro e TTL
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=_TOKEN_TTL_HOURS)).isoformat()

    sb.table("members").update({
        "email_verification_token": token,
        "email_token_expires_at":   expires_at,
    }).eq("id", member["sub"]).execute()

    # Descriptografa email para enviar (nunca logado)
    from utils.security import decrypt
    try:
        email = decrypt(m["email_enc"])
    except Exception:
        raise HTTPException(status_code=500, detail="Erro ao processar email.")

    from services.email_service import send_verification_email
    send_verification_email(email, token, m.get("language", "pt"))

    return {
        "message": "Link de verificacao enviado para seu email.",
        "expires_in_hours": _TOKEN_TTL_HOURS,
    }


@router.get("/auth/email/verify/{token}", response_class=HTMLResponse, include_in_schema=False)
async def confirm_email(token: str):
    """
    Confirma o email via link clicado.
    Rota publica — chamada diretamente pelo link no email.
    Retorna pagina HTML simples (sucesso ou erro).
    """
    if not token or len(token) > 100:
        return _html_result(success=False, language="pt")

    sb = _supabase()
    result = sb.table("members").select(
        "id,email_token_expires_at,email_confirmed,language"
    ).eq("email_verification_token", token).execute()

    if not result.data:
        return _html_result(success=False, language="pt")

    m = result.data[0]
    language = m.get("language", "pt")

    if m.get("email_confirmed"):
        return _html_result(success=True, language=language, already=True)

    # Verifica TTL
    expires_raw = m.get("email_token_expires_at")
    if not expires_raw:
        return _html_result(success=False, language=language)

    expires = datetime.fromisoformat(expires_raw.replace("Z", "+00:00"))
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires:
        return _html_result(success=False, language=language, expired=True)

    # Confirma email e limpa token
    sb.table("members").update({
        "email_confirmed":           True,
        "email_verification_token":  None,
        "email_token_expires_at":    None,
    }).eq("id", m["id"]).execute()

    # Audit log
    sb.table("audit_logs").insert({
        "actor_id":    m["id"],
        "actor_type":  "member",
        "action":      "member.email_confirmed",
        "target_type": "member",
        "target_id":   m["id"],
    }).execute()

    log.info(f"Email confirmado para membro {m['id']}")
    return _html_result(success=True, language=language)


def _html_result(success: bool, language: str = "pt", already: bool = False, expired: bool = False) -> str:
    app_url = os.environ.get("APP_URL", "https://clubeusa.com")

    if language == "es":
        if success and already:
            title, msg, color = "Correo ya confirmado", "Tu correo electronico ya fue confirmado anteriormente.", "#1a56a0"
        elif success:
            title, msg, color = "Correo confirmado!", "Tu correo electronico fue confirmado exitosamente. Ya puedes cerrar esta pagina.", "#1a7a4a"
        elif expired:
            title, msg, color = "Enlace expirado", "Este enlace de confirmacion ya no es valido. Solicita uno nuevo desde tu perfil.", "#c0392b"
        else:
            title, msg, color = "Enlace invalido", "Este enlace de confirmacion es invalido o ya fue utilizado.", "#c0392b"
        btn_label = "Ir al inicio"
    else:
        if success and already:
            title, msg, color = "Email ja confirmado", "Seu email ja foi confirmado anteriormente.", "#1a56a0"
        elif success:
            title, msg, color = "Email confirmado!", "Seu email foi confirmado com sucesso. Voce ja pode fechar esta pagina.", "#1a7a4a"
        elif expired:
            title, msg, color = "Link expirado", "Este link de confirmacao nao e mais valido. Solicite um novo pelo seu perfil.", "#c0392b"
        else:
            title, msg, color = "Link invalido", "Este link de confirmacao e invalido ou ja foi utilizado.", "#c0392b"
        btn_label = "Ir ao inicio"

    return f"""<!DOCTYPE html>
<html lang="{language}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{title} — Clube USA</title>
  <style>
    body{{font-family:Arial,sans-serif;display:flex;align-items:center;justify-content:center;
         min-height:100vh;margin:0;background:#f5f7fa}}
    .card{{background:#fff;border-radius:12px;padding:40px;max-width:400px;width:90%;
           text-align:center;box-shadow:0 2px 16px rgba(0,0,0,.1)}}
    .icon{{font-size:48px;margin-bottom:16px}}
    h1{{color:{color};font-size:24px;margin:0 0 12px}}
    p{{color:#555;line-height:1.5;margin:0 0 24px}}
    a{{display:inline-block;background:#1a56a0;color:#fff;padding:12px 24px;
       border-radius:6px;text-decoration:none;font-weight:bold}}
    a:hover{{background:#154080}}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">{"✅" if success else "❌"}</div>
    <h1>{title}</h1>
    <p>{msg}</p>
    <a href="{app_url}">{btn_label}</a>
  </div>
</body>
</html>"""
