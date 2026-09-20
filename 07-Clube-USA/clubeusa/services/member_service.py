# ============================================================
#  services/member_service.py — Clube USA
#  Cadastro e gestao de membros com seguranca completa
# ============================================================

import os
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional

from utils.security import (
    encrypt, decrypt, hash_pii, hash_ip,
    validate_phone, validate_email, sanitize,
    generate_referral_code, generate_utm, create_token
)
from services.group_manager import assign_member_to_group

log = logging.getLogger("member_service")


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def _audit(action, target_id, metadata=None, actor_id=None, ip=None):
    try:
        sb = _supabase()
        sb.table("audit_logs").insert({
            "actor_id":    actor_id,
            "actor_type":  "member" if actor_id else "system",
            "action":      action,
            "target_type": "member",
            "target_id":   target_id,
            "ip_hash":     hash_ip(ip) if ip else None,
            "metadata":    metadata or {},
        }).execute()
    except Exception as e:
        log.warning(f"Audit log falhou: {e}")


# ============================================================
#  CADASTRO
# ============================================================

def register_member(
    phone: str,
    name: str = None,
    email: str = None,
    language: str = "pt",
    state: str = None,
    categories: list = None,
    referral_code: str = None,
    ip: str = None,
) -> dict:
    """
    Cadastra novo membro com seguranca completa.

    - Valida e normaliza inputs
    - Criptografa PII antes de salvar
    - Verifica duplicatas por hash (sem expor dados)
    - Atribui ao grupo disponivel
    - Processa indicacao se houver codigo
    - Registra no audit log
    """

    # 1. Validar e normalizar
    try:
        phone = validate_phone(phone)
    except ValueError as e:
        raise ValueError(f"Telefone invalido: {e}")

    if email:
        try:
            email = validate_email(email)
        except ValueError as e:
            raise ValueError(f"Email invalido: {e}")

    name  = sanitize(name or "", 80)
    state = sanitize(state or "", 50)
    language = language if language in ("pt", "es") else "pt"
    categories = categories or ["all"]

    # 2. Verificar duplicata por hash (sem expor dados)
    sb = _supabase()
    phone_hash = hash_pii(phone)
    existing = sb.table("members").select("id,status").eq("phone_hash", phone_hash).execute()

    if existing.data:
        member = existing.data[0]
        if member["status"] == "banned":
            raise PermissionError("Acesso negado.")
        # Membro ja existe — retorna token sem criar novo
        token = create_token(member["id"])
        _audit("member.login", member["id"], ip=ip)
        return {"action": "login", "member_id": member["id"], "token": token}

    # 3. Resolver indicacao
    referred_by = None
    if referral_code:
        ref_result = (
            sb.table("members")
            .select("id")
            .eq("referral_code", referral_code.upper())
            .eq("status", "active")
            .execute()
        )
        if ref_result.data:
            referred_by = ref_result.data[0]["id"]

    # 4. Inserir com PII criptografado
    member_data = {
        "phone_hash":     phone_hash,
        "phone_enc":      encrypt(phone),           # criptografado
        "email_hash":     hash_pii(email) if email else None,
        "email_enc":      encrypt(email) if email else None,
        "name_enc":       encrypt(name) if name else None,
        "language":       language,
        "state":          state,
        "categories":     categories,
        "referred_by":    referred_by,
        "points":         100,                       # pontos de boas-vindas
        "referral_code":  generate_referral_code(),
    }

    result = sb.table("members").insert(member_data).execute()
    if not result.data:
        raise RuntimeError("Falha ao criar membro.")

    member = result.data[0]
    member_id = member["id"]

    # 5. Atribuir ao grupo WhatsApp
    try:
        group = assign_member_to_group(member_id, language)
    except Exception as e:
        log.warning(f"Nao foi possivel atribuir grupo: {e}")
        group = None

    # 6. Processar indicacao — pontuar quem indicou
    if referred_by:
        try:
            _process_referral(referred_by, member_id)
        except Exception as e:
            log.warning(f"Erro ao processar indicacao: {e}")

    # 7. Audit log
    _audit("member.created", member_id, {
        "language": language,
        "state": state,
        "has_referral": bool(referred_by),
        "categories": categories,
    }, ip=ip)

    # 8. Gerar token JWT
    token = create_token(member_id, member.get("plan", "free"))

    # 9. Disparar confirmação de email (non-blocking: falha silenciosa)
    email_confirmation_sent = False
    if email:
        try:
            email_confirmation_sent = send_email_confirmation_for_member(member_id, email)
        except Exception as e:
            log.warning(f"Falha ao enviar email de confirmacao para {member_id}: {e}")

    return {
        "action":      "registered",
        "member_id":   member_id,
        "token":       token,
        "points":      100,
        "level":       "bronze",
        "referral_code": member["referral_code"],
        "group_invite": group.get("invite_link") if group else None,
        "group_name":   group.get("name") if group else None,
        "email_confirmation_sent": email_confirmation_sent,
    }


