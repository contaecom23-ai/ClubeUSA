# ============================================================
#  services/email_service.py — Clube USA
#  Confirmacao de email — Fase 0.1
#
#  Padrao OTP: em dev loga o link, em producao usa EMAIL_PROVIDER.
#  Provedores suportados: resend | sendgrid (ver DECISOES.md)
# ============================================================

import os
import secrets
import logging
from datetime import datetime, timedelta, timezone

log = logging.getLogger("email_service")

_TOKEN_TTL_HOURS = 24


# ============================================================
#  UTILITARIOS
# ============================================================

def generate_email_token() -> str:
    """Token criptograficamente seguro, URL-safe, 43 caracteres aprox."""
    return secrets.token_urlsafe(32)


# ============================================================
#  SERVICOS
# ============================================================

def request_email_confirmation(member_id: str) -> dict:
    """
    Gera token de confirmacao e envia email.
    Raises ValueError para estados invalidos (sem email, ja confirmado, rate-limit).
    """
    sb = _supabase()
    result = sb.table("members").select(
        "email_enc,email_confirmed,email_token_expires_at"
    ).eq("id", member_id).execute()

    if not result.data:
        raise ValueError("Membro nao encontrado.")

    m = result.data[0]

    if not m.get("email_enc"):
        raise ValueError("Nenhum email cadastrado. Atualize seu perfil primeiro.")

    if m.get("email_confirmed"):
        raise ValueError("Email ja confirmado.")

    # Rate-limit: nao re-envia se token ainda vigente (janela 24h)
    if m.get("email_token_expires_at"):
        try:
            raw = m["email_token_expires_at"]
            expires = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) < expires:
                raise ValueError(
                    "Email de confirmacao ja enviado. Aguarde 24 horas para reenviar."
                )
        except ValueError:
            raise
        except Exception as e:
            log.warning(f"Erro ao checar expiracao do token de email: {e}")

    token = generate_email_token()
    expires_at = (datetime.utcnow() + timedelta(hours=_TOKEN_TTL_HOURS)).isoformat()

    sb.table("members").update({
        "email_token":            token,
        "email_token_expires_at": expires_at,
    }).eq("id", member_id).execute()

    email = _decrypt(m["email_enc"])
    send_confirmation_email(email, member_id, token)

    return {"message": "Email de confirmacao enviado.", "expires_in_hours": _TOKEN_TTL_HOURS}


def confirm_email_token(token: str) -> dict:
    """
    Valida token de confirmacao.
    Marca email como confirmado, concede 50 pontos, apaga o token.
    Raises ValueError se invalido ou expirado.
    """
    if not token or len(token) > 128:
        raise ValueError("Token invalido.")

    sb = _supabase()
    result = sb.table("members").select(
        "id,email_token,email_token_expires_at,email_confirmed"
    ).eq("email_token", token).execute()

    if not result.data:
        raise ValueError("Token invalido ou expirado.")

    m = result.data[0]

    if m.get("email_confirmed"):
        return {"message": "Email ja confirmado.", "points_awarded": 0}

    raw_exp = m.get("email_token_expires_at")
    if not raw_exp:
        raise ValueError("Token invalido ou expirado.")

    expires = datetime.fromisoformat(raw_exp.replace("Z", "+00:00"))
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires:
        raise ValueError("Token expirado. Solicite um novo link de confirmacao.")

    sb.table("members").update({
        "email_confirmed":        True,
        "email_token":            None,
        "email_token_expires_at": None,
    }).eq("id", m["id"]).execute()

    try:
        sb.rpc("increment_points", {"p_member_id": m["id"], "p_points": 50}).execute()
    except Exception as e:
        log.warning(f"Falha ao incrementar pontos apos confirmacao de email: {e}")

    try:
        sb.table("audit_logs").insert({
            "actor_type":  "member",
            "action":      "member.email_confirmed",
            "target_type": "member",
            "target_id":   m["id"],
        }).execute()
    except Exception as e:
        log.warning(f"Audit log falhou apos confirmacao de email: {e}")

    return {"message": "Email confirmado com sucesso!", "points_awarded": 50}


