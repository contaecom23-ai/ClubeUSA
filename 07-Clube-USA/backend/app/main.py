from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import settings
from app.auth.router import router as auth_router
from app.users.router import router as users_router

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Clube USA API",
    version="0.1.0",
    docs_url="/docs" if settings.APP_ENV == "development" else None,
    redoc_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,
)

# Rotas públicas: /status, /auth/register, /auth/login, /auth/verify-email,
#                 /auth/resend-verification, /auth/refresh
app.include_router(auth_router, prefix="/auth", tags=["auth"])
# Rotas protegidas: todas exigem Bearer token válido (validado em deps.py)
app.include_router(users_router, prefix="/users", tags=["users"])


@app.get("/status", tags=["health"])
def status():
    return {"status": "ok", "version": "0.1.0"}
