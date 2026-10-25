# ============================================================
#  services/email_service.py — Clube USA
#  Abstração para envio de email transacional.
#
#  Em dev (sem RESEND_API_KEY): loga o link de confirmação.
#  Em produção: chama a API Resend (resend.com).
#
#  Para usar outro provedor no futuro, implemente _send_via_smtp()
#  ou _send_via_sendgrid() e altere _dispatch().
# ============================================================

import os
import logging
import json
import urllib.request
import urllib.error

log = logging.getLogger("email_service")

APP_URL      = os.environ.get("APP_URL", "https://clubeusa.com")
FROM_EMAIL   = os.environ.get("EMAIL_FROM", "noreply@clubeusa.com")
FROM_NAME    = os.environ.get("EMAIL_FROM_NAME", "Clube USA")


# ============================================================
#  TEMPLATES
# ============================================================

def _html_confirm_email(name: str, confirm_url: str) -> str:
    first = name.split()[0] if name else "membro"
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><title>Confirme seu email</title></head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;margin:0;padding:20px">
  <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden">
    <div style="background:#1a56db;padding:24px 32px">
      <h1 style="color:#fff;margin:0;font-size:22px">🇺🇸 Clube USA</h1>
    </div>
    <div style="padding:32px">
      <h2 style="color:#111;font-size:20px;margin-top:0">Olá, {first}!</h2>
      <p style="color:#444;line-height:1.6">
        Obrigado por se cadastrar no <strong>Clube USA</strong> — a plataforma para brasileiros nos EUA.
        Clique no botão abaixo para confirmar seu email e ativar sua conta.
      </p>
      <div style="text-align:center;margin:32px 0">
        <a href="{confirm_url}"
           style="background:#1a56db;color:#fff;padding:14px 32px;border-radius:6px;
                  text-decoration:none;font-size:16px;font-weight:bold;display:inline-block">
          Confirmar meu email
        </a>
      </div>
      <p style="color:#888;font-size:13px">
        Este link expira em 24 horas.<br>
        Se você não se cadastrou no Clube USA, ignore este email.
      </p>
      <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
      <p style="color:#aaa;font-size:12px;text-align:center">
        Clube USA · Para brasileiros nos EUA
      </p>
    </div>
  </div>
</body>
</html>
""".strip()


def _text_confirm_email(name: str, confirm_url: str) -> str:
    first = name.split()[0] if name else "membro"
    return (
        f"Olá, {first}!\n\n"
        f"Confirme seu email no Clube USA clicando no link abaixo:\n\n"
        f"{confirm_url}\n\n"
        f"Este link expira em 24 horas.\n"
        f"Se você não se cadastrou, ignore este email.\n\n"
        f"-- Clube USA"
    )


# ============================================================
#  PROVEDORES
# ============================================================

def _send_via_resend(to_email: str, subject: str, html: str, text: str) -> None:
    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key:
        raise RuntimeError("RESEND_API_KEY nao configurado.")

    payload = json.dumps({
        "from":    f"{FROM_NAME} <{FROM_EMAIL}>",
        "to":      [to_email],
        "subject": subject,
        "html":    html,
        "text":    text,
    }).encode()

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status not in (200, 201):
                raise RuntimeError(f"Resend retornou HTTP {resp.status}")
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"Resend erro {e.code}: {body}") from e


def _dispatch(to_email: str, subject: str, html: str, text: str) -> None:
    """Escolhe provedor baseado em env vars."""
    if os.environ.get("RESEND_API_KEY"):
        _send_via_resend(to_email, subject, html, text)
    else:
        # Modo dev: loga ao invés de enviar
        log.info(
            f"[EMAIL DEV] Para: {to_email} | Assunto: {subject}\n"
            f"  Texto: {text[:200]}..."
        )


# ============================================================
#  FUNÇÕES PÚBLICAS
# ============================================================

def send_confirmation_email(to_email: str, name: str, token: str) -> None:
    """
    Envia email de confirmação de cadastro.
    Em dev (sem RESEND_API_KEY), apenas loga o link.
    """
    confirm_url = f"{APP_URL}/verify-email?token={token}"
    subject = "✅ Confirme seu email — Clube USA"
    html = _html_confirm_email(name or "", confirm_url)
    text = _text_confirm_email(name or "", confirm_url)
    try:
        _dispatch(to_email, subject, html, text)
        log.info(f"Email de confirmação enviado para {to_email[:4]}***")
    except Exception as e:
        # Nunca bloqueia o cadastro por falha de email
        log.error(f"Falha ao enviar email de confirmação: {e}")
        raise