def update_member_email(member_id: str, new_email: str) -> dict:
    """
    Adiciona ou atualiza email do membro.
    Reseta confirmacao (novo email exige nova confirmacao).
    Raises ValueError se email invalido ou ja em uso por outro membro.
    """
    email = _validate_email(new_email)
    email_hash = _hash_pii(email)

    sb = _supabase()

    existing = sb.table("members").select("id").eq("email_hash", email_hash).execute()
    if existing.data and existing.data[0]["id"] != member_id:
        raise ValueError("Email ja em uso por outro membro.")

    sb.table("members").update({
        "email_hash":             email_hash,
        "email_enc":              _encrypt(email),
        "email_confirmed":        False,
        "email_token":            None,
        "email_token_expires_at": None,
    }).eq("id", member_id).execute()

    return {
        "message":        "Email atualizado. Confirme seu email para ativar.",
        "email_confirmed": False,
    }


# ============================================================
#  ENVIO DE EMAIL
# ============================================================

def send_confirmation_email(to_email: str, member_id: str, token: str) -> None:
    """
    Envia email de confirmacao.
    Dev: loga o link (nao envia). Producao: EMAIL_PROVIDER env var.
    """
    app_url = os.environ.get("APP_URL", "https://clubeusa.com")
    link = f"{app_url}/auth/email/confirm?token={token}"

    if os.environ.get("ENVIRONMENT") != "production":
        log.info(f"[DEV] Email de confirmacao | dest={to_email[:3]}*** | link={link}")
        return

    provider = os.environ.get("EMAIL_PROVIDER", "")
    if provider == "resend":
        _send_via_resend(to_email, link)
    elif provider == "sendgrid":
        _send_via_sendgrid(to_email, link)
    else:
        log.warning(
            f"EMAIL_PROVIDER nao configurado. "
            f"Configure 'resend' ou 'sendgrid' (ver DECISOES.md). "
            f"Link nao enviado para {to_email[:3]}***"
        )


def _send_via_resend(to_email: str, link: str) -> None:
    import requests as req
    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key:
        log.error("RESEND_API_KEY nao configurada. Defina a env var.")
        return
    try:
        resp = req.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization":  f"Bearer {api_key}",
                "Content-Type":   "application/json",
            },
            json={
                "from":    "Clube USA <no-reply@clubeusa.com>",
                "to":      [to_email],
                "subject": "Confirme seu email — Clube USA",
                "html":    _email_html(link),
            },
            timeout=10,
        )
        if resp.status_code not in (200, 201):
            log.error(f"Resend erro {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        log.error(f"Resend excecao: {e}")


def _send_via_sendgrid(to_email: str, link: str) -> None:
    import requests as req
    api_key = os.environ.get("SENDGRID_API_KEY", "")
    if not api_key:
        log.error("SENDGRID_API_KEY nao configurada. Defina a env var.")
        return
    try:
        resp = req.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type":  "application/json",
            },
            json={
                "personalizations": [{"to": [{"email": to_email}]}],
                "from":    {"email": "no-reply@clubeusa.com", "name": "Clube USA"},
                "subject": "Confirme seu email — Clube USA",
                "content": [{"type": "text/html", "value": _email_html(link)}],
            },
            timeout=10,
        )
        if resp.status_code not in (200, 202):
            log.error(f"SendGrid erro {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        log.error(f"SendGrid excecao: {e}")


def _email_html(link: str) -> str:
    import html
    safe_link = html.escape(link)
    return (
        "<div style='font-family:sans-serif;max-width:480px;margin:auto;padding:24px'>"
        "<h2 style='color:#1a6b3c'>Confirme seu email</h2>"
        "<p>Clique no bot&atilde;o abaixo para confirmar seu email no <b>Clube USA</b>:</p>"
        f"<a href='{safe_link}' style='display:inline-block;padding:12px 28px;"
        "background:#1a6b3c;color:#fff;border-radius:6px;"
        "text-decoration:none;font-weight:bold;font-size:16px'>"
        "Confirmar email"
        "</a>"
        "<p style='color:#666;font-size:12px;margin-top:24px'>"
        "Link v&aacute;lido por 24 horas.<br>"
        "Se n&atilde;o foi voc&ecirc;, ignore este email."
        "</p>"
        "</div>"
    )


# ============================================================
#  PRIVADO
# ============================================================

def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


# Wrappers lazyos para funcoes de criptografia — mockáveis em testes sem ativar a lib.
def _decrypt(text: str) -> str:
    from utils.security import decrypt
    return decrypt(text)


def _encrypt(text: str) -> str:
    from utils.security import encrypt
    return encrypt(text)


def _hash_pii(value: str) -> str:
    from utils.security import hash_pii
    return hash_pii(value)


def _validate_email(email: str) -> str:
    from utils.security import validate_email
    return validate_email(email)
