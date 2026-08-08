import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.auth.router import router as auth_router
from app.config import get_settings
from app.users.router import router as users_router

logging.basicConfig(level=logging.INFO)

s = get_settings()

app = FastAPI(
    title="Clube USA API",
    description="Backend da plataforma para imigrantes brasileiros nos EUA.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=s.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Rotas públicas: /health, /auth/register, /auth/login, /auth/confirm-email
# Todas as outras requerem Bearer token (via Depends nas rotas protegidas).
app.include_router(auth_router)
app.include_router(users_router)


@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok", "version": "0.1.0"}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    import logging
    logging.getLogger(__name__).exception("Erro não tratado: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno. Tente novamente em instantes."},
    )
