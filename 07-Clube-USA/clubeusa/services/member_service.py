# ============================================================
#  services/member_service.py — Clube USA
#  Cadastro e gestao de membros com seguranca completa
# ============================================================

import os
import logging
from datetime import datetime
from typing import Optional

from utils.security import (
    encrypt, decrypt, hash_pii, hash_ip,
    validate_phone, validate_email, sanitize,
    generate_referral_code, generate_utm, create_token
)
from services.group_manager import assign_member_to_group
from services.email_service import send_email_confirmation

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

        # Marcar conversao no click log (melhor esforco)
        if referral_code:
            try:
                _mark_referral_click_converted(referral_code.upper(), member_id)
            except Exception as e:
                log.warning(f"Falha ao marcar conversao referral: {e}")

    # 7. Audit log
    _audit("member.created", member_id, {
        "language": language,
        "state": state,
        "has_referral": bool(referred_by),
        "categories": categories,
    }, ip=ip)

    # 8. Disparar confirmacao de email (nao bloqueante)
    if email:
        try:
            _send_email_confirmation_token(member_id, email, language)
        except Exception as e:
            log.warning(f"Nao foi possivel enviar email de confirmacao: {e}")

    # 9. Gerar token JWT
    token = create_token(member_id, member.get("plan", "free"))

    return {
        "action":         "registered",
        "member_id":      member_id,
        "token":          token,
        "points":         100,
        "level":          "bronze",
        "referral_code":  member["referral_code"],
        "group_invite":   group.get("invite_link") if group else None,
        "group_name":     group.get("name") if group else None,
        "email_confirm_sent": bool(email),
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


def _mark_referral_click_converted(referral_code: str, member_id: str):
    """Atualiza o registro de clique mais recente do codigo com o membro convertido."""
    sb = _supabase()
    # Pega o clique nao convertido mais recente deste codigo
    result = sb.table("referral_clicks").select("id").eq(
        "referral_code", referral_code
    ).is_("converted_member", "null").order("clicked_at", desc=True).limit(1).execute()
    if result.data:
        sb.table("referral_clicks").update({
            "converted_member": member_id,
        }).eq("id", result.data[0]["id"]).execute()


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
        "id":             m["id"],
        "name":           decrypt(m["name_enc"]) if m.get("name_enc") else "",
        "phone":          _mask_phone(decrypt(m["phone_enc"])),
        "email":          _mask_email(decrypt(m["email_enc"])) if m.get("email_enc") else "",
        "email_verified": m.get("email_verified", False),
        "language":       m["language"],
        "state":          m["state"],
        "plan":           m["plan"],
        "points":         m["points"],
        "level":          m["level"],
        "categories":     m["categories"],
        "referral_code":  m["referral_code"],
        "referral_count": m["referral_count"],
        "total_clicks":   m["total_clicks"],
        "created_at":     m["created_at"],
        "vip_expires_at": m.get("vip_expires_at"),
    }


def update_member_categories(member_id: str, categories: list) -> dict:
    sb = _supabase()
    result = sb.table("members").update({"categories": categories}).eq("id", member_id).execute()
    if not result.data:
        raise ValueError("Membro não encontrado.")
    return {"categories": result.data[0]["categories"]}


# ============================================================
#  EMAIL CONFIRMATION
# ============================================================

def _send_email_confirmation_token(member_id: str, email: str, language: str = "pt"):
    """Cria token de confirmacao e envia email."""
    import secrets
    from datetime import timedelta
    sb = _supabase()
    token = secrets.token_urlsafe(32)
    expires = (datetime.utcnow() + timedelta(hours=24)).isoformat()

    # Remove tokens anteriores nao usados deste membro
    sb.table("email_confirm_tokens").delete().eq("member_id", member_id).is_("used_at", "null").execute()

    sb.table("email_confirm_tokens").insert({
        "member_id":  member_id,
        "token":      token,
        "expires_at": expires,
    }).execute()

    send_email_confirmation(email, token, language)
    log.info(f"Email de confirmacao enviado para membro {member_id}")


def confirm_email(token: str) -> dict:
    """
    Confirma email via token.
    Retorna {"ok": True, "member_id": ...} ou lanca ValueError.
    """
    from datetime import timezone
    sb = _supabase()

    result = sb.table("email_confirm_tokens").select("*").eq("token", token).execute()
    if not result.data:
        raise ValueError("Token invalido ou expirado.")

    record = result.data[0]

    if record.get("used_at"):
        raise ValueError("Token ja utilizado.")

    expires = datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00"))
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires:
        raise ValueError("Token expirado. Solicite um novo link.")

    member_id = record["member_id"]

    # Marcar token como usado
    sb.table("email_confirm_tokens").update({
        "used_at": datetime.utcnow().isoformat(),
    }).eq("id", record["id"]).execute()

    # Marcar email como verificado
    sb.table("members").update({"email_verified": True}).eq("id", member_id).execute()

    _audit("member.email_confirmed", member_id)
    log.info(f"Email confirmado para membro {member_id}")

    return {"ok": True, "member_id": member_id}


def resend_email_confirmation(member_id: str) -> dict:
    """
    Reenvia email de confirmacao se o email ainda nao foi verificado.
    Anti-spam: max 3 envios por hora (controlado por rate_limit na API).
    """
    sb = _supabase()
    result = sb.table("members").select(
        "id,email_enc,email_verified,language"
    ).eq("id", member_id).execute()

    if not result.data:
        raise ValueError("Membro nao encontrado.")

    m = result.data[0]

    if m.get("email_verified"):
        raise ValueError("Email ja confirmado.")

    if not m.get("email_enc"):
        raise ValueError("Nenhum email cadastrado.")

    email    = decrypt(m["email_enc"])
    language = m.get("language", "pt")

    _send_email_confirmation_token(member_id, email, language)
    return {"ok": True, "message": "Email de confirmacao reenviado."}


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
