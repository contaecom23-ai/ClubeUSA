from fastapi import Request
from slowapi import Limiter


def get_client_ip(request: Request) -> str:
    """Extrai IP real, suporta X-Forwarded-For para deploys atrás de proxy."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=get_client_ip, default_limits=["300/minute"])
