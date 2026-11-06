# ============================================================
#  services/email_service.py — Clube USA
#  Envio de emails transacionais com fallback para console (dev).
#
#  Em producao: configurar SMTP_HOST, SMTP_PORT, SMTP_USER,
#  SMTP_PASS, EMAIL_FROM no .env.
#  Em dev (env vars ausentes): loga o email no console.
# ============================================================

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

log = logging.getLogger("email_service")

APP_URL   = os.environ.get("APP_URL", "https://clubeusa.com")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "noreply@clubeusa.com")


def _smtp_configured() -> bool:
    return bool(os.environ.get("SMTP_HOST") and os.environ.get("SMTP_USER"))


def _send_smtp(to: str, subject: str, html: str, text: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = EMAIL_FROM
    msg["To"]      = to
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html",  "utf-8"))

    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ["SMTP_USER"]
    pw   = os.environ.get("SMTP_PASS", "")

    with smtplib.SMTP(host, port, timeout=15) as s:
        s.ehlo()
        s.starttls()
        s.login(user, pw)
        s.sendmail(EMAIL_FROM, [to], msg.as_string())


def send_email_verification(to: str, token: str, language: str = "pt") -> None:
    """
    Envia email com link de verificacao.
    Em dev (sem SMTP configurado) apenas loga o link.
    """
    verify_url = f"{APP_URL}/auth/email/verify/{token}"

    subjects = {
        "pt": "Confirme seu email — Clube USA",
        "es": "Confirma tu email — Club USA",
    }
    texts = {
        "pt": (
            f"Clube USA — Confirmacao de email\n\n"
            f"Clique no link abaixo para confirmar seu email:\n{verify_url}\n\n"
            "O link expira em 24 horas.\n\n"
            "Se nao solicitou, ignore este email."
        ),
        "es": (
            f"Club USA — Confirmacion de email\n\n"
            f"Haz clic en el siguiente enlace para confirmar tu email:\n{verify_url}\n\n"
            "El enlace expira en 24 horas.\n\n"
            "Si no lo solicitaste, ignora este correo."
        ),
    }
    htmls = {
        "pt": f"""<!DOCTYPE html>
<html lang="pt">
<body style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:24px">
<img src="{APP_URL}/assets/logo.png" alt="Clube USA" height="40" style="margin-bottom:16px">
<h2 style="color:#1a56db">Confirme seu email</h2>
<p>Clique no botao abaixo para confirmar seu endereco de email e ativar sua conta.</p>
<a href="{verify_url}"
   style="display:inline-block;background:#1a56db;color:#fff;padding:12px 24px;
          border-radius:6px;text-decoration:none;font-weight:bold;margin:16px 0">
  Confirmar email
</a>
<p style="color:#666;font-size:13px">O link expira em 24 horas.<br>
Se nao solicitou, ignore este email.</p>
<hr style="border:none;border-top:1px solid #eee">
<p style="color:#999;font-size:12px">Clube USA &mdash; Comunidade brasileira nos EUA</p>
</body></html>""",
        "es": f"""<!DOCTYPE html>
<html lang="es">
<body style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:24px">
<img src="{APP_URL}/assets/logo.png" alt="Club USA" height="40" style="margin-bottom:16px">
<h2 style="color:#1a56db">Confirma tu email</h2>
<p>Haz clic en el boton de abajo para confirmar tu email y activar tu cuenta.</p>
<a href="{verify_url}"
   style="display:inline-block;background:#1a56db;color:#fff;padding:12px 24px;
          border-radius:6px;text-decoration:none;font-weight:bold;margin:16px 0">
  Confirmar email
</a>
<p style="color:#666;font-size:13px">El enlace expira en 24 horas.<br>
Si no lo solicitaste, ignora este correo.</p>
<hr style="border:none;border-top:1px solid #eee">
<p style="color:#999;font-size:12px">Club USA &mdash; Comunidad brasilena en EE.UU.</p>
</body></html>""",
    }

    lang = language if language in ("pt", "es") else "pt"
    subject = subjects[lang]
    html    = htmls[lang]
    text    = texts[lang]

    if _smtp_configured() and os.environ.get("ENVIRONMENT") == "production":
        try:
            _send_smtp(to, subject, html, text)
            log.info(f"Email de verificacao enviado para {to[:3]}***")
        except Exception as e:
            log.error(f"Falha ao enviar email de verificacao: {e}")
            raise
    else:
        log.info(
            f"[DEV] Email de verificacao para {to[:3]}***  |  "
            f"Link: {verify_url}"
        )
