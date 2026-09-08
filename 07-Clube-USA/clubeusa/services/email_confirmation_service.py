# ============================================================
#  services/email_confirmation_service.py — Clube USA
#  Confirmacao de email (Fase 0.1)
#
#  Fluxo:
#    1. send_confirmation_email(member_id) — gera token, salva hash, envia email
#    2. verify_confirmation_token(token)   — valida hash, marca email_confirmed
#
#  Email real e enviado se SENDGRID_API_KEY ou SMTP_HOST estiver configurado.
#  Em dev (ENVIRONMENT != production), apenas loga o link.
# ============================================================

import os
import secrets
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from utils.security import decrypt, validate_email, encrypt, hash_pii

log = logging.getLogger("email_confirmation")

_TOKEN_TTL_HRS = 24
_APP_URL = os.environ.get("APP_URL", "https://clubeusa.com")


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# ============================================================
#  ENVIO
# ============================================================

def send_confirmation_email(member_id: str) -> dict:
    """
    Gera token de confirmacao, salva hash no banco e envia email ao membro.

    Retorna {"sent": True, "email_masked": "jo**@gmail.com"} em producao
    ou {"sent": False, "dev_link": "http://..."} em dev.

    Raises:
        ValueError — membro nao tem email cadastrado
        RuntimeError — falha ao salvar token
    """
    sb = _supabase()

    # Busca email criptografado do membro
    result = sb.table("members").select(
        "id, email_enc, email_hash, email_confirmed"
    ).eq("id", member_id).execute()

    if not result.data:
        raise ValueError("Membro nao encontrado.")

    member = result.data[0]

    if not member.get("email_enc"):
        raise ValueError("Nenhum email cadastrado. Adicione um email primeiro.")

    if member.get("email_confirmed"):
        return {"already_confirmed": True}

    # Descriptografa email para envio (nunca salvo em log)
    email = decrypt(member["email_enc"])

    # Gera token seguro de 32 bytes (URL-safe)
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=_TOKEN_TTL_HRS)).isoformat()

    # Invalida tokens anteriores nao usados do mesmo membro
    sb.table("email_confirmations").delete().eq(
        "member_id", member_id
    ).is_("used_at", "null").execute()

    # Salva novo token (apenas o hash — token raw nunca fica no banco)
    ins = sb.table("email_confirmations").insert({
        "member_id":  member_id,
        "token_hash": token_hash,
        "expires_at": expires_at,
    }).execute()

    if not ins.data:
        raise RuntimeError("Falha ao criar token de confirmacao.")

    confirm_url = f"{_APP_URL}/auth/email/confirm/{raw_token}"

    if os.environ.get("ENVIRONMENT") == "production":
        _send_email(email, confirm_url)
        return {
            "sent":         True,
            "email_masked": _mask_email_local(email),
            "expires_in_hrs": _TOKEN_TTL_HRS,
        }
    else:
        log.info(f"[DEV] Email confirmation link para {member_id}: {confirm_url}")
        return {
            "sent":         False,
            "dev_link":     confirm_url,
            "email_masked": _mask_email_local(email),
            "expires_in_hrs": _TOKEN_TTL_HRS,
        }


def verify_confirmation_token(token: str) -> dict:
    """
    Valida token de confirmacao e marca o email como confirmado.

    Retorna {"confirmed": True, "member_id": "..."}.
    Raises ValueError com mensagem amigavel em caso de falha.
    """
    if not token or len(token) > 200:
        raise ValueError("Token invalido.")

    token_hash = _hash_token(token)
    sb = _supabase()

    result = sb.table("email_confirmations").select("*").eq(
        "token_hash", token_hash
    ).is_("used_at", "null").execute()

    if not result.data:
        raise ValueError("Link de confirmacao invalido ou ja utilizado.")

    record = result.data[0]
    expires_at = datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00"))
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires_at:
        raise ValueError("Link de confirmacao expirado. Solicite um novo.")

    member_id = record["member_id"]
    now_iso = datetime.now(timezone.utc).isoformat()

    # Marca token como usado
    sb.table("email_confirmations").update({"used_at": now_iso}).eq(
        "id", record["id"]
    ).execute()

    # Marca email como confirmado no membro
    sb.table("members").update({
        "email_confirmed":    True,
        "email_confirmed_at": now_iso,
    }).eq("id", member_id).execute()

    # Audit
    try:
        sb.table("audit_logs").insert({
            "actor_type":  "member",
            "actor_id":    member_id,
            "action":      "member.email_confirmed",
            "target_type": "member",
            "target_id":   member_id,
        }).execute()
    except Exception as e:
        log.warning(f"Audit log falhou: {e}")

    log.info(f"Email confirmado para membro {member_id}")
    return {"confirmed": True, "member_id": member_id}


