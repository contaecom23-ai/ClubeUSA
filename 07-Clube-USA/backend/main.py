import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.auth import router as auth_router
from app.config import get_settings
from app.db import close_pool, init_pool
from app.limiter import limiter
from app.users import router as users_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    logger.info("Connecting to database...")
    await init_pool(s.DATABASE_URL)
    logger.info("Database pool ready.")
    yield
    await close_pool()
    logger.info("Database pool closed.")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Clube USA API",
    version="0.1.0",
    lifespan=lifespan,
    # Hide docs in production
    docs_url=None if get_settings().ENV == "production" else "/docs",
    redoc_url=None if get_settings().ENV == "production" else "/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────────────────────────

s = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=s.allowed_origins_list(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# ── Security headers ──────────────────────────────────────────────────────────

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # CSP: allow inline scripts/styles only for the frontend HTML pages
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self'"
    )
    return response

# ── Rate-limited auth routes ──────────────────────────────────────────────────
# slowapi decorators live in the route handlers; we just need to apply limits per-endpoint.
# The decorators in auth.py use @limiter.limit("5/minute") etc.

# ── Routers ───────────────────────────────────────────────────────────────────

# ── Health check (must be before static mount) ────────────────────────────────

@app.get("/status", tags=["health"])
async def status():
    return {"status": "ok", "version": "0.1.0"}


app.include_router(auth_router)
app.include_router(users_router)

# ── Static frontend (catch-all — must be last) ────────────────────────────────

frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
