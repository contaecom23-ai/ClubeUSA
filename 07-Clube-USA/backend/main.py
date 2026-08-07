from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from config import get_settings
from models import LoginRequest, RegisterRequest, TokenResponse
from routes.auth import confirm_email_handler, login_handler, register_handler
from routes.profile import router as profile_router
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# ------------------------------------------------------------------ App
app = FastAPI(
    title="Clube USA API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
)

# ------------------------------------------------------------------ Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ------------------------------------------------------------------ CORS (restrito a origens conhecidas)
s = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=s.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


# ------------------------------------------------------------------ Security headers (pure ASGI — evita conflito com ExceptionMiddleware)
class SecurityHeadersMiddleware:
    """Injeta headers de segurança em toda resposta HTTP via ASGI puro.
    Não usa BaseHTTPMiddleware para evitar o bug de RuntimeError com
    exception handlers no Starlette 0.37+.
    """
    _HEADERS = [
        (b"x-content-type-options", b"nosniff"),
        (b"x-frame-options", b"DENY"),
        (b"x-xss-protection", b"1; mode=block"),
        (b"referrer-policy", b"strict-origin-when-cross-origin"),
    ]

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(self._HEADERS)
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_security_headers)


app.add_middleware(SecurityHeadersMiddleware)


# ------------------------------------------------------------------ Rotas públicas (lista explícita e mínima)
@app.get("/health", tags=["status"])
def health():
    return {"status": "ok"}


@app.post("/auth/register", response_model=TokenResponse, tags=["auth"])
@limiter.limit(s.RATE_LIMIT_REGISTER)
def register(request: Request, body: RegisterRequest):
    return register_handler(request, body)


@app.get("/auth/confirm-email", tags=["auth"])
def confirm_email(token: str = ""):
    return confirm_email_handler(token)


@app.post("/auth/login", response_model=TokenResponse, tags=["auth"])
@limiter.limit(s.RATE_LIMIT_LOGIN)
def login(request: Request, body: LoginRequest):
    return login_handler(request, body)


# ------------------------------------------------------------------ Rotas protegidas (exigem JWT)
app.include_router(profile_router)
