import os

import jwt as pyjwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_security = HTTPBearer()


def _get_jwt_secret() -> str:
    secret = os.environ.get("SUPABASE_JWT_SECRET", "")
    if not secret:
        raise RuntimeError("SUPABASE_JWT_SECRET não configurado — não inicie o servidor sem ela")
    return secret


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(_security),
) -> dict:
    """
    Valida o JWT emitido pelo Supabase Auth.
    Retorna {'user_id': str, 'email': str, 'role': str}.
    Nunca confia no user_id vindo do corpo da request — sempre do token.
    """
    token = credentials.credentials
    try:
        payload = pyjwt.decode(
            token,
            _get_jwt_secret(),
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
        )
    except pyjwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sem identidade",
        )

    return {
        "user_id": user_id,
        "email": payload.get("email", ""),
        "role": payload.get("role", "authenticated"),
    }
