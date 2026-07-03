from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.dependencies import get_current_user
from app.auth.schemas import (
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResendConfirmationRequest,
    TokenResponse,
    UserProfile,
)
from app.auth.service import (
    authenticate_user,
    confirm_email,
    create_jwt,
    register_user,
    reset_confirmation_token,
)
from app.database import get_pool
from app.email_service import send_confirmation_email
from app.rate_limiter import limiter

router = APIRouter()

# Rotas públicas com rate-limit agressivo (anti-fraude / brute-force)
_REGISTER_LIMIT = "3/hour"
_LOGIN_LIMIT = "5/minute"
_RESEND_LIMIT = "3/hour"


@router.post("/register", response_model=MessageResponse, status_code=201)
@limiter.limit(_REGISTER_LIMIT)
async def register(
    request: Request,
    body: RegisterRequest,
    pool=Depends(get_pool),
):
    result = await register_user(
        pool,
        email=body.email,
        password=body.password,
        full_name=body.full_name,
        zip_code=body.zip_code,
    )

    if "error" not in result:
        # Envia email de confirmação (falha silenciosa — usuário já está no banco)
        await send_confirmation_email(
            to_email=result["user"]["email"],
            full_name=result["user"]["full_name"],
            token=result["confirmation_token"],
        )

    # Mesma resposta para email já cadastrado ou novo — evita enumeração
    return MessageResponse(
        message="Cadastro realizado! Verifique seu email para confirmar sua conta."
    )


@router.get("/confirm", response_model=TokenResponse)
@limiter.limit("20/hour")
async def confirm_email_route(
    request: Request,
    token: str,
    pool=Depends(get_pool),
):
    user = await confirm_email(pool, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Link inválido ou expirado. Solicite um novo email de confirmação.",
        )

    access_token, expires_in = create_jwt(str(user["id"]), user["email"])
    return TokenResponse(access_token=access_token, expires_in=expires_in)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(_LOGIN_LIMIT)
async def login(
    request: Request,
    body: LoginRequest,
    pool=Depends(get_pool),
):
    user = await authenticate_user(pool, body.email, body.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
        )

    if not user["email_confirmed"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email não confirmado. Verifique sua caixa de entrada ou solicite reenvio.",
        )

    access_token, expires_in = create_jwt(str(user["id"]), user["email"])
    return TokenResponse(access_token=access_token, expires_in=expires_in)


@router.post("/resend-confirmation", response_model=MessageResponse)
@limiter.limit(_RESEND_LIMIT)
async def resend_confirmation(
    request: Request,
    body: ResendConfirmationRequest,
    pool=Depends(get_pool),
):
    new_token = await reset_confirmation_token(pool, body.email)

    if new_token:
        # Busca nome do usuário para o email
        from asyncpg import Pool
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT full_name FROM users WHERE email = $1", body.email.lower()
            )
        if row:
            await send_confirmation_email(
                to_email=body.email.lower(),
                full_name=row["full_name"],
                token=new_token,
            )

    # Sempre mesma resposta — evita enumeração
    return MessageResponse(
        message="Se existir uma conta não confirmada com este email, enviaremos um novo link."
    )


@router.get("/me", response_model=UserProfile)
async def get_profile(current_user: dict = Depends(get_current_user)):
    return UserProfile(
        id=str(current_user["id"]),
        email=current_user["email"],
        full_name=current_user["full_name"],
        zip_code=current_user.get("zip_code"),
        email_confirmed=current_user["email_confirmed"],
        created_at=current_user["created_at"].isoformat(),
    )
