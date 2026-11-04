# ============================================================
#  utils/email_sender.py — Clube USA
#  Envio de emails transacionais
#
#  Em producao: define RESEND_API_KEY no .env
#  Em dev: o token e logado (sem envio real)
#
#  Resend (resend.com) — free tier: 3.000 emails/mes
#  Sem dependencia extra: usa requests (ja no projeto)
# ============================================================

import os
import logging
import hashlib
import secrets
from datetime import datetime, timedelta

log = logging.getLogger("email_sender")

APP_URL   = os.environ.get("APP_URL", "https://clubeusa.com")
FROM_ADDR = os.environ.get("EMAIL_FROM", "Clube USA <noreply@clubeusa.com>")


def generate_email_token() -> tuple[str, str]:
    """
    Retorna (token_raw, token_hash).
    token_raw  → enviado ao usuario por email (nunca salvo no banco)
    token_hash → salvo no banco para comparacao
    """
    token_raw  = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token_raw.encode()).hexdigest()
    return token_raw, token_hash


def hash_token(token_raw: str) -> str:
    return hashlib.sha256(token_raw.encode()).hexdigest()


def send_confirmation_email(
    email: str,
    token_raw: str,
    name: str = "",
    language: str = "pt",
) -> bool:
    """
    Envia email de confirmacao.
    Retorna True se enviado (ou logado em dev), False em caso de falha real.
    """
    confirm_url = f"{APP_URL}/auth/email/confirm/{token_raw}"
    greeting    = name.split()[0] if name else "Membro"

    if language == "es":
        subject = "Confirma tu correo — Club USA"
        html = _html_es(greeting, confirm_url)
    else:
        subject = "Confirme seu email — Clube USA"
        html = _html_pt(greeting, confirm_url)

    api_key = os.environ.get("RESEND_API_KEY", "")

    if not api_key:
        # Dev mode: loga o token para testes manuais
        log.info(f"[DEV] Confirmar email para {email} → {confirm_url}")
        return True

    try:
        import requests
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from":    FROM_ADDR,
                "to":      [email],
                "subject": subject,
                "html":    html,
            },
            timeout=10,
        )
        resp.raise_for_status()
        log.info(f"Email confirmacao enviado para {email[:4]}***")
        return True
    except Exception as e:
        log.error(f"Falha ao enviar email de confirmacao: {e}")
        return False


# ---- templates HTML ----

def _html_pt(nome: str, url: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang="pt">
<head><meta charset="utf-8"><title>Clube USA</title></head>
<body style="font-family:sans-serif;max-width:600px;margin:40px auto;color:#222">
  <h2 style="color:#1a6fc4">Clube USA — Confirme seu email</h2>
  <p>Olá, <strong>{nome}</strong>!</p>
  <p>Clique no botão abaixo para confirmar seu endereço de email.
     O link expira em <strong>24 horas</strong>.</p>
  <p style="margin:32px 0">
    <a href="{url}"
       style="background:#1a6fc4;color:#fff;padding:14px 28px;
              border-radius:6px;text-decoration:none;font-size:16px">
      Confirmar email
    </a>
  </p>
  <p style="color:#888;font-size:13px">
    Se você não criou uma conta no Clube USA, ignore este email.
  </p>
</body>
</html>"""


def _html_es(nombre: str, url: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><title>Club USA</title></head>
<body style="font-family:sans-serif;max-width:600px;margin:40px auto;color:#222">
  <h2 style="color:#1a6fc4">Club USA — Confirma tu correo</h2>
  <p>Hola, <strong>{nombre}</strong>!</p>
  <p>Haz clic en el botón de abajo para confirmar tu dirección de correo.
     El enlace expira en <strong>24 horas</strong>.</p>
  <p style="margin:32px 0">
    <a href="{url}"
       style="background:#1a6fc4;color:#fff;padding:14px 28px;
              border-radius:6px;text-decoration:none;font-size:16px">
      Confirmar correo
    </a>
  </p>
  <p style="color:#888;font-size:13px">
    Si no creaste una cuenta en Club USA, ignora este correo.
  </p>
</body>
</html>"""
