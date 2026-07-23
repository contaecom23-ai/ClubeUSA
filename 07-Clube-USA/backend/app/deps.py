from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import get_settings
from .db import get_conn
from .jwt_utils import decode as jwt_decode

_bearer = HTTPBearer()


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    s = get_settings()
    try:
        payload = jwt_decode(creds.credentials, s.SECRET_KEY)
        user_id: str = payload.get("sub", "")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido")
    except ValueError:
        raise HTTPException(status_code=401, detail="Token inválido")

    async with get_conn() as conn:
        row = await conn.fetchrow(
            "SELECT id, email, full_name, email_confirmed, referral_code, created_at "
            "FROM users WHERE id = $1 AND is_active = TRUE",
            user_id,
        )
    if not row:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return dict(row)
