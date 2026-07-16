import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.database import get_pool, close_pool
from app.routes import auth, profile

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Limiter global — disponível para todos os routers via app.state
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_pool()
    logger.info("Conexão com banco de dados estabelecida.")
    yield
    await close_pool()
    logger.info("Conexão com banco de dados encerrada.")


app = FastAPI(
    title="Clube USA API",
    version="0.1.0",
    description="API para a plataforma Clube USA — imigrantes brasileiros nos EUA.",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url=None,
)

# ---------------------------------------------------------------------------
# Rate limiting (SlowAPI)
# ---------------------------------------------------------------------------
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ---------------------------------------------------------------------------
# CORS — restrito a origens conhecidas
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# ---------------------------------------------------------------------------
# Security headers em toda resposta
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(profile.router)


@app.get("/", include_in_schema=False)
async def root():
    return {"service": "Clube USA API", "version": "0.1.0", "status": "ok"}


@app.get("/health", tags=["infra"])
async def health():
    return {"status": "ok"}
