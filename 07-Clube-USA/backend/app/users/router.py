from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.service import get_user_by_id
from app.auth.utils import decode_access_token
from app.database import get_db
from app.users.schemas import UpdateProfileRequest, UserProfile

router = APIRouter()
bearer = HTTPBearer()


def current_user_id(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> str:
    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")
    return user_id


@router.get("/me", response_model=UserProfile)
def get_me(user_id: str = Depends(current_user_id)):
    db = get_db()
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return user


@router.put("/me", response_model=UserProfile)
def update_me(body: UpdateProfileRequest, user_id: str = Depends(current_user_id)):
    db = get_db()
    updates = body.model_dump(exclude_none=True)
    # Never accept id, email, password_hash, or role from client body — enforced by schema
    if not updates:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar.")

    db.table("users").update(updates).eq("id", user_id).execute()
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return user
