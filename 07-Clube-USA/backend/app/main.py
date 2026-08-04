import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .config import settings
from .routers import auth, users

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Clube USA API v0.1 iniciando — BASE_URL=%s", settings.BASE_URL)
    yield
    logger.info("Clube USA API encerrando")


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Clube USA API",
    version="0.1.0",
    description="API para imigrantes brasileiros nos EUA",
    lifespan=lifespan,
    docs_url="/docs" if "localhost" in settings.BASE_URL else None,
    redoc_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# Rotas públicas: /health, /auth/*
# Rotas protegidas: /users/* (requerem Bearer token)
app.include_router(auth.router)
app.include_router(users.router)


@app.get("/health", tags=["infra"])
async def health():
    return {"status": "ok", "version": "0.1.0"}
