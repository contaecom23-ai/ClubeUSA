"""Dependências compartilhadas do FastAPI."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.config import settings

_bearer = HTTPBearer()


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    """
    Valida JWT emitido pelo Supabase (HS256).
    Retorna dict com user_id e email.
    Levanta 401 se inválido ou expirado.
    """
    token = creds.credentials
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
        )

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token sem identificador de usuário.")

    return {
        "user_id": user_id,
        "email": payload.get("email", ""),
        "email_confirmed": payload.get("email_confirmed_at") is not None,
    }
