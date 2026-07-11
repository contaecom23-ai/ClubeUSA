"""
Clube USA API — FastAPI application factory.

Public routes (no auth required):
  GET  /health
  POST /auth/register
  POST /auth/login
  POST /auth/verify-email
  POST /auth/resend-confirmation

Everything else requires Authorization: Bearer <token>.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from .config import settings
from .middleware.security import SecurityHeadersMiddleware
from .routers import auth, profile


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        docs_url="/docs" if settings.DEBUG else None,  # disable Swagger in prod
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
    )

    # ── Rate limiter ───────────────────────────────────────────────────────
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # ── CORS — restricted to known origins ────────────────────────────────
    allowed_origins = settings.get_allowed_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # ── Security headers ──────────────────────────────────────────────────
    app.add_middleware(SecurityHeadersMiddleware)

    # ── Routes ────────────────────────────────────────────────────────────
    app.include_router(auth.router, prefix="/api")
    app.include_router(profile.router, prefix="/api")

    @app.get("/health", tags=["system"])
    async def health() -> dict:
        return {"status": "ok"}

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Not found."})

    return app


app = create_app()
