from fastapi import APIRouter, Depends, HTTPException, Request, Response
from database import get_user_client, get_admin_client
from auth import get_current_user_id
from limiter import limiter
from models import (
    RegisterRequest,
    LoginRequest,
    ConfirmRequest,
    ProfileResponse,
    LoginResponse,
    MessageResponse,
)
from config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])

_CONFIRM_TYPES = {"email", "signup"}

# ─── Register ────────────────────────────────────────────────────────────────

@router.post("/register", response_model=MessageResponse, status_code=201)
@limiter.limit("5/minute")
async def register(request: Request, body: RegisterRequest):
    try:
        auth_resp = get_user_client().auth.sign_up(
            {
                "email": body.email,
                "password": body.password,
                "options": {
                    "email_redirect_to": f"{settings.SITE_URL}/confirm.html"
                },
            }
        )
    except Exception:
        # Não vaza se o email já existe (prevenção de enumeração)
        return MessageResponse(
            message="Se este email for válido, você receberá um link de confirmação em breve."
        )

    if not auth_resp.user:
        return MessageResponse(
            message="Se este email for válido, você receberá um link de confirmação em breve."
        )

    user_id = auth_resp.user.id

    # Cria perfil server-side (service_role bypassa RLS)
    try:
        get_admin_client().table("profiles").insert(
            {
                "id": user_id,
                "full_name": body.full_name,
                "us_state": body.us_state,
                "city": body.city,
            }
        ).execute()
    except Exception:
        # Perfil pode já existir em re-registros do mesmo email — não é erro fatal
        pass

    return MessageResponse(
        message="Cadastro recebido. Verifique seu email para confirmar a conta."
    )


# ─── Login ───────────────────────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest, response: Response):
    try:
        auth_resp = get_user_client().auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    if not auth_resp.session:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    session = auth_resp.session
    user = auth_resp.user

    # Token de acesso em cookie httpOnly (não acessível por JS — proteção XSS)
    response.set_cookie(
        key="access_token",
        value=session.access_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=3600,  # 1 hora (access token)
    )
    # Refresh token em cookie separado, caminho restrito
    response.set_cookie(
        key="refresh_token",
        value=session.refresh_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=7 * 24 * 3600,  # 7 dias
        path="/api/auth/refresh",
    )

    email_confirmed = (
        user.email_confirmed_at is not None if user else False
    )

    return LoginResponse(
        message="Login realizado com sucesso.",
        email_confirmed=email_confirmed,
    )


# ─── Refresh ─────────────────────────────────────────────────────────────────

@router.post("/refresh", response_model=MessageResponse)
async def refresh(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token ausente")

    try:
        auth_resp = get_user_client().auth.refresh_session(refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Refresh token inválido ou expirado")

    if not auth_resp.session:
        raise HTTPException(status_code=401, detail="Refresh token inválido ou expirado")

    session = auth_resp.session
    response.set_cookie(
        key="access_token",
        value=session.access_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=3600,
    )
    response.set_cookie(
        key="refresh_token",
        value=session.refresh_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=7 * 24 * 3600,
        path="/api/auth/refresh",
    )
    return MessageResponse(message="Token renovado com sucesso.")


# ─── Confirm email ────────────────────────────────────────────────────────────

@router.post("/confirm", response_model=MessageResponse)
async def confirm_email(body: ConfirmRequest):
    if body.type not in _CONFIRM_TYPES:
        raise HTTPException(status_code=400, detail="Tipo de confirmação inválido")

    try:
        otp_resp = get_user_client().auth.verify_otp(
            {"token_hash": body.token_hash, "type": body.type}
        )
    except Exception:
        raise HTTPException(
            status_code=400, detail="Token de confirmação inválido ou expirado"
        )

    if not otp_resp.user:
        raise HTTPException(
            status_code=400, detail="Token de confirmação inválido ou expirado"
        )

    return MessageResponse(message="Email confirmado com sucesso. Você já pode fazer login.")


# ─── Logout ──────────────────────────────────────────────────────────────────

@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response, _: str = Depends(get_current_user_id)):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token", path="/api/auth/refresh")
    return MessageResponse(message="Logout realizado com sucesso.")


# ─── Me ──────────────────────────────────────────────────────────────────────

@router.get("/me", response_model=ProfileResponse)
async def get_me(user_id: str = Depends(get_current_user_id)):
    # user_id vem do JWT verificado no servidor — nunca do input do cliente
    admin = get_admin_client()

    try:
        user_resp = admin.auth.admin.get_user_by_id(user_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if not user_resp.user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    auth_user = user_resp.user

    try:
        profile_resp = (
            admin.table("profiles").select("*").eq("id", user_id).single().execute()
        )
    except Exception:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")

    if not profile_resp.data:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")

    p = profile_resp.data
    return ProfileResponse(
        id=user_id,
        email=auth_user.email or "",
        full_name=p["full_name"],
        us_state=p.get("us_state"),
        city=p.get("city"),
        email_confirmed=auth_user.email_confirmed_at is not None,
    )
