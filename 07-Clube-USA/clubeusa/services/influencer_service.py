"""
services/influencer_service.py — Fase 1.3: Programa de Influenciadores

Calcula tiers com base no referral_count existente na tabela members.
Sem schema changes — usa o campo já presente.

Tiers:
  Parceiro     ≥  50 indicações válidas
  Embaixador   ≥ 250 indicações válidas
  Hall da Fama ≥ 1000 indicações válidas

Comissões (pagamento por resultado) aguardam decisão D-006 em DECISOES.md.
"""

import os
import logging

log = logging.getLogger("influencer_service")

# Tiers em ordem crescente de requisito
TIERS = [
    {"key": "hall_da_fama", "label": "Hall da Fama", "min_referrals": 1000},
    {"key": "embaixador",   "label": "Embaixador",   "min_referrals": 250},
    {"key": "parceiro",     "label": "Parceiro",     "min_referrals": 50},
]


def get_tier(referral_count: int) -> dict:
    """Retorna o tier atual e informações de progressão para um dado referral_count."""
    current_tier = None
    for tier in TIERS:
        if referral_count >= tier["min_referrals"]:
            current_tier = tier
            break

    # Próximo tier a atingir (o mais próximo, não o mais alto)
    next_tier = None
    for tier in reversed(TIERS):
        if referral_count < tier["min_referrals"]:
            next_tier = tier
            break

    needed = (next_tier["min_referrals"] - referral_count) if next_tier else 0

    return {
        "tier":         current_tier["key"] if current_tier else None,
        "tier_label":   current_tier["label"] if current_tier else "Sem selo",
        "next_tier":    next_tier["key"] if next_tier else None,
        "next_tier_label": next_tier["label"] if next_tier else None,
        "referrals_needed": needed,
    }


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def get_member_influencer_stats(member_id: str) -> dict:
    """Retorna tier e estatísticas de influência do membro autenticado."""
    sb = _supabase()
    result = sb.table("members").select(
        "referral_code,referral_count"
    ).eq("id", member_id).execute()

    if not result.data:
        return None

    m = result.data[0]
    tier_info = get_tier(m["referral_count"])

    return {
        "referral_code":   m["referral_code"],
        "valid_referrals": m["referral_count"],
        **tier_info,
    }


def list_influencers(min_referrals: int = 1) -> list[dict]:
    """Lista membros com ≥ min_referrals indicações válidas, com tier calculado.
    Destinado ao admin. Não expõe PII (referral_code é o identificador).
    """
    sb = _supabase()
    result = sb.table("members").select(
        "id,referral_code,referral_count,created_at"
    ).gte("referral_count", min_referrals).order(
        "referral_count", desc=True
    ).limit(200).execute()

    rows = result.data or []
    return [
        {
            "id":              r["id"],
            "referral_code":   r["referral_code"],
            "valid_referrals": r["referral_count"],
            "joined_at":       r["created_at"],
            **get_tier(r["referral_count"]),
        }
        for r in rows
    ]