def _process_referral(referrer_id: str, referred_id: str):
    """Registra indicacao e adiciona pontos ao indicador."""
    sb = _supabase()

    # Registrar indicacao
    sb.table("referrals").insert({
        "referrer_id":    referrer_id,
        "referred_id":    referred_id,
        "points_awarded": 200,
        "status":         "confirmed",
        "confirmed_at":   datetime.utcnow().isoformat(),
    }).execute()

    # Pontuar indicador
    sb.rpc("increment_points", {
        "p_member_id": referrer_id,
        "p_points":    200,
    }).execute()

    # Incrementar contador de indicacoes
    sb.rpc("increment_referral_count", {
        "p_member_id": referrer_id,
    }).execute()

    _audit("referral.confirmed", referred_id, {"referrer_id": referrer_id})
    log.info(f"Indicacao confirmada: {referrer_id} indicou {referred_id}")

    # Verifica milestone: 3 indicacoes = 30 dias VIP gratis
    try:
        _check_vip_milestone(referrer_id)
    except Exception as e:
        log.warning(f"Falha na verificacao de milestone VIP: {e}")


def _check_vip_milestone(referrer_id: str):
    """Concede trial VIP 30 dias quando indicador atinge 3 indicacoes."""
    sb = _supabase()
    result = sb.table("members").select(
        "referral_count,plan,vip_trial_used"
    ).eq("id", referrer_id).execute()

    if not result.data:
        return

    m = result.data[0]
    if m["referral_count"] >= 3 and m["plan"] == "free" and not m.get("vip_trial_used", False):
        from datetime import datetime, timedelta
        sb.table("members").update({
            "plan":           "vip",
            "vip_started_at": datetime.utcnow().isoformat(),
            "vip_expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "vip_trial_used": True,
        }).eq("id", referrer_id).execute()

        sb.table("audit_logs").insert({
            "actor_type":  "system",
            "action":      "member.vip_trial_granted",
            "target_type": "member",
            "target_id":   referrer_id,
            "metadata":    {"reason": "referral_milestone_3"},
        }).execute()

        log.info(f"VIP trial 30 dias concedido a {referrer_id} por 3 indicacoes")


# ============================================================
#  BUSCA E PERFIL
# ============================================================

def get_member_profile(member_id: str) -> Optional[dict]:
    """
    Retorna perfil do membro com PII descriptografado.
    Usado apenas para exibir no painel do proprio membro.
    """
    sb = _supabase()
    result = sb.table("members").select("*").eq("id", member_id).execute()
    if not result.data:
        return None

    m = result.data[0]

    # Descriptografa PII apenas para exibicao
    return {
        "id":              m["id"],
        "name":            decrypt(m["name_enc"]) if m.get("name_enc") else "",
        "phone":           _mask_phone(decrypt(m["phone_enc"])),  # mascara parcial
        "email":           _mask_email(decrypt(m["email_enc"])) if m.get("email_enc") else "",
        "email_confirmed": m.get("email_confirmed_at") is not None,
        "language":        m["language"],
        "state":           m["state"],
        "plan":            m["plan"],
        "points":          m["points"],
        "level":           m["level"],
        "categories":      m["categories"],
        "referral_code":   m["referral_code"],
        "referral_count":  m["referral_count"],
        "total_clicks":    m["total_clicks"],
        "created_at":      m["created_at"],
        "vip_expires_at":  m.get("vip_expires_at"),
    }


def update_member_categories(member_id: str, categories: list) -> dict:
    sb = _supabase()
    result = sb.table("members").update({"categories": categories}).eq("id", member_id).execute()
    if not result.data:
        raise ValueError("Membro não encontrado.")
    return {"categories": result.data[0]["categories"]}


def _mask_phone(phone: str) -> str:
    """Mascara numero — exibe apenas ultimos 4 digitos."""
    if len(phone) <= 4: return phone
    return "*" * (len(phone) - 4) + phone[-4:]


def _mask_email(email: str) -> str:
    """Mascara email — exibe apenas inicio e dominio."""
    if "@" not in email: return email
    local, domain = email.split("@", 1)
    if len(local) <= 2: return email
    return local[:2] + "*" * (len(local) - 2) + "@" + domain


# ============================================================
#  CONFIRMAÇÃO DE EMAIL
# ============================================================

