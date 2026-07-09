from fastapi import APIRouter, Depends
from auth.middleware import get_current_user

router = APIRouter()


@router.get("/me")
async def me(user: dict = Depends(get_current_user)) -> dict:
    """Retorna dados básicos do usuário autenticado extraídos do JWT."""
    return {"user_id": user["user_id"], "email": user["email"]}
