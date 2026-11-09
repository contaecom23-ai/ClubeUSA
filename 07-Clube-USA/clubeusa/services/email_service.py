"""
email_service.py — Clube USA  Fase 0.1

Envia emails transacionais via Resend (resend.com).
Resend foi escolhido como padrão por:
  - 3.000 emails/mês grátis (suficiente para ~1.000 usuários iniciais)
  - API minimalista (1 request HTTP)
  - Sem configuração de SMTP ou DNS complexo
  - Fácil trocar para SendGrid/SES no futuro (interface idêntica aqui)

REQUER: env var RESEND_API_KEY (ver .env.example)
"""

import os
import logging
import requests

log = logging.getLogger("email_service")

RESEND_API_KEY  = os.environ.get("RESEND_API_KEY", "")
EMAIL_FROM      = os.environ.get("EMAIL_FROM", "noreply@clubeusa.com")
APP_URL         = os.environ.get("APP_URL", "https://clubeusa.com")


def send_email_confirmation(to_email: str, member_name: str, token: str, language: str = "pt") -> bool:
    """
    Envia email com link de confirmação.
    Retorna True se enviado com sucesso.
    Em modo desenvolvimento (sem RESEND_API_KEY) loga o link e retorna True.
    """
    confirm_url = f"{APP_URL}/auth/email/confirm/{token}"

    if language == "es":
        subject = "Confirma tu correo en Club USA"
        html = _html_es(member_name or "Usuario", confirm_url)
        text = f"Hola {member_name or 'Usuario'},\n\nConfirma tu correo:\n{confirm_url}\n\nEl enlace expira en 24h."
    else:
        subject = "Confirme seu email no Clube USA"
        html = _html_pt(member_name or "Membro", confirm_url)
        text = f"Olá {member_name or 'Membro'},\n\nConfirme seu email:\n{confirm_url}\n\nO link expira em 24h."

    if not RESEND_API_KEY:
        log.info(f"[DEV] Email de confirmação para {to_email}: {confirm_url}")
        return True

    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type":  "application/json",
            },
            json={
                "from":    EMAIL_FROM,
                "to":      [to_email],
                "subject": subject,
                "html":    html,
                "text":    text,
            },
            timeout=10,
        )
        if resp.status_code in (200, 201):
            log.info(f"Email de confirmação enviado para {to_email[:4]}***")
            return True
        log.warning(f"Resend retornou {resp.status_code}: {resp.text[:200]}")
        return False
    except Exception as e:
        log.error(f"Falha ao enviar email de confirmação: {e}")
        return False


def _html_pt(name: str, url: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="font-family:Arial,sans-serif;background:#f4f4f4;margin:0;padding:20px;">
  <div style="max-width:520px;margin:auto;background:#fff;border-radius:8px;overflow:hidden;">
    <div style="background:#002B5C;padding:28px 32px;">
      <h1 style="color:#fff;margin:0;font-size:22px;">Clube USA</h1>
    </div>
    <div style="padding:32px;">
      <p style="font-size:16px;color:#333;">Olá, <strong>{name}</strong>!</p>
      <p style="font-size:15px;color:#555;">Clique no botão abaixo para confirmar seu email e ativar sua conta.</p>
      <div style="text-align:center;margin:32px 0;">
        <a href="{url}"
           style="background:#C0392B;color:#fff;padding:14px 36px;border-radius:6px;
                  text-decoration:none;font-size:15px;font-weight:bold;display:inline-block;">
          Confirmar meu email
        </a>
      </div>
      <p style="font-size:12px;color:#999;text-align:center;">
        O link expira em 24 horas.<br>
        Se você não criou uma conta, ignore este email.
      </p>
    </div>
  </div>
</body>
</html>"""


def _html_es(name: str, url: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="font-family:Arial,sans-serif;background:#f4f4f4;margin:0;padding:20px;">
  <div style="max-width:520px;margin:auto;background:#fff;border-radius:8px;overflow:hidden;">
    <div style="background:#002B5C;padding:28px 32px;">
      <h1 style="color:#fff;margin:0;font-size:22px;">Club USA</h1>
    </div>
    <div style="padding:32px;">
      <p style="font-size:16px;color:#333;">Hola, <strong>{name}</strong>!</p>
      <p style="font-size:15px;color:#555;">Haz clic en el botón para confirmar tu correo y activar tu cuenta.</p>
      <div style="text-align:center;margin:32px 0;">
        <a href="{url}"
           style="background:#C0392B;color:#fff;padding:14px 36px;border-radius:6px;
                  text-decoration:none;font-size:15px;font-weight:bold;display:inline-block;">
          Confirmar mi correo
        </a>
      </div>
      <p style="font-size:12px;color:#999;text-align:center;">
        El enlace expira en 24 horas.<br>
        Si no creaste una cuenta, ignora este correo.
      </p>
    </div>
  </div>
</body>
</html>"""
