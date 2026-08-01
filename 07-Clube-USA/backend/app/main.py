import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .config import get_settings
from .database import close_pool, create_pool
from .limiter import limiter
from .auth.router import router as auth_router
from .users.router import router as users_router

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await create_pool()
        log.info("Pool de banco de dados inicializado.")
    except Exception:
        log.exception("Falha ao conectar ao banco — verifique DATABASE_URL")
    yield
    await close_pool()


def create_app() -> FastAPI:
    s = get_settings()

    app = FastAPI(
        title="Clube USA API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if s.debug else None,
        redoc_url="/redoc" if s.debug else None,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    @app.get("/health", tags=["infra"])
    async def health():
        return {"status": "ok", "service": "clube-usa-api"}

    app.include_router(auth_router)
    app.include_router(users_router)

    return app


app = create_app()