def add_or_update_email(member_id: str, new_email: str) -> dict:
    """
    Adiciona ou atualiza email de um membro (reseta confirmacao).
    Deve ser seguido de send_confirmation_email().
    """
    email = validate_email(new_email)
    sb = _supabase()

    # Verifica se email ja pertence a outro membro
    email_hash = hash_pii(email)
    existing = sb.table("members").select("id").eq(
        "email_hash", email_hash
    ).neq("id", member_id).execute()

    if existing.data:
        raise ValueError("Este email ja esta cadastrado em outra conta.")

    sb.table("members").update({
        "email_hash":      email_hash,
        "email_enc":       encrypt(email),
        "email_confirmed": False,
        "email_confirmed_at": None,
    }).eq("id", member_id).execute()

    # Invalida tokens antigos
    sb.table("email_confirmations").delete().eq(
        "member_id", member_id
    ).is_("used_at", "null").execute()

    return {"email_updated": True, "email_masked": _mask_email_local(email)}


# ============================================================
#  HELPERS INTERNOS
# ============================================================

def _mask_email_local(email: str) -> str:
    if "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        return email
    return local[:2] + "*" * (len(local) - 2) + "@" + domain


def _send_email(to_email: str, confirm_url: str):
    """
    Envia email de confirmacao.
    Suporta SendGrid (SENDGRID_API_KEY) ou SMTP (SMTP_HOST + SMTP_USER + SMTP_PASS).
    """
    subject = "Clube USA — Confirme seu email"
    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px">
      <h2 style="color:#1a56db">Clube USA</h2>
      <p>Clique no botao abaixo para confirmar seu email:</p>
      <a href="{confirm_url}"
         style="display:inline-block;background:#1a56db;color:#fff;
                padding:12px 24px;border-radius:6px;text-decoration:none;
                font-weight:bold;margin:16px 0">
        Confirmar email
      </a>
      <p style="color:#666;font-size:13px">
        Ou cole este link no navegador:<br>
        <a href="{confirm_url}" style="color:#1a56db">{confirm_url}</a>
      </p>
      <p style="color:#666;font-size:13px">
        Este link expira em {_TOKEN_TTL_HRS} horas.<br>
        Se voce nao se cadastrou no Clube USA, ignore este email.
      </p>
    </div>
    """

    sendgrid_key = os.environ.get("SENDGRID_API_KEY")
    if sendgrid_key:
        _send_via_sendgrid(sendgrid_key, to_email, subject, html_body)
        return

    smtp_host = os.environ.get("SMTP_HOST")
    if smtp_host:
        _send_via_smtp(smtp_host, to_email, subject, html_body)
        return

    # Nenhum provedor configurado — loga o link (nao deve acontecer em producao)
    log.error(
        "Nenhum provedor de email configurado (SENDGRID_API_KEY ou SMTP_HOST). "
        "Adicione ao .env para enviar emails reais."
    )
    log.info(f"[FALLBACK] Confirmation URL: {confirm_url}")


def _send_via_sendgrid(api_key: str, to_email: str, subject: str, html_body: str):
    import urllib.request, json as _json
    from_email = os.environ.get("EMAIL_FROM", "noreply@clubeusa.com")
    payload = _json.dumps({
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email, "name": "Clube USA"},
        "subject": subject,
        "content": [{"type": "text/html", "value": html_body}],
    }).encode()
    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status not in (200, 202):
                log.error(f"SendGrid retornou status {resp.status}")
    except Exception as e:
        log.error(f"Falha ao enviar via SendGrid: {e}")
        raise RuntimeError("Falha ao enviar email de confirmacao.")


def _send_via_smtp(host: str, to_email: str, subject: str, html_body: str):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASS", "")
    port = int(os.environ.get("SMTP_PORT", "587"))
    from_email = os.environ.get("EMAIL_FROM", user or "noreply@clubeusa.com")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Clube USA <{from_email}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(host, port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            if user and password:
                server.login(user, password)
            server.sendmail(from_email, [to_email], msg.as_string())
    except Exception as e:
        log.error(f"Falha ao enviar via SMTP: {e}")
        raise RuntimeError("Falha ao enviar email de confirmacao.")