def send_email_confirmation_for_member(member_id: str, email: str) -> bool:
    """
    Gera token de verificação, persiste (hash), e envia email.

    - Token bruto: URL-safe 32 bytes (256 bits de entropia)
    - Armazenado como SHA-256 — nunca o token bruto
    - TTL: 24 horas
    - Idempotente: deleta tokens anteriores do mesmo membro

    Returns True se o email foi enviado (ou logado em dev).
    """
    from utils.email_sender import send_email_confirmation

    app_url  = os.environ.get("APP_URL", "https://clubeusa.com")
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = (datetime.utcnow() + timedelta(hours=24)).isoformat()

    sb = _supabase()

    # Remove tokens anteriores deste membro (mantém apenas 1 pendente)
    sb.table("email_verify_tokens").delete().eq("member_id", member_id).execute()

    # Insere novo token
    sb.table("email_verify_tokens").insert({
        "member_id":  member_id,
        "token_hash": token_hash,
        "expires_at": expires_at,
    }).execute()

    confirm_url = f"{app_url}/auth/email/confirm?token={raw_token}"

    # Busca nome para personalizar o email
    member_result = sb.table("members").select("name_enc").eq("id", member_id).execute()
    name = ""
    if member_result.data and member_result.data[0].get("name_enc"):
        try:
            name = decrypt(member_result.data[0]["name_enc"])
        except Exception:
            pass

    return send_email_confirmation(email, confirm_url, name)


def confirm_member_email(raw_token: str) -> dict:
    """
    Verifica token de email e marca membro como confirmado.

    Returns dict com member_id ou lança ValueError.
    """
    if not raw_token or len(raw_token) > 200:
        raise ValueError("Token inválido.")

    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    sb = _supabase()

    result = sb.table("email_verify_tokens").select("*").eq("token_hash", token_hash).execute()
    if not result.data:
        raise ValueError("Token inválido ou já utilizado.")

    record = result.data[0]

    if record.get("used_at"):
        raise ValueError("Token já utilizado.")

    from datetime import timezone
    expires = datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00"))
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires:
        sb.table("email_verify_tokens").delete().eq("token_hash", token_hash).execute()
        raise ValueError("Token expirado. Solicite um novo link de confirmação.")

    member_id = record["member_id"]

    # Marcar token como usado
    sb.table("email_verify_tokens").update(
        {"used_at": datetime.utcnow().isoformat()}
    ).eq("token_hash", token_hash).execute()

    # Marcar email como confirmado no perfil
    sb.table("members").update(
        {"email_confirmed_at": datetime.utcnow().isoformat()}
    ).eq("id", member_id).execute()

    _audit("member.email_confirmed", member_id)
    log.info(f"Email confirmado para membro {member_id}")

    return {"member_id": member_id, "confirmed": True}


def resend_email_confirmation(member_id: str) -> bool:
    """Re-envia o email de confirmação. Limita a 1 reenvio por hora via TTL."""
    sb = _supabase()

    # Verifica se já tem token recente (< 1 hora) para evitar flood
    result = sb.table("email_verify_tokens").select("created_at").eq("member_id", member_id).execute()
    if result.data:
        from datetime import timezone
        created = datetime.fromisoformat(result.data[0]["created_at"].replace("Z", "+00:00"))
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age_minutes = (datetime.now(timezone.utc) - created).total_seconds() / 60
        if age_minutes < 60:
            raise ValueError(f"Aguarde {int(60 - age_minutes)} minutos antes de solicitar um novo link.")

    # Busca email do membro
    member_result = sb.table("members").select("email_enc,email_confirmed_at").eq("id", member_id).execute()
    if not member_result.data:
        raise ValueError("Membro não encontrado.")

    m = member_result.data[0]
    if m.get("email_confirmed_at"):
        raise ValueError("Email já confirmado.")
    if not m.get("email_enc"):
        raise ValueError("Nenhum email cadastrado.")

    email = decrypt(m["email_enc"])
    return send_email_confirmation_for_member(member_id, email)


# ============================================================
#  RASTREAMENTO DE CLIQUES
# ============================================================

def track_click(member_id: str, deal_id: str, ip: str = None) -> str:
    """
    Registra clique de membro num deal.
    Retorna UTM code unico para o link afiliado.
    Pontua o membro automaticamente.
    """
    sb = _supabase()
    utm = generate_utm(member_id, deal_id)

    # Verifica se ja clicou neste deal (idempotente)
    existing = (
        sb.table("clicks")
        .select("id,utm_code")
        .eq("member_id", member_id)
        .eq("deal_id", deal_id)
        .execute()
    )
    if existing.data:
        return existing.data[0]["utm_code"]  # retorna UTM existente

    # Registra clique
    sb.table("clicks").insert({
        "member_id": member_id,
        "deal_id":   deal_id,
        "utm_code":  utm,
        "ip_hash":   hash_ip(ip) if ip else None,
    }).execute()

    # Adiciona 10 pontos pelo clique
    sb.rpc("increment_points", {"p_member_id": member_id, "p_points": 10}).execute()
    sb.rpc("increment_clicks", {"p_member_id": member_id}).execute()

    return utm
