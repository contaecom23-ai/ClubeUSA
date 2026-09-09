from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from supabase import Client

from core.deps import get_current_user_id
from core.limiter import limiter
from db.supabase import get_supabase
from referrals.schemas import ReferralStatsResponse
from referrals.service import get_referral_stats, record_click

router = APIRouter(tags=["referrals"])


@router.get("/me", response_model=ReferralStatsResponse)
def get_my_referral_stats(
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase),
):
    return get_referral_stats(supabase, user_id)


@router.post("/click/{slug}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("60/minute")
def track_referral_click(
    request: Request,
    slug: str = Path(..., pattern=r"^[a-zA-Z0-9_-]{3,24}$"),
    supabase: Client = Depends(get_supabase),
):
    found = record_click(supabase, slug)
    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link de referral não encontrado",
        )
