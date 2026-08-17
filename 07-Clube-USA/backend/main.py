from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from auth.router import router as auth_router
from config import settings
from core.limiter import limiter
from referrals.router import router as referrals_router
from users.router import router as users_router

app = FastAPI(
    title="Clube USA API",
    version="0.2.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router, prefix="/auth")
app.include_router(users_router, prefix="/users")
app.include_router(referrals_router, prefix="/referrals")


@app.get("/", tags=["health"])
def root():
    return {"product": "Clube USA", "version": "0.2.0"}


@app.get("/health", tags=["health"])
def health():
    return {"status": "healthy"}
