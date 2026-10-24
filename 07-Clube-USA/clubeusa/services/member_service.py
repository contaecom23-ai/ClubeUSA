# ============================================================
#  services/member_service.py — Clube USA
#  Cadastro e gestao de membros com seguranca completa
# ============================================================

import os
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

EMAIL_TOKEN_TTL_HOURS = 24
# Intervalo mínimo entre reenvios (evita spam/abuse)
RESEND_COOLDOWN_MINUTES = 5

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

    # 4. Gerar token de confirmação de email se email fornecido
    confirm_token      = None
    confirm_expires_at = None
    if email:
        confirm_token      = secrets.token_urlsafe(32)
        confirm_expires_at = (datetime.utcnow() + timedelta(hours=EMAIL_TOKEN_TTL_HOURS)).isoformat()

    # 5. Inserir com PII criptografado
    member_data = {
        "phone_hash":              phone_hash,
        "phone_enc":               encrypt(phone),
        "email_hash":              hash_pii(email) if email else None,
        "email_enc":               encrypt(email) if email else None,
        "name_enc":                encrypt(name) if name else None,
        "language":                language,
        "state":                   state,
        "categories":              categories,
        "referred_by":             referred_by,
        "points":                  100,
        "referral_code":           generate_referral_code(),
        "email_confirmed":         False,
        "email_confirm_token":     confirm_token,
        "email_confirm_expires_at": confirm_expires_at,
    }

    result = sb.table("members").insert(member_data).execute()
    if not result.data:
        raise RuntimeError("Falha ao criar membro.")

    member = result.data[0]
    member_id = member["id"]

    # 6. Enviar email de confirmação (não bloqueia cadastro se falhar)
    if email and confirm_token:
        try:
            from utils.email import send_confirmation_email
            send_confirmation_email(email, name or "", confirm_token)
        except Exception as e:
            log.error("Falha ao enviar email de confirmacao: %s", e)

    # 7. Atribuir ao grupo WhatsApp
    try:
        group = assign_member_to_group(member_id, language)
    except Exception as e:
        log.warning(f"Nao foi possivel atribuir grupo: {e}")
        group = None

    # 8. Processar indicacao — pontuar quem indicou
    if referred_by:
        try:
            _process_referral(referred_by, member_id)
        except Exception as e:
            log.warning(f"Erro ao processar indicacao: {e}")

    # 9. Audit log
    _audit("member.created", member_id, {
        "language":    language,
        "state":       state,
        "has_referral": bool(referred_by),
        "categories":  categories,
        "has_email":   bool(email),
    }, ip=ip)

    # 10. Gerar token JWT
    token = create_token(member_id, member.get("plan", "free"))

    return {
        "action":           "registered",
        "member_id":        member_id,
        "token":            token,
        "points":           100,
        "level":            "bronze",
        "referral_code":    member["referral_code"],
        "email_confirmed":  False,
        "email_pending":    bool(email),
        "group_invite":     group.get("invite_link") if group else None,
        "group_name":       group.get("name") if group else None,
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
        "phone":           _mask_phone(decrypt(m["phone_enc"])),
        "email":           _mask_email(decrypt(m["email_enc"])) if m.get("email_enc") else "",
        "email_confirmed": m.get("email_confirmed", False),
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


# ============================================================
#  CONFIRMAÇÃO DE EMAIL
# ============================================================

def confirm_email(token: str) -> dict:
    """
    Valida token de confirmação e marca email como confirmado.
    Retorna resposta genérica independente de token válido ou não
    (evita oracle — não vaza se o token existe).
    """
    if not token or len(token) > 200:
        return {"confirmed": False}

    sb = _supabase()
    result = (
        sb.table("members")
        .select("id,email_confirmed,email_confirm_expires_at")
        .eq("email_confirm_token", token)
        .execute()
    )

    if not result.data:
        log.info("confirm_email: token nao encontrado")
        return {"confirmed": False}

    m = result.data[0]

    if m.get("email_confirmed"):
        return {"confirmed": True, "already": True}

    expires_at_str = m.get("email_confirm_expires_at")
    if expires_at_str:
        try:
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
            if expires_at.replace(tzinfo=None) < datetime.utcnow():
                log.info("confirm_email: token expirado para membro %s", m["id"])
                return {"confirmed": False, "expired": True}
        except Exception:
            pass

    # Confirmar e invalidar token
    sb.table("members").update({
        "email_confirmed":          True,
        "email_confirm_token":      None,
        "email_confirm_expires_at": None,
    }).eq("id", m["id"]).execute()

    _audit("member.email_confirmed", m["id"])
    log.info("Email confirmado para membro %s", m["id"])
    return {"confirmed": True}


def resend_confirmation(member_id: str) -> dict:
    """
    Reenvia email de confirmação ao membro autenticado.
    Aplica cooldown de RESEND_COOLDOWN_MINUTES para evitar abuso.
    """
    sb = _supabase()
    result = sb.table("members").select(
        "id,email_enc,email_confirmed,email_confirm_expires_at"
    ).eq("id", member_id).execute()

    if not result.data:
        raise ValueError("Membro não encontrado.")

    m = result.data[0]

    if m.get("email_confirmed"):
        return {"sent": False, "reason": "already_confirmed"}

    if not m.get("email_enc"):
        return {"sent": False, "reason": "no_email"}

    # Cooldown: se token atual ainda não expirou e foi gerado há pouco tempo
    expires_at_str = m.get("email_confirm_expires_at")
    if expires_at_str:
        try:
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
            token_created = expires_at.replace(tzinfo=None) - timedelta(hours=EMAIL_TOKEN_TTL_HOURS)
            cooldown_end  = token_created + timedelta(minutes=RESEND_COOLDOWN_MINUTES)
            if cooldown_end > datetime.utcnow():
                wait_secs = int((cooldown_end - datetime.utcnow()).total_seconds())
                return {"sent": False, "reason": "cooldown", "retry_in_seconds": wait_secs}
        except Exception:
            pass

    # Gerar novo token
    new_token   = secrets.token_urlsafe(32)
    new_expires = (datetime.utcnow() + timedelta(hours=EMAIL_TOKEN_TTL_HOURS)).isoformat()

    sb.table("members").update({
        "email_confirm_token":      new_token,
        "email_confirm_expires_at": new_expires,
    }).eq("id", member_id).execute()

    email_plain = decrypt(m["email_enc"])

    try:
        from utils.email import send_confirmation_email
        member_result = sb.table("members").select("name_enc").eq("id", member_id).execute()
        name = decrypt(member_result.data[0]["name_enc"]) if member_result.data and member_result.data[0].get("name_enc") else ""
        send_confirmation_email(email_plain, name, new_token)
    except Exception as e:
        log.error("Falha ao reenviar email de confirmacao: %s", e)
        return {"sent": False, "reason": "send_error"}

    _audit("member.email_confirmation_resent", member_id)
    return {"sent": True}


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
