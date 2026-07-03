import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.auth.router import router as auth_router
from app.config import settings
from app.database import close_db_pool, create_db_pool
from app.rate_limiter import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.DATABASE_URL:
        await create_db_pool()
    yield
    await close_db_pool()


app = FastAPI(
    title="Clube USA API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda req, exc: __import__("fastapi").responses.JSONResponse(
    status_code=429,
    content={"detail": "Muitas requisições. Aguarde e tente novamente."},
))
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

# Servir frontend estático
_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(_frontend_dir):
    app.mount("/static", StaticFiles(directory=_frontend_dir), name="static")

    @app.get("/")
    async def root():
        return FileResponse(os.path.join(_frontend_dir, "index.html"))

    @app.get("/login")
    async def login_page():
        return FileResponse(os.path.join(_frontend_dir, "login.html"))

    @app.get("/confirm")
    async def confirm_page():
        return FileResponse(os.path.join(_frontend_dir, "confirm.html"))


@app.get("/health", tags=["infra"])
async def health():
    return {"status": "ok", "version": "0.1.0"}
