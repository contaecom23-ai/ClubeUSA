"""
Fase 1.3 — Programa de Influenciadores Pago por Resultado.

Fluxo de pagamento:
1. Usuário acumula referrals válidos (email confirmado + localização preenchida).
2. Admin vê lista de pendências em GET /admin/influencer/pending.
3. Admin paga externamente (PayPal/Venmo/Zelle) e registra via POST /admin/influencer/payouts.
4. Usuário vê histórico em GET /influencer/status.

Decisões de negócio (PAYOUT_RATE_USD, PAYOUT_BUDGET_USD) em DECISOES.md — não hardcodadas.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from supabase import Client

from config import settings
from deps import get_current_user_id, get_db
from models import (
    InfluencerLeaderboard,
    InfluencerPendingItem,
    InfluencerStatus,
    LeaderboardEntry,
    PayoutResponse,
    RegisterPayoutRequest,
    compute_badge,
)

router = APIRouter(prefix="/influencer", tags=["influencer"])
admin_router = APIRouter(prefix="/admin/influencer", tags=["admin-influencer"])


def _require_admin(x_admin_key: str = Header(default="")) -> None:
    """Valida a chave de admin. Reutiliza o mesmo mecanismo do router de admin geral."""
    if not settings.ADMIN_KEY or x_admin_key != settings.ADMIN_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chave de admin inválida ou ausente",
        )


def _get_total_paid(db: Client, user_id: str) -> float:
    result = (
        db.table("influencer_payouts")
        .select("amount_usd")
        .eq("user_id", user_id)
        .execute()
    )
    return sum(float(row["amount_usd"]) for row in (result.data or []))


def _get_valid_referral_count(db: Client, user_id: str) -> int:
    result = db.rpc("get_valid_referral_count", {"p_user_id": user_id}).execute()
    return int(result.data or 0)


# ── Rotas públicas / autenticadas ────────────────────────────────────────────

@router.get("/leaderboard", response_model=InfluencerLeaderboard)
async def get_leaderboard(
    db: Annotated[Client, Depends(get_db)],
) -> InfluencerLeaderboard:
    """Ranking público dos top 20 influenciadores. Sem dados PII (sem email/telefone)."""
    result = db.rpc("get_influencer_leaderboard", {"p_limit": 20}).execute()
    rows = result.data or []

    entries = []
    for rank, row in enumerate(rows, start=1):
        count = int(row["valid_referrals"])
        badge, _, _ = compute_badge(count)
        entries.append(
            LeaderboardEntry(
                rank=rank,
                display_name=row["display_name"],
                city=row.get("city"),
                state=row.get("state"),
                valid_referrals=count,
                badge=badge,
            )
        )

    rate: float | None = settings.PAYOUT_RATE_USD if settings.PAYOUT_RATE_USD > 0 else None
    return InfluencerLeaderboard(entries=entries, payout_rate_usd=rate)


@router.get("/status", response_model=InfluencerStatus)
async def get_my_influencer_status(
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[Client, Depends(get_db)],
) -> InfluencerStatus:
    """Status do influenciador autenticado: nível, referrals válidos, estimativa de ganho."""
    valid_referrals = _get_valid_referral_count(db, user_id)
    total_paid = _get_total_paid(db, user_id)
    badge, next_badge, next_badge_at = compute_badge(valid_referrals)

    if settings.PAYOUT_RATE_USD > 0:
        estimated = round(valid_referrals * settings.PAYOUT_RATE_USD, 2)
    else:
        estimated = None

    return InfluencerStatus(
        valid_referrals=valid_referrals,
        badge=badge,
        next_badge=next_badge,
        next_badge_at=next_badge_at,
        estimated_earning_usd=estimated,
        total_paid_usd=total_paid,
    )


# ── Rotas de admin ────────────────────────────────────────────────────────────

@admin_router.get("/pending", response_model=list[InfluencerPendingItem])
async def get_pending_payouts(
    db: Annotated[Client, Depends(get_db)],
    _: Annotated[None, Depends(_require_admin)],
) -> list[InfluencerPendingItem]:
    """
    Lista usuários que têm referrals válidos mas saldo ainda a ser pago.
    Requer PAYOUT_RATE_USD configurado — caso contrário retorna lista vazia com aviso em header.
    """
    if settings.PAYOUT_RATE_USD <= 0:
        return []

    result = db.rpc("get_influencer_leaderboard", {"p_limit": 500}).execute()
    rows = result.data or []

    items = []
    for row in rows:
        count = int(row["valid_referrals"])
        if count == 0:
            continue
        total_paid = _get_total_paid(db, str(row["user_id"]))
        owed = round(count * settings.PAYOUT_RATE_USD - total_paid, 2)
        if owed <= 0:
            continue
        badge, _, _ = compute_badge(count)
        items.append(
            InfluencerPendingItem(
                user_id=str(row["user_id"]),
                display_name=row["display_name"],
                valid_referrals=count,
                badge=badge,
                estimated_owed_usd=owed,
                total_paid_usd=total_paid,
            )
        )

    return sorted(items, key=lambda x: x.estimated_owed_usd, reverse=True)


@admin_router.post("/payouts", response_model=PayoutResponse, status_code=status.HTTP_201_CREATED)
async def register_payout(
    body: RegisterPayoutRequest,
    db: Annotated[Client, Depends(get_db)],
    _: Annotated[None, Depends(_require_admin)],
) -> PayoutResponse:
    """
    Registra um pagamento já realizado externamente (PayPal/Venmo/etc.).
    Não transfere dinheiro — apenas rastreia o histórico para auditoria.
    """
    # Verifica que o usuário existe
    user_result = db.table("users").select("id").eq("id", body.user_id).execute()
    if not user_result.data:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    valid_referrals = _get_valid_referral_count(db, body.user_id)

    result = (
        db.table("influencer_payouts")
        .insert(
            {
                "user_id": body.user_id,
                "valid_referrals": valid_referrals,
                "amount_usd": body.amount_usd,
                "payment_method": body.payment_method,
                "payment_ref": body.payment_ref,
                "notes": body.notes,
            }
        )
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=500, detail="Erro ao registrar pagamento")

    row = result.data[0]
    return PayoutResponse(
        id=row["id"],
        user_id=row["user_id"],
        valid_referrals=row["valid_referrals"],
        amount_usd=float(row["amount_usd"]),
        payment_method=row["payment_method"],
        payment_ref=row.get("payment_ref"),
        notes=row.get("notes"),
        created_at=row["created_at"],
    )
