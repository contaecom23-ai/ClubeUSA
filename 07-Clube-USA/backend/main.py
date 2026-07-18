from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.auth.router import router as auth_router
from app.config import settings
from app.middleware import SecurityHeadersMiddleware
from app.users.router import router as users_router

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Clube USA API",
    version="0.1.0",
    # Disable docs in production — enable only when needed
    docs_url="/docs" if settings.EMAIL_SERVICE == "log" else None,
    redoc_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(users_router, prefix="/users", tags=["users"])


@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok", "version": "0.1.0"}
