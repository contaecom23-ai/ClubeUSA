import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from core.config import get_settings
from core.limiter import limiter
from core.security import get_current_user_id
from core.supabase_client import get_supabase
from models.user import LoginRequest, RegisterRequest, UpdateProfileRequest, UserProfile

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/auth", tags=["auth"])

# ─── Rotas públicas ────────────────────────────────────────────────────────────


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
async def register(request: Request, body: RegisterRequest):
    """
    Cria conta + perfil mínimo. Supabase envia email de confirmação.
    rate-limit: 5/min por IP (anti brute-force / anti-fraude).
    """
    sb = get_supabase()

    try:
        auth_response = sb.auth.sign_up(
            {
                "email": body.email,
                "password": body.password,
                "options": {
                    "email_redirect_to": f"{settings.FRONTEND_URL}/confirm.html"
                },
            }
        )
    except Exception as exc:
        logger.warning("Falha no sign_up Supabase: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível criar a conta. Email já cadastrado ou dados inválidos.",
        )

    if not auth_response.user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível criar a conta.",
        )

    user_id = auth_response.user.id

    try:
        sb.table("users_profile").insert(
            {
                "user_id": user_id,
                "full_name": body.full_name,
                "email": body.email,
            }
        ).execute()
    except Exception as exc:
        logger.error("Falha ao criar perfil para user_id=%s: %s", user_id, exc)
        # Limpeza: remove usuário órfão do auth
        try:
            sb.auth.admin.delete_user(user_id)
        except Exception:
            logger.error("Falha ao remover usuário órfão user_id=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao salvar perfil. Tente novamente.",
        )

    return {
        "message": "Cadastro realizado! Verifique seu email para confirmar a conta."
    }


@router.post("/login")
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login(request: Request, body: LoginRequest):
    """
    Autentica com email + senha. Retorna access_token (TTL ~7d, controlado pelo Supabase)
    e refresh_token. Tokens armazenados APENAS no cliente.
    """
    sb = get_supabase()

    try:
        auth_response = sb.auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
    except Exception:
        # Nunca revele se é email ou senha incorretos (timing attack / user enumeration)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not auth_response.session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos.",
        )

    return {
        "access_token": auth_response.session.access_token,
        "refresh_token": auth_response.session.refresh_token,
        "token_type": "bearer",
    }


# ─── Rotas autenticadas ────────────────────────────────────────────────────────


@router.get("/me", response_model=UserProfile)
async def me(user_id: str = Depends(get_current_user_id)):
    """
    Retorna perfil do usuário autenticado.
    user_id vem SEMPRE do JWT validado (nunca do request).
    """
    sb = get_supabase()

    result = (
        sb.table("users_profile")
        .select("user_id, full_name, email")
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado.",
        )

    # email_confirmed vem do Supabase Auth (fonte de verdade)
    try:
        auth_user = sb.auth.admin.get_user_by_id(user_id)
        email_confirmed = (
            auth_user.user.email_confirmed_at is not None
            if auth_user.user
            else False
        )
    except Exception:
        email_confirmed = False

    return UserProfile(
        user_id=user_id,
        email=result.data["email"],
        full_name=result.data["full_name"],
        email_confirmed=email_confirmed,
    )


@router.put("/me", response_model=UserProfile)
async def update_profile(
    body: UpdateProfileRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Atualiza nome do perfil autenticado."""
    sb = get_supabase()

    result = (
        sb.table("users_profile")
        .update({"full_name": body.full_name})
        .eq("user_id", user_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado.",
        )

    row = result.data[0]

    try:
        auth_user = sb.auth.admin.get_user_by_id(user_id)
        email_confirmed = (
            auth_user.user.email_confirmed_at is not None
            if auth_user.user
            else False
        )
    except Exception:
        email_confirmed = False

    return UserProfile(
        user_id=user_id,
        email=row["email"],
        full_name=row["full_name"],
        email_confirmed=email_confirmed,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(user_id: str = Depends(get_current_user_id)):
    """
    Invalida todas as sessões do usuário no Supabase (server-side).
    O cliente deve descartar os tokens localmente também.
    """
    sb = get_supabase()
    try:
        sb.auth.admin.sign_out(user_id)
    except Exception:
        # Best-effort: o token expirará naturalmente mesmo que falhe
        pass
    return None
