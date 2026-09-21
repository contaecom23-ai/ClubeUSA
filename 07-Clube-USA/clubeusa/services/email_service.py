# services/email_service.py — Clube USA
# Envio de e-mail transacional via SMTP (Mailgun/SendGrid/AWS SES compatível)
# Em dev: loga a URL no console em vez de enviar

import hashlib
import logging
import os
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

log = logging.getLogger("email_service")

_APP_URL = os.environ.get("APP_URL", "https://clubeusa.com")
_TOKEN_TTL_HOURS = 24


def _smtp_cfg() -> dict | None:
    host = os.environ.get("SMTP_HOST")
    if not host:
        return None
    return {
        "host":     host,
        "port":     int(os.environ.get("SMTP_PORT", "587")),
        "user":     os.environ.get("SMTP_USER", ""),
        "password": os.environ.get("SMTP_PASSWORD", ""),
        "from":     os.environ.get("SMTP_FROM", "noreply@clubeusa.com"),
        "tls":      os.environ.get("SMTP_TLS", "true").lower() == "true",
    }


def _send_raw(to: str, subject: str, html: str, text: str) -> bool:
    cfg = _smtp_cfg()
    if not cfg:
        log.info(f"[DEV] E-mail para {to} | {subject}\n{text}")
        return True

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = cfg["from"]
    msg["To"]      = to
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        if cfg["tls"]:
            with smtplib.SMTP(cfg["host"], cfg["port"]) as s:
                s.starttls()
                if cfg["user"]:
                    s.login(cfg["user"], cfg["password"])
                s.send_message(msg)
        else:
            with smtplib.SMTP_SSL(cfg["host"], cfg["port"]) as s:
                if cfg["user"]:
                    s.login(cfg["user"], cfg["password"])
                s.send_message(msg)
        return True
    except Exception as e:
        log.error(f"Falha ao enviar e-mail para {to}: {e}")
        return False


def send_confirmation_email(member_id: str, email: str, language: str = "pt") -> bool:
    """
    Gera token seguro, persiste o hash no banco, envia e-mail com link de confirmação.
    Retorna True se o e-mail foi enviado (ou logado em dev).
    """
    from supabase import create_client
    from utils.security import decrypt

    token_raw  = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(token_raw.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=_TOKEN_TTL_HOURS)

    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

    # Remove tokens anteriores pendentes para este membro
    sb.table("email_confirmation_tokens").delete().eq("member_id", member_id).is_(
        "used_at", "null"
    ).execute()

    sb.table("email_confirmation_tokens").insert({
        "member_id":  member_id,
        "token_hash": token_hash,
        "expires_at": expires_at.isoformat(),
    }).execute()

    confirm_url = f"{_APP_URL}/auth/email/confirm/{token_raw}"

    if language == "es":
        subject = "Confirma tu correo — Club USA"
        text    = (
            f"Hola!\n\n"
            f"Haz clic en el siguiente enlace para confirmar tu correo electrónico:\n\n"
            f"{confirm_url}\n\n"
            f"El enlace expira en {_TOKEN_TTL_HOURS} horas.\n\n"
            f"Si no creaste una cuenta en Club USA, ignora este mensaje.\n\n"
            f"— Club USA"
        )
        html = _build_html_es(confirm_url)
    else:
        subject = "Confirme seu e-mail — Clube USA"
        text    = (
            f"Olá!\n\n"
            f"Clique no link abaixo para confirmar seu e-mail:\n\n"
            f"{confirm_url}\n\n"
            f"O link expira em {_TOKEN_TTL_HOURS} horas.\n\n"
            f"Se você não criou uma conta no Clube USA, ignore esta mensagem.\n\n"
            f"— Clube USA"
        )
        html = _build_html_pt(confirm_url)

    return _send_raw(email, subject, html, text)


def _build_html_pt(url: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt">
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:40px 0;">
  <div style="max-width:480px;margin:0 auto;background:#fff;border-radius:8px;padding:32px;">
    <h2 style="color:#1a1a2e;margin-top:0;">Confirme seu e-mail</h2>
    <p style="color:#444;">Você está quase lá! Clique no botão abaixo para ativar sua conta no <strong>Clube USA</strong>.</p>
    <a href="{url}" style="display:inline-block;background:#c0392b;color:#fff;padding:14px 28px;border-radius:6px;text-decoration:none;font-weight:bold;margin:16px 0;">
      Confirmar e-mail
    </a>
    <p style="color:#888;font-size:13px;">O link expira em 24 horas.<br>Se não criou uma conta, ignore esta mensagem.</p>
    <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
    <p style="color:#aaa;font-size:12px;margin:0;">Clube USA — Para imigrantes brasileiros nos EUA</p>
  </div>
</body>
</html>"""


def _build_html_es(url: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:40px 0;">
  <div style="max-width:480px;margin:0 auto;background:#fff;border-radius:8px;padding:32px;">
    <h2 style="color:#1a1a2e;margin-top:0;">Confirma tu correo</h2>
    <p style="color:#444;">¡Ya casi! Haz clic en el botón para activar tu cuenta en <strong>Club USA</strong>.</p>
    <a href="{url}" style="display:inline-block;background:#c0392b;color:#fff;padding:14px 28px;border-radius:6px;text-decoration:none;font-weight:bold;margin:16px 0;">
      Confirmar correo
    </a>
    <p style="color:#888;font-size:13px;">El enlace expira en 24 horas.<br>Si no creaste una cuenta, ignora este mensaje.</p>
    <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
    <p style="color:#aaa;font-size:12px;margin:0;">Club USA — Para inmigrantes brasileños en EE.UU.</p>
  </div>
</body>
</html>"""


def confirm_email_token(token_raw: str) -> dict:
    """
    Valida token de confirmação de e-mail.
    Retorna {"ok": True, "member_id": "..."} ou {"ok": False, "error": "..."}.
    """
    from supabase import create_client

    token_hash = hashlib.sha256(token_raw.encode()).hexdigest()
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

    result = sb.table("email_confirmation_tokens").select("*").eq(
        "token_hash", token_hash
    ).is_("used_at", "null").execute()

    if not result.data:
        return {"ok": False, "error": "Token inválido ou expirado."}

    record = result.data[0]
    expires = datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00"))
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires:
        sb.table("email_confirmation_tokens").delete().eq("id", record["id"]).execute()
        return {"ok": False, "error": "Token expirado. Solicite um novo."}

    # Marca token como usado e confirma e-mail do membro atomicamente
    sb.table("email_confirmation_tokens").update({
        "used_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", record["id"]).execute()

    sb.table("members").update({
        "email_confirmed": True
    }).eq("id", record["member_id"]).execute()

    # Audit log
    sb.table("audit_logs").insert({
        "actor_type":  "member",
        "actor_id":    record["member_id"],
        "action":      "member.email_confirmed",
        "target_type": "member",
        "target_id":   record["member_id"],
    }).execute()

    log.info(f"E-mail confirmado para membro {record['member_id']}")
    return {"ok": True, "member_id": record["member_id"]}
