from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app import database as db
from app.config import settings
from app.routers import auth, users

# ── Rate limiter global ───────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.startup()
    yield
    await db.shutdown()


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Clube USA API",
    description="API da plataforma Clube USA — para imigrantes brasileiros nos EUA.",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# ── Rotas públicas da API ─────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(users.router)


# Rate-limit explícito em rotas sensíveis
@app.middleware("http")
async def rate_limit_sensitive(request, call_next):
    return await call_next(request)


@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok", "version": "0.1.0"}


# ── Frontend estático ─────────────────────────────────────────────────────────
FRONTEND = Path(__file__).parent.parent / "frontend"
if FRONTEND.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND / "assets")), name="assets")

    @app.get("/", include_in_schema=False)
    async def home():
        return FileResponse(str(FRONTEND / "index.html"))

    @app.get("/login.html", include_in_schema=False)
    async def login_page():
        return FileResponse(str(FRONTEND / "login.html"))

    @app.get("/confirm-email.html", include_in_schema=False)
    async def confirm_page():
        return FileResponse(str(FRONTEND / "confirm-email.html"))

    @app.get("/profile.html", include_in_schema=False)
    async def profile_page():
        return FileResponse(str(FRONTEND / "profile.html"))
