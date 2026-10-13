# ============================================================
#  services/email_service.py — Clube USA
#  Envio de emails transacionais via SMTP
#
#  Configura via env vars (padrao: loga URL em dev se SMTP nao configurado):
#    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FROM_EMAIL
# ============================================================

import os
import logging
import secrets
import hashlib
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

_UTC = timezone.utc

log = logging.getLogger("email_service")

VERIFICATION_TTL_HRS = 24


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def _hash_token(token: str) -> str:
    """SHA-256 do token — nunca guardar token puro no banco."""
    return hashlib.sha256(token.encode()).hexdigest()


def _smtp_configured() -> bool:
    return bool(os.environ.get("SMTP_HOST") and os.environ.get("SMTP_USER"))


def _send_smtp(to_email: str, subject: str, html_body: str, text_body: str) -> bool:
    """Envia email via SMTP. Retorna True em sucesso."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = os.environ.get("FROM_EMAIL", os.environ["SMTP_USER"])
        msg["To"]      = to_email

        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        host = os.environ["SMTP_HOST"]
        port = int(os.environ.get("SMTP_PORT", "587"))
        user = os.environ["SMTP_USER"]
        pwd  = os.environ.get("SMTP_PASS", "")

        with smtplib.SMTP(host, port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(user, pwd)
            server.sendmail(msg["From"], [to_email], msg.as_string())

        return True
    except Exception as e:
        log.error(f"Falha ao enviar email para {to_email[:3]}***: {e}")
        return False


def send_verification_email(member_id: str, email: str) -> bool:
    """
    Gera token de verificacao, persiste no banco e envia email.
    Retorna True se email foi enviado (ou logado em dev).
    """
    sb = _supabase()

    # Invalida tokens anteriores para este membro (evita acumulo)
    sb.table("email_verification_tokens").delete().eq("member_id", member_id).execute()

    # Gera token criptograficamente seguro
    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    expires_at = (datetime.now(_UTC) + timedelta(hours=VERIFICATION_TTL_HRS)).isoformat()

    sb.table("email_verification_tokens").insert({
        "member_id":  member_id,
        "token_hash": token_hash,
        "expires_at": expires_at,
    }).execute()

    app_url = os.environ.get("APP_URL", "https://clubeusa.com")
    verify_url = f"{app_url}/auth/email/verify?token={token}"

    subject = "Confirme seu email — Clube USA"
    html_body = _build_verification_html(verify_url)
    text_body = (
        f"Clube USA — Confirmacao de Email\n\n"
        f"Clique no link abaixo para confirmar seu email (valido por {VERIFICATION_TTL_HRS}h):\n\n"
        f"{verify_url}\n\n"
        f"Se voce nao solicitou isto, ignore este email.\n"
    )

    if _smtp_configured():
        sent = _send_smtp(email, subject, html_body, text_body)
        if sent:
            log.info(f"Email de verificacao enviado para membro {member_id[:8]}...")
        return sent
    else:
        # Dev/staging: loga a URL para facilitar testes sem SMTP configurado
        log.info(
            f"[DEV] Email de verificacao NAO enviado (SMTP nao configurado). "
            f"URL: {verify_url}"
        )
        return True  # considera "enviado" para nao bloquear o fluxo de testes


def confirm_email_token(token: str) -> dict:
    """
    Verifica token e marca email como confirmado no membro.
    Retorna {"ok": True, "member_id": "..."} ou {"ok": False, "error": "..."}.
    """
    if not token or len(token) > 200:
        return {"ok": False, "error": "Token invalido."}

    token_hash = _hash_token(token)
    sb = _supabase()

    result = sb.table("email_verification_tokens").select(
        "id,member_id,expires_at"
    ).eq("token_hash", token_hash).execute()

    if not result.data:
        return {"ok": False, "error": "Token invalido ou ja utilizado."}

    row = result.data[0]

    # Verifica expiracao
    expires_at = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
    if datetime.now(_UTC) > expires_at:
        sb.table("email_verification_tokens").delete().eq("id", row["id"]).execute()
        return {"ok": False, "error": "Token expirado. Solicite um novo."}

    member_id = row["member_id"]

    # Marca email como confirmado
    sb.table("members").update({
        "email_confirmed_at": datetime.now(_UTC).isoformat(),
    }).eq("id", member_id).execute()

    # Deleta token (uso unico)
    sb.table("email_verification_tokens").delete().eq("id", row["id"]).execute()

    # Audit
    try:
        sb.table("audit_logs").insert({
            "actor_id":    member_id,
            "actor_type":  "member",
            "action":      "member.email_confirmed",
            "target_type": "member",
            "target_id":   member_id,
        }).execute()
    except Exception as e:
        log.warning(f"Audit log falhou: {e}")

    log.info(f"Email confirmado para membro {member_id[:8]}...")
    return {"ok": True, "member_id": member_id}


def _build_verification_html(verify_url: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt">
<head><meta charset="utf-8"><title>Confirme seu email</title></head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;padding:20px">
  <div style="max-width:480px;margin:0 auto;background:#fff;border-radius:8px;padding:32px">
    <h2 style="color:#1a56db;margin-top:0">🇧🇷 Clube USA</h2>
    <p>Olá! Confirme seu email para ativar sua conta no Clube USA.</p>
    <a href="{verify_url}"
       style="display:inline-block;background:#1a56db;color:#fff;padding:12px 24px;
              border-radius:6px;text-decoration:none;font-weight:bold;margin:16px 0">
      Confirmar meu email
    </a>
    <p style="color:#666;font-size:13px">
      Link válido por {VERIFICATION_TTL_HRS} horas.<br>
      Se você não solicitou isto, ignore este email.
    </p>
  </div>
</body>
</html>"""
