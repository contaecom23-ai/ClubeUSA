from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service as auth_service
from app.deps import get_db
from app.rate_limit import limiter
from app.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
@limiter.limit("3/minute")
async def register(
    request: Request,
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await auth_service.register_user(db, data)
    return {
        "message": "Cadastro realizado! Verifique seu email para confirmar a conta.",
        "user_id": str(user.id),
    }


@router.get("/confirm-email/{token}")
async def confirm_email(token: str, db: AsyncSession = Depends(get_db)):
    await auth_service.confirm_email(db, token)
    return {"message": "Email confirmado com sucesso! Faça login para continuar."}


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    ua = request.headers.get("user-agent", "")
    ip = request.client.host if request.client else ""
    access_token, refresh_token = await auth_service.login_user(db, data.email, data.password, ua, ip)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    access_token, refresh_token = await auth_service.refresh_tokens(db, data.refresh_token)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout")
async def logout(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.logout_user(db, data.refresh_token)
    return {"message": "Logout realizado com sucesso"}
