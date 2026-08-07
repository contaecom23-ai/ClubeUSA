from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database import Database
from app.limiter import rate_limiter
from app.services.auth import decode_access_token

_bearer = HTTPBearer()


def get_db(request: Request) -> Database:
    return request.app.state.db


def _client_ip(request: Request) -> str:
    # In tests TestClient sets no real peer, so fall back to a sentinel
    return request.client.host if request.client else "testclient"


def limit_register(request: Request) -> None:
    ip = _client_ip(request)
    if not rate_limiter.is_allowed(f"reg:{ip}", max_calls=5, period_seconds=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de cadastro. Tente novamente em 1 minuto.",
        )


def limit_login(request: Request) -> None:
    ip = _client_ip(request)
    if not rate_limiter.is_allowed(f"login:{ip}", max_calls=10, period_seconds=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de login. Tente novamente em 1 minuto.",
        )


def limit_resend(request: Request) -> None:
    ip = _client_ip(request)
    if not rate_limiter.is_allowed(f"resend:{ip}", max_calls=3, period_seconds=3600):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas solicitações. Tente novamente em 1 hora.",
        )


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido.")
    return user_id


def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: Database = Depends(get_db),
) -> dict:
    user = db.get_user_by_id(user_id)
    if not user or not user.get("is_active"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado.")
    return user
