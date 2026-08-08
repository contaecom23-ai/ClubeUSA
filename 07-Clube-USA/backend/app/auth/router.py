from fastapi import APIRouter, Depends, Request
from supabase import Client

from app.auth.models import LoginRequest, MessageResponse, RegisterRequest, TokenResponse
from app.auth.service import confirm_email, login_user, register_user
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=MessageResponse, status_code=201)
async def register(body: RegisterRequest, request: Request, db: Client = Depends(get_db)):
    await register_user(db, body.email, body.password, body.full_name, _client_ip(request))
    return {"message": "Conta criada! Verifique seu email para confirmar o cadastro."}


@router.get("/confirm-email", response_model=MessageResponse)
def confirm(token: str, db: Client = Depends(get_db)):
    confirm_email(db, token)
    return {"message": "Email confirmado com sucesso! Você já pode fazer login."}


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, db: Client = Depends(get_db)):
    token = await login_user(db, body.email, body.password, _client_ip(request))
    return {"access_token": token}
