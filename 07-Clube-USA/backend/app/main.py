import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .config import settings
from .routers import auth, users

logging.basicConfig(level=logging.INFO)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Clube USA API",
    version="0.1.0",
    # Desabilita Swagger em produção para não expor schema desnecessariamente
    docs_url="/docs" if settings.is_dev else None,
    redoc_url="/redoc" if settings.is_dev else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
# Rotas públicas: /status, /auth/register, /auth/login, /auth/confirm-email, /auth/resend-confirmation
# Rotas autenticadas: /users/*
app.include_router(auth.router)
app.include_router(users.router)


@app.get("/status")
async def status_check() -> dict:
    return {"status": "ok", "version": "0.1.0"}
