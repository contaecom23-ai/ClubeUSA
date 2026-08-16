# clubeusa/api/deps.py
import os
import hmac
from fastapi import Depends, Header, HTTPException
from supabase import create_client


def _sb():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def get_current_member(authorization: str = Header(None)) -> dict:
    from utils.security import verify_token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token nao fornecido.")
    token = authorization.split(" ", 1)[1]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalido ou expirado.")
    return payload


def require_vip(member: dict = Depends(get_current_member)) -> dict:
    if member.get("plan") != "vip":
        raise HTTPException(status_code=403, detail="Recurso exclusivo para membros VIP.")
    return member


def require_paid_plan(member: dict = Depends(get_current_member)) -> dict:
    if member.get("plan") not in ("vip",):
        raise HTTPException(status_code=403, detail="Faca upgrade do seu plano.")
    return member


def require_admin(authorization: str = Header(None)) -> None:
    secret = os.environ.get("ADMIN_SECRET", "")
    expected = f"Bearer {secret}"
    if not secret or not hmac.compare_digest(
        (authorization or "").encode(), expected.encode()
    ):
        raise HTTPException(status_code=401, detail="Acesso negado.")
