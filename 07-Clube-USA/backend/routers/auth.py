from fastapi import APIRouter, Depends, HTTPException, Request

from ..database import get_supabase
from ..middleware.auth import get_current_user_id
from ..middleware.rate_limit import login_limiter, register_limiter
from ..models.user import AuthResponse, LoginRequest, RefreshRequest, RegisterRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/register", status_code=201)
async def register(request: Request, body: RegisterRequest):
    register_limiter.check(_client_ip(request))

    db = get_supabase()
    try:
        resp = db.auth.admin.create_user(
            {
                "email": str(body.email),
                "password": body.password,
                "email_confirm": False,
                "user_metadata": {"full_name": body.full_name},
            }
        )
        user = resp.user
        if not user:
            raise HTTPException(status_code=400, detail="Erro ao criar conta")

        db.table("profiles").insert(
            {
                "id": str(user.id),
                "full_name": body.full_name,
                "zip_code": body.zip_code,
            }
        ).execute()

    except HTTPException:
        raise
    except Exception as exc:
        msg = str(exc).lower()
        if "already" in msg or "duplicate" in msg:
            raise HTTPException(status_code=409, detail="Email já cadastrado")
        raise HTTPException(status_code=400, detail="Erro ao criar conta")

    return {
        "message": "Conta criada. Verifique seu email para confirmar o cadastro.",
        "email": str(body.email),
    }


@router.post("/login", response_model=AuthResponse)
async def login(request: Request, body: LoginRequest):
    login_limiter.check(_client_ip(request))

    db = get_supabase()
    try:
        resp = db.auth.sign_in_with_password(
            {"email": str(body.email), "password": body.password}
        )
        session = resp.session
        user = resp.user

        if not session or not user:
            raise HTTPException(status_code=401, detail="Email ou senha inválidos")

        if not user.email_confirmed_at:
            raise HTTPException(
                status_code=403,
                detail="Email não confirmado. Verifique sua caixa de entrada.",
            )

    except HTTPException:
        raise
    except Exception as exc:
        msg = str(exc).lower()
        if "invalid" in msg or "credentials" in msg or "not found" in msg:
            raise HTTPException(status_code=401, detail="Email ou senha inválidos")
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")

    return AuthResponse(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        user=UserResponse(id=str(user.id), email=user.email),
    )


@router.post("/refresh")
async def refresh_token(body: RefreshRequest):
    db = get_supabase()
    try:
        resp = db.auth.refresh_session(body.refresh_token)
        session = resp.session
        if not session:
            raise HTTPException(status_code=401, detail="Refresh token inválido")
        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Refresh token inválido ou expirado")


@router.get("/me")
async def get_me(user_id: str = Depends(get_current_user_id)):
    return {"user_id": user_id}
