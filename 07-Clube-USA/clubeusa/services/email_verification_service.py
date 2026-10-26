# ============================================================
#  services/email_verification_service.py — Clube USA
#  Confirmacao de email: gera token, envia email, valida token.
#
#  Design:
#  - Token URL-safe de 32 bytes (256 bits), TTL 24h, uso unico.
#  - Email nao bloqueia acesso — e incentivado (+100 pontos).
#  - Em dev: loga o link. Em prod: envia via SMTP configurado.
#  - Rate limit de 3 envios por membro a cada 24h (anti-spam).
# ============================================================

import os
import secrets
import logging
from datetime import datetime, timedelta, timezone

log = logging.getLogger("email_verification")

_APP_URL = os.environ.get("APP_URL", "https://clubeusa.com")
_MAX_TOKENS_PER_DAY = 3
_TOKEN_TTL_HRS = 24
_POINTS_FOR_EMAIL_VERIFICATION = 100


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def request_email_verification(member_id: str) -> dict:
    """
    Gera token de verificacao de email para o membro autenticado.
    Retorna instrucoes. O token e enviado por email (ou logado em dev).

    Raises:
        ValueError: se membro nao tem email, email ja confirmado, ou rate limit.
    """
    sb = _supabase()

    # Busca membro
    result = sb.table("members").select(
        "id,email_enc,email_verified"
    ).eq("id", member_id).execute()

    if not result.data:
        raise ValueError("Membro nao encontrado.")

    member = result.data[0]

    if not member.get("email_enc"):
        raise ValueError("Nenhum email cadastrado. Atualize seu perfil primeiro.")

    if member.get("email_verified"):
        raise ValueError("Email ja confirmado.")

    # Rate limit: max 3 tokens nas ultimas 24h
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    recent = (
        sb.table("email_verification_tokens")
        .select("id", count="exact")
        .eq("member_id", member_id)
        .gte("created_at", cutoff)
        .execute()
    )
    if (recent.count or 0) >= _MAX_TOKENS_PER_DAY:
        raise ValueError(
            f"Limite de {_MAX_TOKENS_PER_DAY} solicitacoes por dia atingido. "
            "Aguarde 24h para tentar novamente."
        )

    # Invalida tokens anteriores (cleanup)
    sb.table("email_verification_tokens").delete().eq(
        "member_id", member_id
    ).is_("used_at", "null").execute()

    # Gera novo token
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=_TOKEN_TTL_HRS)).isoformat()

    sb.table("email_verification_tokens").insert({
        "member_id":  member_id,
        "token":      token,
        "expires_at": expires_at,
    }).execute()

    # Descriptografa email para envio
    from utils.security import decrypt
    email = decrypt(member["email_enc"])

    # Envia email (ou loga em dev)
    _send_verification_email(email, token, member_id)

    return {
        "message": "Email de confirmacao enviado. Verifique sua caixa de entrada.",
        "expires_in_hours": _TOKEN_TTL_HRS,
    }


def confirm_email_verification(token: str) -> dict:
    """
    Valida o token e marca o email como verificado.
    Concede pontos de bonus ao membro.

    Raises:
        ValueError: se token invalido, expirado ou ja usado.
    """
    if not token or len(token) > 64:
        raise ValueError("Token invalido.")

    sb = _supabase()
    now = datetime.now(timezone.utc)

    result = (
        sb.table("email_verification_tokens")
        .select("*")
        .eq("token", token)
        .execute()
    )

    if not result.data:
        raise ValueError("Token invalido ou expirado.")

    record = result.data[0]

    if record.get("used_at"):
        raise ValueError("Token ja utilizado.")

    expires = datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00"))
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if now > expires:
        raise ValueError("Token expirado. Solicite um novo link de confirmacao.")

    member_id = record["member_id"]

    # Verifica se ainda nao foi confirmado (idempotencia)
    member_check = sb.table("members").select(
        "email_verified"
    ).eq("id", member_id).execute()

    if not member_check.data:
        raise ValueError("Membro nao encontrado.")

    if member_check.data[0].get("email_verified"):
        # Marca token como usado mesmo assim
        sb.table("email_verification_tokens").update(
            {"used_at": now.isoformat()}
        ).eq("id", record["id"]).execute()
        return {"message": "Email ja confirmado anteriormente.", "already_verified": True}

    # Marca email como verificado
    sb.table("members").update({"email_verified": True}).eq("id", member_id).execute()

    # Invalida o token
    sb.table("email_verification_tokens").update(
        {"used_at": now.isoformat()}
    ).eq("id", record["id"]).execute()

    # Bonus de pontos
    try:
        sb.rpc("increment_points", {
            "p_member_id": member_id,
            "p_points":    _POINTS_FOR_EMAIL_VERIFICATION,
        }).execute()
    except Exception as e:
        log.warning(f"Falha ao conceder pontos de verificacao: {e}")

    # Audit log
    try:
        sb.table("audit_logs").insert({
            "actor_type":  "member",
            "actor_id":    member_id,
            "action":      "member.email_verified",
            "target_type": "member",
            "target_id":   member_id,
            "metadata":    {"points_awarded": _POINTS_FOR_EMAIL_VERIFICATION},
        }).execute()
    except Exception as e:
        log.warning(f"Audit log falhou: {e}")

    log.info(f"Email confirmado para membro {member_id}")

    return {
        "message":        "Email confirmado com sucesso!",
        "points_awarded": _POINTS_FOR_EMAIL_VERIFICATION,
        "already_verified": False,
    }


def _send_verification_email(email: str, token: str, member_id: str):
    """
    Envia email de confirmacao.
    - Em dev (ENVIRONMENT != 'production'): loga o link no console.
    - Em prod: usa SMTP via variaveis de ambiente.
      Variaveis necessarias: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_FROM
    """
    confirm_url = f"{_APP_URL}/auth/email/verify/{token}"

    if os.environ.get("ENVIRONMENT") != "production":
        log.info(
            f"[DEV] Link de confirmacao de email para membro {member_id}: {confirm_url}"
        )
        return

    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    email_from = os.environ.get("EMAIL_FROM", "noreply@clubeusa.com")

    if not all([smtp_host, smtp_user, smtp_pass]):
        log.warning(
            "SMTP nao configurado. Link de verificacao nao enviado. "
            f"Configure SMTP_HOST, SMTP_USER e SMTP_PASS. Link: {confirm_url}"
        )
        return

    subject = "Confirme seu email — Clube USA"
    body_pt = (
        f"Ola!\n\n"
        f"Clique no link abaixo para confirmar seu email no Clube USA:\n\n"
        f"{confirm_url}\n\n"
        f"O link expira em {_TOKEN_TTL_HRS} horas.\n\n"
        f"Se voce nao solicitou isso, ignore este email.\n\n"
        f"— Clube USA"
    )

    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = email_from
        msg["To"]      = email

        msg.attach(MIMEText(body_pt, "plain", "utf-8"))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(email_from, [email], msg.as_string())

        log.info(f"Email de verificacao enviado para membro {member_id}")

    except Exception as e:
        log.error(f"Falha ao enviar email de verificacao para membro {member_id}: {e}")
