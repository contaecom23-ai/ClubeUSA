# services/email_service.py — Clube USA  Fase 0.1
# Envio de email transacional com suporte a SMTP e Resend.
# Em dev (EMAIL_PROVIDER ausente ou 'dev'), apenas loga no console.
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

from supabase import create_client

log = logging.getLogger("email_service")

TOKEN_TTL_HOURS = 48


def _sb():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def generate_confirmation_token(member_id: str) -> str:
    """Gera token de confirmacao no banco e retorna o valor raw.
    Invalida tokens pendentes anteriores do mesmo membro."""
    sb = _sb()
    sb.table("email_tokens").delete().eq("member_id", member_id).eq(
        "token_type", "email_confirm"
    ).is_("used_at", "null").execute()

    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=TOKEN_TTL_HOURS)).isoformat()
    sb.table("email_tokens").insert({
        "member_id":  member_id,
        "token":      token,
        "token_type": "email_confirm",
        "expires_at": expires_at,
    }).execute()
    return token


def verify_confirmation_token(token: str) -> str | None:
    """Verifica token. Se valido e nao usado, marca como usado, confirma email e retorna member_id.
    Retorna None se invalido, expirado ou ja usado."""
    sb = _sb()
    result = sb.table("email_tokens").select("*").eq("token", token).eq(
        "token_type", "email_confirm"
    ).is_("used_at", "null").execute()

    if not result.data:
        return None

    record = result.data[0]
    raw_expires = record["expires_at"].replace("Z", "+00:00")
    expires = datetime.fromisoformat(raw_expires)
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires:
        sb.table("email_tokens").delete().eq("id", record["id"]).execute()
        return None

    member_id = record["member_id"]
    now_iso = datetime.now(timezone.utc).isoformat()

    sb.table("email_tokens").update({"used_at": now_iso}).eq("id", record["id"]).execute()
    sb.table("members").update({"email_confirmed_at": now_iso}).eq("id", member_id).execute()
    return member_id


def send_confirmation_email(member_id: str, email: str, name: str | None = None) -> bool:
    """Gera token e envia email de confirmacao. Retorna True se enviado."""
    try:
        token = generate_confirmation_token(member_id)
        app_url = os.environ.get("APP_URL", "https://clubeusa.com")
        confirm_url = f"{app_url}/auth/email/confirm/{token}"
        display = name or "membro"
        _send(
            to_email  = email,
            subject   = "Confirme seu email — Clube USA",
            body_html = _build_html(display, confirm_url),
            body_text = (
                f"Ola, {display}!\n\n"
                f"Confirme seu email no Clube USA:\n{confirm_url}\n\n"
                f"Link valido por {TOKEN_TTL_HOURS} horas.\n\nClube USA"
            ),
        )
        log.info(f"Email de confirmacao enviado — membro {member_id}")
        return True
    except Exception as e:
        log.error(f"Falha ao enviar email de confirmacao para membro {member_id}: {e}")
        return False


def _send(to_email: str, subject: str, body_html: str, body_text: str) -> None:
    provider = os.environ.get("EMAIL_PROVIDER", "dev").lower()
    if provider == "smtp":
        _send_smtp(to_email, subject, body_html, body_text)
    elif provider == "resend":
        _send_resend(to_email, subject, body_html)
    else:
        log.info(f"[DEV EMAIL] To={to_email} | Subject={subject}")
        log.info(f"[DEV EMAIL] {body_text}")


def _send_smtp(to_email: str, subject: str, body_html: str, body_text: str) -> None:
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    host     = os.environ["EMAIL_SMTP_HOST"]
    port     = int(os.environ.get("EMAIL_SMTP_PORT", "587"))
    user     = os.environ["EMAIL_SMTP_USER"]
    password = os.environ["EMAIL_SMTP_PASS"]
    from_    = os.environ.get("EMAIL_FROM", user)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Clube USA <{from_}>"
    msg["To"]      = to_email
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))
    with smtplib.SMTP(host, port) as s:
        s.ehlo()
        s.starttls()
        s.login(user, password)
        s.sendmail(from_, to_email, msg.as_string())


def _send_resend(to_email: str, subject: str, body_html: str) -> None:
    import requests
    api_key  = os.environ["RESEND_API_KEY"]
    from_    = os.environ.get("EMAIL_FROM", "noreply@clubeusa.com")
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"from": f"Clube USA <{from_}>", "to": [to_email], "subject": subject, "html": body_html},
        timeout=10,
    )
    resp.raise_for_status()


def _build_html(name: str, confirm_url: str) -> str:
    return (
        '<!DOCTYPE html><html lang="pt-BR">'
        '<body style="font-family:sans-serif;max-width:560px;margin:auto;padding:24px">'
        '<h2 style="color:#1a56db">Confirme seu email &#8212; Clube USA</h2>'
        f'<p>Ol&#225;, <strong>{name}</strong>!</p>'
        '<p>Clique no bot&#227;o abaixo para confirmar seu endere&#231;o de email e ativar sua conta:</p>'
        f'<a href="{confirm_url}" style="display:inline-block;background:#1a56db;color:#fff;'
        'padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:bold">'
        'Confirmar email</a>'
        f'<p style="margin-top:24px;color:#666;font-size:13px">Ou copie e cole este link:<br>'
        f'<a href="{confirm_url}">{confirm_url}</a></p>'
        f'<p style="color:#999;font-size:12px">Link v&#225;lido por {TOKEN_TTL_HOURS} horas. '
        'Se voc&#234; n&#227;o criou uma conta no Clube USA, ignore este email.</p>'
        '</body></html>'
    )
