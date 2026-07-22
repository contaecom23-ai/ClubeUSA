"""
Ponto de entrada da API Clube USA.
Rotas públicas explícitas: /health, /auth/register, /auth/confirm-email, /auth/login, /auth/refresh.
Todas as demais exigem Bearer token válido (aplicado via Depends em cada router).
"""
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.auth.router import router as auth_router
from app.config import settings
from app.database import init_db
from app.users.router import router as users_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Clube USA API",
    description="API da plataforma para imigrantes brasileiros nos EUA",
    version="0.1.0",
    # Desabilitar docs em produção (deixar configurável)
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Rate limiter ─────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS — restrito a origens conhecidas ─────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# ── Security headers ─────────────────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# ── Startup ───────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    await init_db()
    logger.info("Clube USA API iniciada — versão 0.1.0")


# ── Routers ───────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(users_router)


# ── Health check (rota pública) ───────────────────────────────────────────
@app.get("/health", tags=["infra"])
async def health():
    return {"status": "ok", "version": "0.1.0"}
