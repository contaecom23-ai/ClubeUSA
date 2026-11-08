# ============================================================
#  services/email_service.py — Clube USA (Fase 0.1)
#  Verificacao de email: gera token, envia email, valida token.
# ============================================================

import os
import hashlib
import secrets
import logging
from datetime import datetime, timedelta, timezone
from utils.security import decrypt

log = logging.getLogger("email_service")

_TOKEN_TTL_HOURS = 24
_RATE_LIMIT_PER_HOUR = 3


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def _hash_token(raw: str) -> str:
    salt = os.environ.get("ENCRYPTION_KEY", "dev-only-salt")
    return hashlib.sha256(f"{salt}:email_verify:{raw}".encode()).hexdigest()


def request_verification(member_id: str, email_enc: str) -> dict:
    """
    Gera token de verificacao de 24h e envia por email.
    Rate-limit: max 3 tokens por hora por membro.

    Returns {"ok": True, "expires_in": 86400}
    Raises ValueError se rate-limit excedido.
    """
    sb = _supabase()

    # Rate limit: max 3 tokens não-usados na última hora
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    recent = (
        sb.table("email_verification_tokens")
        .select("id", count="exact")
        .eq("member_id", member_id)
        .gt("created_at", cutoff)
        .is_("used_at", None)
        .execute()
    )
    if (recent.count or 0) >= _RATE_LIMIT_PER_HOUR:
        raise ValueError("Muitas solicitacoes. Aguarde 1 hora e tente novamente.")

    # Invalida tokens anteriores não-usados do mesmo membro
    sb.table("email_verification_tokens").delete().eq(
        "member_id", member_id
    ).is_("used_at", None).execute()

    # Gera novo token criptograficamente seguro
    raw = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw)
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=_TOKEN_TTL_HOURS)).isoformat()

    sb.table("email_verification_tokens").insert({
        "member_id":  member_id,
        "token_hash": token_hash,
        "expires_at": expires_at,
    }).execute()

    # Descriptografa email só para envio (nunca persiste em texto puro)
    email = decrypt(email_enc)

    _send_verification_email(email, raw)

    return {"ok": True, "expires_in": _TOKEN_TTL_HOURS * 3600}


def verify_email_token(token_raw: str) -> dict:
    """
    Valida o token e marca email como verificado.
    Token unico: invalidado apos uso.

    Returns {"ok": True, "member_id": "..."}
    Raises ValueError se inválido/expirado/já usado.
    """
    if not token_raw or len(token_raw) > 64:
        raise ValueError("Token inválido.")

    token_hash = _hash_token(token_raw)
    sb = _supabase()

    result = (
        sb.table("email_verification_tokens")
        .select("*")
        .eq("token_hash", token_hash)
        .is_("used_at", None)
        .execute()
    )

    if not result.data:
        raise ValueError("Token inválido ou já utilizado.")

    record = result.data[0]

    # Verifica expiração
    expires_raw = record["expires_at"].replace("Z", "+00:00")
    expires = datetime.fromisoformat(expires_raw)
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires:
        sb.table("email_verification_tokens").delete().eq("id", record["id"]).execute()
        raise ValueError("Token expirado. Solicite um novo link de verificacao.")

    # Marca token como usado
    sb.table("email_verification_tokens").update({
        "used_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", record["id"]).execute()

    # Marca email como verificado
    sb.table("members").update({
        "email_verified": True
    }).eq("id", record["member_id"]).execute()

    log.info(f"Email verificado para membro {record['member_id']}")

    return {"ok": True, "member_id": record["member_id"]}


def _send_verification_email(email: str, token_raw: str) -> None:
    """Envia email de verificacao. Em dev loga o link; em prod usa SMTP."""
    app_url = os.environ.get("APP_URL", "https://clubeusa.com")
    verify_url = f"{app_url}/auth/email/verify?token={token_raw}"

    if os.environ.get("ENVIRONMENT") != "production":
        log.info(f"[DEV] Link de verificacao para {email}: {verify_url}")
        return

    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    smtp_from = os.environ.get("SMTP_FROM", "noreply@clubeusa.com")

    if not all([smtp_host, smtp_user, smtp_pass]):
        log.warning("SMTP nao configurado — email de verificacao nao enviado em producao.")
        return

    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Confirme seu email — Clube USA"
    msg["From"]    = smtp_from
    msg["To"]      = email

    body_txt = (
        f"Clube USA — Confirmação de Email\n\n"
        f"Clique no link abaixo para confirmar seu email:\n{verify_url}\n\n"
        f"Link válido por {_TOKEN_TTL_HOURS} horas.\n\n"
        f"Se você não criou uma conta no Clube USA, ignore este email."
    )
    body_html = (
        f"<html><body style='font-family:sans-serif;max-width:480px;margin:auto'>"
        f"<h2 style='color:#1e40af'>Clube USA — Confirme seu email</h2>"
        f"<p>Clique no botão abaixo para confirmar seu email:</p>"
        f"<a href='{verify_url}' style='background:#2563eb;color:#fff;padding:12px 24px;"
        f"text-decoration:none;border-radius:6px;display:inline-block;font-weight:bold'>"
        f"Confirmar email</a>"
        f"<p style='color:#6b7280;font-size:14px'>Ou copie e cole: {verify_url}</p>"
        f"<p style='color:#6b7280;font-size:12px'>Link válido por {_TOKEN_TTL_HOURS} horas. "
        f"Se não criou conta no Clube USA, ignore este email.</p>"
        f"</body></html>"
    )

    msg.attach(MIMEText(body_txt, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_from, email, msg.as_string())
        log.info(f"Email de verificacao enviado para {email[:3]}***")
    except Exception as e:
        log.error(f"Falha ao enviar email: {e}")
        raise
