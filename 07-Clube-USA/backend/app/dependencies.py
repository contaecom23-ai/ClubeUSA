from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from supabase import Client, create_client

from app.config import Settings, get_settings

security = HTTPBearer()

_supabase_client: Client | None = None


def get_supabase(settings: Settings = Depends(get_settings)) -> Client:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
    return _supabase_client


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    settings: Settings = Depends(get_settings),
) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_iss": False},
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    if not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Token inválido")

    return payload
