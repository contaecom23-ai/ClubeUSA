import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from config import settings
from database import close_db, get_pool, init_db
from email_service import send_confirmation_email
from schemas import (
    ConfirmEmailRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserProfile,
)
from security import (
    create_access_token,
    decode_access_token,
    generate_email_token,
    hash_password,
    verify_password,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Banco de dados inicializado")
    yield
    await close_db()


app = FastAPI(
    title="Clube USA API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Authorization", "Content-Type"],
)

_bearer = HTTPBearer()


async def _current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado")
    return user_id


async def _fetch_user_profile(user_id: str) -> UserProfile:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, email, first_name, last_name, phone, zip_code, city, state,
                   email_confirmed, created_at
            FROM users WHERE id = $1 AND is_active = TRUE
            """,
            uuid.UUID(user_id),
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return UserProfile(
        id=str(row["id"]),
        email=row["email"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        phone=row["phone"],
        zip_code=row["zip_code"],
        city=row["city"],
        state=row["state"],
        email_confirmed=row["email_confirmed"],
        created_at=row["created_at"].isoformat(),
    )


# ---------------------------------------------------------------------------
# Rotas públicas
# ---------------------------------------------------------------------------

@app.get("/status", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "clube-usa-api", "version": "0.1.0"}


@app.post(
    "/api/v1/auth/register",
    status_code=201,
    response_model=MessageResponse,
    tags=["Auth"],
)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
async def register(request: Request, body: RegisterRequest):
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1", body.email.lower()
        )
        if existing:
            # Não revela se o email existe para impedir enumeração de cadastros.
            # Mesma mensagem que o sucesso — usuário real vai receber o email.
            return MessageResponse(
                message="Se este email não estiver cadastrado, você receberá um link de confirmação."
            )

        user_id = uuid.uuid4()
        token = generate_email_token()
        token_expires = datetime.now(timezone.utc) + timedelta(hours=24)

        await conn.execute(
            """
            INSERT INTO users
              (id, email, password_hash, first_name, last_name, phone, zip_code,
               email_confirm_token, email_confirm_token_expires_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            user_id,
            body.email.lower(),
            hash_password(body.password),
            body.first_name,
            body.last_name,
            body.phone,
            body.zip_code,
            token,
            token_expires,
        )

    await send_confirmation_email(body.email.lower(), body.first_name, token)

    return MessageResponse(
        message="Cadastro realizado! Verifique seu email para confirmar a conta."
    )


@app.post(
    "/api/v1/auth/confirm-email",
    response_model=MessageResponse,
    tags=["Auth"],
)
async def confirm_email(body: ConfirmEmailRequest):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, email_confirmed, email_confirm_token_expires_at
            FROM users
            WHERE email_confirm_token = $1
            """,
            body.token,
        )

        if not row:
            raise HTTPException(status_code=400, detail="Token de confirmação inválido")

        if row["email_confirmed"]:
            return MessageResponse(message="Email já confirmado. Faça login.")

        if row["email_confirm_token_expires_at"] < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=400,
                detail="Token expirado. Faça novo cadastro ou entre em contato com o suporte.",
            )

        await conn.execute(
            """
            UPDATE users
            SET email_confirmed = TRUE,
                email_confirm_token = NULL,
                email_confirm_token_expires_at = NULL
            WHERE id = $1
            """,
            row["id"],
        )

    return MessageResponse(message="Email confirmado com sucesso! Você já pode fazer login.")


@app.post(
    "/api/v1/auth/login",
    response_model=TokenResponse,
    tags=["Auth"],
)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login(request: Request, body: LoginRequest):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, email, password_hash, first_name, email_confirmed, is_active
            FROM users WHERE email = $1
            """,
            body.email.lower(),
        )

    # Mesma mensagem para email errado e senha errada (impede enumeração)
    _INVALID = HTTPException(status_code=401, detail="Credenciais inválidas")

    if not row:
        raise _INVALID
    if not verify_password(body.password, row["password_hash"]):
        raise _INVALID
    if not row["is_active"]:
        raise HTTPException(status_code=403, detail="Conta desativada")

    return TokenResponse(
        access_token=create_access_token(str(row["id"])),
        user_id=str(row["id"]),
        email=row["email"],
        first_name=row["first_name"],
        email_confirmed=row["email_confirmed"],
    )


# ---------------------------------------------------------------------------
# Rotas autenticadas
# ---------------------------------------------------------------------------

@app.get(
    "/api/v1/auth/me",
    response_model=UserProfile,
    tags=["Profile"],
)
async def get_me(user_id: str = Depends(_current_user_id)):
    return await _fetch_user_profile(user_id)


@app.put(
    "/api/v1/auth/profile",
    response_model=UserProfile,
    tags=["Profile"],
)
async def update_profile(
    body: UpdateProfileRequest,
    user_id: str = Depends(_current_user_id),
):
    updates: dict = {}
    if body.first_name is not None:
        updates["first_name"] = body.first_name
    if body.last_name is not None:
        updates["last_name"] = body.last_name
    if body.phone is not None:
        updates["phone"] = body.phone
    if body.zip_code is not None:
        updates["zip_code"] = body.zip_code
    if body.city is not None:
        updates["city"] = body.city
    if body.state is not None:
        updates["state"] = body.state

    if updates:
        keys = list(updates.keys())
        values = list(updates.values())
        set_clause = ", ".join(f"{k} = ${i + 1}" for i, k in enumerate(keys))
        values.append(uuid.UUID(user_id))

        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                f"UPDATE users SET {set_clause} WHERE id = ${len(values)}",
                *values,
            )

    return await _fetch_user_profile(user_id)


# ---------------------------------------------------------------------------
# Frontend estático (deve ser montado por último)
# ---------------------------------------------------------------------------

_frontend_dir = Path(__file__).parent.parent / "frontend"
if _frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
