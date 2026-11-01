# ============================================================
#  services/email_service.py — Clube USA
#  Fase 0.1: confirmação de email
#
#  Fluxo:
#    1. request_email_verification(member_id, email)
#       → salva email no perfil (não confirmado)
#       → gera token seguro (32 bytes urlsafe)
#       → salva HASH SHA-256 com TTL 24h
#       → envia email (ou loga em dev)
#
#    2. confirm_email_token(token)
#       → verifica hash, expiração, single-use
#       → marca email_confirmed = True
#
#  Provedor: EMAIL_PROVIDER=sendgrid|smtp (ver DECISOES.md)
#  Dev: imprime link no log, retorna dev_token na resposta
# ============================================================

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

log = logging.getLogger("email_service")


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def request_email_verification(member_id: str, email: str) -> dict:
    """
    Inicia fluxo de confirmação de email.
    - Valida formato do email.
    - Garante unicidade entre membros.
    - Persiste email criptografado (não confirmado) no perfil.
    - Gera token seguro, salva hash, envia email.
    Retorna dict com 'sent' e (em dev) 'dev_token'.
    """
    from utils.security import validate_email, encrypt, hash_pii

    try:
        email = validate_email(email)
    except ValueError as e:
        raise ValueError(f"Email inválido: {e}")

    sb = _supabase()
    email_hash = hash_pii(email)

    # Unicidade: email não pode pertencer a outro membro
    conflict = (
        sb.table("members")
        .select("id")
        .eq("email_hash", email_hash)
        .neq("id", member_id)
        .execute()
    )
    if conflict.data:
        raise ValueError("Este email já está cadastrado em outra conta.")

    # Remove tokens anteriores do mesmo membro (anti-spam)
    sb.table("email_verification_tokens").delete().eq("member_id", member_id).execute()

    # Persiste email no perfil (email_confirmed permanece False até confirmação)
    sb.table("members").update({
        "email_hash":      email_hash,
        "email_enc":       encrypt(email),
        "email_confirmed": False,
    }).eq("id", member_id).execute()

    # Token: 32 bytes = 256 bits de entropia; armazenamos apenas o hash SHA-256
    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    sb.table("email_verification_tokens").insert({
        "member_id":  member_id,
        "token_hash": token_hash,
        "expires_at": expires_at.isoformat(),
    }).execute()

    verify_url = (
        f"{os.environ.get('APP_URL', 'https://clubeusa.com')}"
        f"/auth/email/verify?token={token}"
    )

    if os.environ.get("ENVIRONMENT") == "production":
        _send_email(email, verify_url)
        return {"sent": True, "detail": "Email de confirmação enviado. Verifique sua caixa de entrada."}
    else:
        log.info(f"[DEV] Confirmação de email para {email}: {verify_url}")
        return {
            "sent":      True,
            "detail":    "Email de confirmação enviado (dev: verifique o log do servidor).",
            "dev_token": token,
        }


def confirm_email_token(token: str) -> dict:
    """
    Verifica token e confirma o email do membro.
    Token é single-use e válido por 24h.
    Retorna {'confirmed': True, 'member_id': '...'}.
    """
    sb = _supabase()
    token_hash = _hash_token(token)

    result = (
        sb.table("email_verification_tokens")
        .select("*")
        .eq("token_hash", token_hash)
        .execute()
    )

    if not result.data:
        raise ValueError("Token inválido ou já utilizado.")

    record = result.data[0]

    if record["used"]:
        raise ValueError("Token já utilizado.")

    expires = datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00"))
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires:
        sb.table("email_verification_tokens").delete().eq("id", record["id"]).execute()
        raise ValueError("Token expirado. Solicite um novo link de confirmação.")

    # Marca como usado ANTES de confirmar (evita race condition em requests paralelos)
    sb.table("email_verification_tokens").update({"used": True}).eq("id", record["id"]).execute()

    # Confirma o email
    member_id = record["member_id"]
    sb.table("members").update({"email_confirmed": True}).eq("id", member_id).execute()

    try:
        sb.table("audit_logs").insert({
            "actor_type":  "member",
            "actor_id":    member_id,
            "action":      "member.email_confirmed",
            "target_type": "member",
            "target_id":   member_id,
            "metadata":    {},
        }).execute()
    except Exception as e:
        log.warning(f"Audit log falhou: {e}")

    return {"confirmed": True, "member_id": member_id}


def _send_email(to_email: str, verify_url: str):
    """
    Despacha o email de confirmação via provedor configurado.
    EMAIL_PROVIDER=sendgrid|smtp (ver DECISOES.md).
    Lança RuntimeError se provedor não configurado.
    """
    provider = os.environ.get("EMAIL_PROVIDER", "")
    subject   = "Confirme seu email — Clube USA"
    body_html = (
        "<p>Olá,</p>"
        "<p>Clique no link abaixo para confirmar seu email no <strong>Clube USA</strong>:</p>"
        f'<p><a href="{verify_url}">{verify_url}</a></p>'
        "<p>O link expira em <strong>24 horas</strong>.</p>"
        "<hr><p><small>Se você não solicitou isso, ignore este email.</small></p>"
    )
    body_text = f"Confirme seu email no Clube USA:\n{verify_url}\n\nLink válido por 24 horas."

    if provider == "sendgrid":
        _send_sendgrid(to_email, subject, body_html, body_text)
    elif provider == "smtp":
        _send_smtp(to_email, subject, body_html, body_text)
    else:
        raise RuntimeError(
            "EMAIL_PROVIDER não configurado. "
            "Defina como 'sendgrid' ou 'smtp'. Consulte DECISOES.md."
        )


def _send_sendgrid(to_email: str, subject: str, body_html: str, body_text: str):
    import requests
    api_key    = os.environ.get("SENDGRID_API_KEY", "")
    from_email = os.environ.get("EMAIL_FROM", "noreply@clubeusa.com")
    if not api_key:
        raise RuntimeError("SENDGRID_API_KEY não configurado.")
    resp = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
        },
        json={
            "personalizations": [{"to": [{"email": to_email}]}],
            "from":    {"email": from_email, "name": "Clube USA"},
            "subject": subject,
            "content": [
                {"type": "text/plain", "value": body_text},
                {"type": "text/html",  "value": body_html},
            ],
        },
        timeout=10,
    )
    if resp.status_code not in (200, 202):
        raise RuntimeError(f"Erro SendGrid {resp.status_code}: {resp.text[:200]}")


def _send_smtp(to_email: str, subject: str, body_html: str, body_text: str):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    smtp_host  = os.environ.get("SMTP_HOST", "")
    smtp_port  = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user  = os.environ.get("SMTP_USER", "")
    smtp_pass  = os.environ.get("SMTP_PASS", "")
    from_email = os.environ.get("EMAIL_FROM", smtp_user)

    if not smtp_host or not smtp_user:
        raise RuntimeError("SMTP_HOST/SMTP_USER não configurados.")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = from_email
    msg["To"]      = to_email
    msg.attach(MIMEText(body_text, "plain"))
    msg.attach(MIMEText(body_html, "html"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(from_email, [to_email], msg.as_string())
