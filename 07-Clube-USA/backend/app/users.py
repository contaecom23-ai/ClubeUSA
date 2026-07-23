from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from .deps import get_current_user
from .db import get_conn

router = APIRouter(prefix="/api", tags=["users"])

US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC",
}


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    us_state: Optional[str] = None
    us_city: Optional[str] = None
    whatsapp: Optional[str] = None
    bio: Optional[str] = None

    def validate_fields(self):
        if self.full_name is not None:
            self.full_name = self.full_name.strip()
            if len(self.full_name) < 2:
                raise ValueError("Nome muito curto")
        if self.us_state is not None:
            self.us_state = self.us_state.upper().strip()
            if self.us_state and self.us_state not in US_STATES:
                raise ValueError(f"Estado inválido: {self.us_state}")
        if self.bio is not None and len(self.bio) > 500:
            raise ValueError("Bio deve ter no máximo 500 caracteres")


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    user_id = current_user["id"]
    async with get_conn() as conn:
        profile = await conn.fetchrow(
            "SELECT us_state, us_city, whatsapp, bio, avatar_url, updated_at "
            "FROM profiles WHERE user_id = $1",
            user_id,
        )
    return {
        "user": {
            "id": str(current_user["id"]),
            "email": current_user["email"],
            "full_name": current_user["full_name"],
            "email_confirmed": current_user["email_confirmed"],
            "referral_code": current_user["referral_code"],
        },
        "profile": dict(profile) if profile else {},
    }


@router.put("/me")
async def update_me(
    body: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update the authenticated user's profile."""
    try:
        body.validate_fields()
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    user_id = current_user["id"]

    async with get_conn() as conn:
        if body.full_name is not None:
            await conn.execute(
                "UPDATE users SET full_name = $1 WHERE id = $2",
                body.full_name,
                user_id,
            )

        profile_fields = {
            k: v
            for k, v in {
                "us_state": body.us_state,
                "us_city": body.us_city,
                "whatsapp": body.whatsapp,
                "bio": body.bio,
            }.items()
            if v is not None
        }

        if profile_fields:
            set_clause = ", ".join(
                f"{col} = ${i + 2}" for i, col in enumerate(profile_fields)
            )
            values = list(profile_fields.values())
            await conn.execute(
                f"UPDATE profiles SET {set_clause} WHERE user_id = $1",
                user_id,
                *values,
            )

        updated_user = await conn.fetchrow(
            "SELECT id, email, full_name, email_confirmed, referral_code FROM users WHERE id = $1",
            user_id,
        )
        updated_profile = await conn.fetchrow(
            "SELECT us_state, us_city, whatsapp, bio, avatar_url, updated_at FROM profiles WHERE user_id = $1",
            user_id,
        )

    return {
        "user": dict(updated_user),
        "profile": dict(updated_profile) if updated_profile else {},
    }


@router.get("/referral-stats")
async def referral_stats(current_user: dict = Depends(get_current_user)):
    """How many users registered via this user's referral link."""
    async with get_conn() as conn:
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM users WHERE referred_by_user_id = $1",
            current_user["id"],
        )
        confirmed = await conn.fetchval(
            "SELECT COUNT(*) FROM users WHERE referred_by_user_id = $1 AND email_confirmed = TRUE",
            current_user["id"],
        )
    return {
        "referral_code": current_user["referral_code"],
        "total_referrals": count,
        "confirmed_referrals": confirmed,
        "referral_link": f"https://clubeusa.com/r/{current_user['referral_code']}",
    }
