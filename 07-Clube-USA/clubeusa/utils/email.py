# ============================================================
#  utils/email.py — Clube USA
#  Envio de email com abstração de provider.
#
#  Em dev (EMAIL_PROVIDER não configurado): loga o link.
#  Em prod: usa Resend (preferido) ou SMTP genérico.
#
#  Variáveis de ambiente:
#    EMAIL_PROVIDER   = "resend" | "smtp" | "" (dev/log)
#    RESEND_API_KEY   = re_...
#    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS  (para smtp)
#    EMAIL_FROM       = "Clube USA <noreply@clubeusa.com>"
#    APP_URL          = https://clubeusa.com
# ============================================================

import os
import logging
import hashlib
import secrets

log = logging.getLogger("email")

APP_URL   = os.environ.get("APP_URL", "https://clubeusa.com")
FROM_ADDR = os.environ.get("EMAIL_FROM", "Clube USA <noreply@clubeusa.com>")


def _hash_token(token: str) -> str:
    """SHA-256 do token — o que é salvo no banco."""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_confirm_token() -> tuple[str, str]:
    """
    Gera token de confirmação.
    Retorna (token_em_claro, hash_para_banco).
    O token em claro vai no link enviado ao usuário.
    """
    token = secrets.token_urlsafe(32)
    return token, _hash_token(token)


def verify_token_hash(token: str, token_hash: str) -> bool:
    """Compara token em claro com hash armazenado."""
    return hmac_compare(_hash_token(token), token_hash)


def hmac_compare(a: str, b: str) -> bool:
    """Comparação segura contra timing attack."""
    import hmac as _hmac
    return _hmac.compare_digest(a.encode(), b.encode())


def send_email_confirmation(email: str, member_id: str, token: str, language: str = "pt"):
    """
    Envia email de confirmação ao usuário.
    Dispatches para o provider configurado em EMAIL_PROVIDER.
    """
    confirm_url = f"{APP_URL}/auth/email/confirm?token={token}"
    subject, body_html, body_text = _build_confirm_message(confirm_url, language)

    provider = os.environ.get("EMAIL_PROVIDER", "").lower()

    if provider == "resend":
        _send_resend(to=email, subject=subject, html=body_html, text=body_text)
    elif provider == "smtp":
        _send_smtp(to=email, subject=subject, html=body_html, text=body_text)
    else:
        # Modo dev — apenas loga
        log.info(
            f"[DEV] Email de confirmação para {email} | membro {member_id} | "
            f"link: {confirm_url}"
        )


def _build_confirm_message(confirm_url: str, language: str) -> tuple[str, str, str]:
    if language == "es":
        subject = "Confirma tu email — Club USA"
        text = (
            f"Hola!\n\nConfirma tu email haciendo clic en el link:\n{confirm_url}\n\n"
            "El link expira en 24 horas.\n\nClub USA"
        )
        html = f"""
<div style="font-family:sans-serif;max-width:480px;margin:0 auto">
  <h2 style="color:#1a5fb4">Club USA</h2>
  <p>Hola! Confirma tu dirección de email haciendo clic en el botón abajo.</p>
  <p style="margin:32px 0">
    <a href="{confirm_url}"
       style="background:#1a5fb4;color:#fff;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:bold">
      Confirmar email
    </a>
  </p>
  <p style="color:#888;font-size:13px">El link expira en 24 horas. Si no solicitaste esto, ignora este mensaje.</p>
</div>"""
    else:
        subject = "Confirme seu email — Clube USA"
        text = (
            f"Oi!\n\nConfirme seu email clicando no link:\n{confirm_url}\n\n"
            "O link expira em 24 horas.\n\nClube USA"
        )
        html = f"""
<div style="font-family:sans-serif;max-width:480px;margin:0 auto">
  <h2 style="color:#1a5fb4">Clube USA</h2>
  <p>Oi! Confirme seu endereço de email clicando no botão abaixo.</p>
  <p style="margin:32px 0">
    <a href="{confirm_url}"
       style="background:#1a5fb4;color:#fff;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:bold">
      Confirmar email
    </a>
  </p>
  <p style="color:#888;font-size:13px">O link expira em 24 horas. Se você não solicitou isso, ignore esta mensagem.</p>
</div>"""

    return subject, html, text


def _send_resend(to: str, subject: str, html: str, text: str):
    import requests
    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key:
        log.error("RESEND_API_KEY não configurada.")
        return
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"from": FROM_ADDR, "to": [to], "subject": subject, "html": html, "text": text},
        timeout=10,
    )
    if resp.status_code not in (200, 201):
        log.error(f"Resend erro {resp.status_code}: {resp.text}")
    else:
        log.info(f"Email enviado via Resend para {to[:3]}***")


def _send_smtp(to: str, subject: str, html: str, text: str):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    host = os.environ.get("SMTP_HOST", "")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASS", "")

    if not host or not user:
        log.error("SMTP não configurado (SMTP_HOST, SMTP_USER, SMTP_PASS).")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = FROM_ADDR
    msg["To"] = to
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(FROM_ADDR, [to], msg.as_string())
        log.info(f"Email enviado via SMTP para {to[:3]}***")
    except Exception as e:
        log.error(f"SMTP erro: {e}")
