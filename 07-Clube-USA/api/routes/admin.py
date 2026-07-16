from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from supabase import Client

from config import settings
from deps import get_db
from models import AdminMetrics, EventMetrics, ReferralMetrics, UsersMetrics

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(x_admin_key: Annotated[str, Header()] = "") -> None:
    if not settings.ADMIN_KEY or x_admin_key != settings.ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Acesso negado")


@router.get(
    "/metrics",
    response_model=AdminMetrics,
    dependencies=[Depends(_require_admin)],
    summary="Métricas agregadas da plataforma (somente admin)",
)
async def get_metrics(
    db: Annotated[Client, Depends(get_db)],
) -> AdminMetrics:
    """
    Requer o header X-Admin-Key com o valor de ADMIN_KEY do .env.
    Para MVP (< 10k usuários) carrega dados em memória e agrega em Python.
    Migrar para queries COUNT/aggregate no Supabase quando ultrapassar 50k registros.
    """
    now = datetime.now(timezone.utc)
    seven_days_ago = (now - timedelta(days=7)).isoformat()
    thirty_days_ago = (now - timedelta(days=30)).isoformat()

    # Carrega todos os usuários (MVP — ver docstring para escala)
    users_result = (
        db.table("users")
        .select("id, email_confirmed_at, referred_by_user_id, created_at, state, city, zip_code")
        .execute()
    )
    users = users_result.data or []

    def _has_location(u: dict) -> bool:
        return bool(u.get("zip_code") or (u.get("state") and u.get("city")))

    total_users = len(users)
    confirmed_users = sum(1 for u in users if u.get("email_confirmed_at"))
    new_7d = sum(1 for u in users if (u.get("created_at") or "") >= seven_days_ago)
    new_30d = sum(1 for u in users if (u.get("created_at") or "") >= thirty_days_ago)
    total_referred = sum(1 for u in users if u.get("referred_by_user_id"))
    valid_registrations = sum(1 for u in users if u.get("email_confirmed_at") and _has_location(u))

    # Carrega eventos dos últimos 30 dias
    events_result = (
        db.table("events")
        .select("event_type, created_at")
        .gte("created_at", thirty_days_ago)
        .execute()
    )
    events = events_result.data or []

    logins_7d = sum(
        1 for e in events
        if e.get("event_type") == "user_login" and (e.get("created_at") or "") >= seven_days_ago
    )
    logins_30d = sum(1 for e in events if e.get("event_type") == "user_login")
    reg_7d = sum(
        1 for e in events
        if e.get("event_type") == "user_registered" and (e.get("created_at") or "") >= seven_days_ago
    )
    reg_30d = sum(1 for e in events if e.get("event_type") == "user_registered")

    confirmation_rate = round(confirmed_users / total_users, 3) if total_users > 0 else 0.0
    attribution_rate = round(total_referred / total_users, 3) if total_users > 0 else 0.0
    valid_rate = round(valid_registrations / total_users, 3) if total_users > 0 else 0.0

    return AdminMetrics(
        users=UsersMetrics(
            total=total_users,
            confirmed=confirmed_users,
            unconfirmed=total_users - confirmed_users,
            confirmation_rate=confirmation_rate,
            new_last_7d=new_7d,
            new_last_30d=new_30d,
            valid_registrations=valid_registrations,
            valid_rate=valid_rate,
        ),
        referrals=ReferralMetrics(
            total_attributed=total_referred,
            attribution_rate=attribution_rate,
        ),
        events=EventMetrics(
            logins_last_7d=logins_7d,
            logins_last_30d=logins_30d,
            registrations_last_7d=reg_7d,
            registrations_last_30d=reg_30d,
        ),
        as_of=now.isoformat(),
    )
