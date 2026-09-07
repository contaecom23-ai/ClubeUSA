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
    from utils.email import generate_confirm_token
    from datetime import timezone as _tz

    confirm_token = generate_confirm_token() if email else None

    member_data = {
        "phone_hash":          phone_hash,
        "phone_enc":           encrypt(phone),
        "email_hash":          hash_pii(email) if email else None,
        "email_enc":           encrypt(email) if email else None,
        "name_enc":            encrypt(name) if name else None,
        "language":            language,
        "state":               state,
        "categories":          categories,
        "referred_by":         referred_by,
        "points":              100,
        "referral_code":       generate_referral_code(),
        "email_confirmed":     False,
        "email_confirm_token": confirm_token,
        "email_confirm_sent_at": datetime.now(_tz.utc).isoformat() if confirm_token else None,
    }

    result = sb.table("members").insert(member_data).execute()
    if not result.data:
        raise RuntimeError("Falha ao criar membro.")

    member = result.data[0]
    member_id = member["id"]

    # 5. Enviar email de confirmacao (nao bloqueia cadastro em caso de falha)
    if email and confirm_token:
        try:
            from utils.email import send_confirmation_email
            send_confirmation_email(email, name or "", confirm_token)
        except Exception as e:
            log.warning(f"Falha ao enviar email de confirmacao: {e}")

    # 6. Atribuir ao grupo WhatsApp
    try:
        group = assign_member_to_group(member_id, language)
    except Exception as e:
        log.warning(f"Nao foi possivel atribuir grupo: {e}")
        group = None

    # 7. Processar indicacao — pontuar quem indicou
    if referred_by:
        try:
            _process_referral(referred_by, member_id)
        except Exception as e:
            log.warning(f"Erro ao processar indicacao: {e}")

    # 8. Audit log
    _audit("member.created", member_id, {
        "language": language,
        "state": state,
        "has_referral": bool(referred_by),
        "has_email": bool(email),
        "categories": categories,
    }, ip=ip)

    # 9. Gerar token JWT
    token = create_token(member_id, member.get("plan", "free"))

    return {
        "action":           "registered",
        "member_id":        member_id,
        "token":            token,
        "points":           100,
        "level":            "bronze",
        "referral_code":    member["referral_code"],
        "email_confirm_sent": bool(email),
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


# ============================================================
#  CONFIRMACAO DE EMAIL
# ============================================================

def confirm_email_token(token: str) -> dict:
    """
    Consome o token de confirmacao de email.

    Retorna {"ok": True, "member_id": ...} em sucesso.
    Levanta ValueError em token invalido/expirado.

    Tokens expiram em 72 horas a partir do email_confirm_sent_at.
    """
    if not token or len(token) > 128:
        raise ValueError("Token invalido.")

    from datetime import timezone as _tz
    sb = _supabase()

    result = sb.table("members").select(
        "id,email_confirmed,email_confirm_sent_at"
    ).eq("email_confirm_token", token).execute()

    if not result.data:
        raise ValueError("Token invalido ou ja utilizado.")

    m = result.data[0]

    if m.get("email_confirmed"):
        # Idempotente: ja confirmado, apenas confirma ok
        return {"ok": True, "member_id": m["id"], "already_confirmed": True}

    # Verifica TTL de 72 horas
    sent_at_raw = m.get("email_confirm_sent_at")
    if sent_at_raw:
        sent_at = datetime.fromisoformat(sent_at_raw.replace("Z", "+00:00"))
        if sent_at.tzinfo is None:
            sent_at = sent_at.replace(tzinfo=_tz.utc)
        age_hours = (datetime.now(_tz.utc) - sent_at).total_seconds() / 3600
        if age_hours > 72:
            raise ValueError("Link de confirmacao expirado. Solicite um novo no seu painel.")

    # Marca confirmado e apaga token (one-time use)
    sb.table("members").update({
        "email_confirmed":     True,
        "email_confirm_token": None,
    }).eq("id", m["id"]).execute()

    _audit("member.email_confirmed", m["id"])
    log.info(f"Email confirmado para membro {m['id']}")

    return {"ok": True, "member_id": m["id"], "already_confirmed": False}
