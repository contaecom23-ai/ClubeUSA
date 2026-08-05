from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .auth.router import router as auth_router
from .config import get_settings
from .limiter import limiter
from .users.router import router as users_router

settings = get_settings()

app = FastAPI(
    title="Clube USA API",
    version="0.1.0",
    # Hide docs in production
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

# ── Public routes (no auth required) ────────────────────────────────────────

@app.get("/status", include_in_schema=False)
def health():
    return {"status": "ok", "service": "clube-usa-api", "version": "0.1.0"}


# ── Feature routers ──────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(users_router)
