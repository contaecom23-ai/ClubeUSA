# ============================================================
#  services/email_service.py — Clube USA
#  Envio de emails transacionais (verificacao, notificacoes)
#
#  Env vars necessarias (producao):
#    SMTP_HOST      — ex: smtp.sendgrid.net
#    SMTP_PORT      — ex: 587
#    SMTP_USER      — ex: apikey
#    SMTP_PASSWORD  — chave SMTP do provedor
#    SMTP_FROM      — ex: noreply@clubeusa.com
#    APP_URL        — ex: https://clubeusa.com
#
#  Em dev (sem SMTP_HOST): apenas loga o link no console.
# ============================================================

import os
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

log = logging.getLogger("email_service")

APP_URL = os.environ.get("APP_URL", "https://clubeusa.com")


def send_verification_email(email: str, token: str, language: str = "pt") -> bool:
    """
    Envia email de verificacao com link de confirmacao.
    Retorna True se enviado (ou logado em dev), False em caso de erro.
    """
    verify_url = f"{APP_URL}/auth/email/verify/{token}"

    subject, body_html, body_text = _build_verification_content(language, verify_url)

    smtp_host = os.environ.get("SMTP_HOST", "")
    if not smtp_host:
        # Modo dev: apenas loga — nunca enviar dados reais para fora sem config
        log.info(f"[DEV] Email de verificacao para {email}: {verify_url}")
        return True

    return _send_smtp(email, subject, body_html, body_text)


def _build_verification_content(language: str, verify_url: str) -> tuple:
    if language == "es":
        subject = "Confirma tu correo — Club USA"
        body_text = (
            f"Confirma tu correo electronico en Club USA.\n\n"
            f"Haz clic en el siguiente enlace (valido 24 horas):\n{verify_url}\n\n"
            f"Si no te registraste en Club USA, ignora este mensaje."
        )
        body_html = f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><title>Confirma tu correo — Club USA</title></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px;color:#222">
  <h2 style="color:#1a56a0">Club USA</h2>
  <p>Hola! Para activar tu cuenta, confirma tu correo electronico.</p>
  <p style="margin:32px 0">
    <a href="{verify_url}"
       style="background:#1a56a0;color:#fff;padding:14px 28px;border-radius:6px;text-decoration:none;font-weight:bold">
      Confirmar correo
    </a>
  </p>
  <p style="color:#666;font-size:13px">Este enlace es valido por 24 horas.<br>
  Si no creaste una cuenta en Club USA, ignora este mensaje.</p>
  <hr style="border:none;border-top:1px solid #eee;margin:32px 0">
  <p style="color:#999;font-size:12px">Club USA — La comunidad para brasileños en EE.UU.</p>
</body></html>"""
    else:
        subject = "Confirme seu email — Clube USA"
        body_text = (
            f"Confirme seu email no Clube USA.\n\n"
            f"Clique no link abaixo (valido por 24 horas):\n{verify_url}\n\n"
            f"Se voce nao criou uma conta no Clube USA, ignore este email."
        )
        body_html = f"""<!DOCTYPE html>
<html lang="pt">
<head><meta charset="utf-8"><title>Confirme seu email — Clube USA</title></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px;color:#222">
  <h2 style="color:#1a56a0">Clube USA</h2>
  <p>Ola! Para ativar sua conta, confirme seu endereço de email.</p>
  <p style="margin:32px 0">
    <a href="{verify_url}"
       style="background:#1a56a0;color:#fff;padding:14px 28px;border-radius:6px;text-decoration:none;font-weight:bold">
      Confirmar email
    </a>
  </p>
  <p style="color:#666;font-size:13px">Este link e valido por 24 horas.<br>
  Se voce nao criou uma conta no Clube USA, ignore este email.</p>
  <hr style="border:none;border-top:1px solid #eee;margin:32px 0">
  <p style="color:#999;font-size:12px">Clube USA — A comunidade para brasileiros nos EUA</p>
</body></html>"""

    return subject, body_html, body_text


def _send_smtp(to_email: str, subject: str, body_html: str, body_text: str) -> bool:
    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASSWORD", "")
    from_addr = os.environ.get("SMTP_FROM", "noreply@clubeusa.com")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = from_addr
    msg["To"]      = to_email
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html",  "utf-8"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_addr, to_email, msg.as_string())
        log.info(f"Email de verificacao enviado para {to_email[:4]}***")
        return True
    except Exception as e:
        log.error(f"Falha ao enviar email: {e}")
        return False
