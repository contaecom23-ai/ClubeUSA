import logging
from supabase import Client
from fastapi import HTTPException, status
from analytics.service import track_event
from auth.schemas import RegisterRequest, LoginRequest, TokenResponse
from referrals.service import generate_unique_slug
from validation.service import is_disposable_email

logger = logging.getLogger(__name__)


def register_user(supabase: Client, data: RegisterRequest) -> dict:
    if is_disposable_email(data.email):
        domain = data.email.lower().split("@")[-1]
        track_event(
            supabase,
            "registration.blocked",
            metadata={"reason": "disposable_email", "domain": domain},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email temporário não é permitido. Use um email permanente.",
        )

    try:
        response = supabase.auth.sign_up(
            {"email": data.email, "password": data.password}
        )
    except Exception as e:
        logger.error("sign_up error: %s", type(e).__name__)
        # Não vazar detalhes do erro para evitar enumeração de emails
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível criar a conta. Tente novamente.",
        )

    if not response.user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cadastro falhou. Tente novamente.",
        )

    user_id = response.user.id

    referral_slug = generate_unique_slug(supabase, data.first_name)

    profile_data: dict = {
        "id": user_id,
        "first_name": data.first_name.strip(),
        "last_name": data.last_name.strip(),
        "zip_code": data.zip_code.strip(),
        "phone": data.phone.strip(),
        "referral_slug": referral_slug,
    }

    # Valida o código de referral recebido sem falhar o cadastro se inválido
    referral_valid = False
    if data.referred_by_slug:
        try:
            ref_check = (
                supabase.table("profiles")
                .select("id")
                .eq("referral_slug", data.referred_by_slug)
                .execute()
            )
            if ref_check.data:
                profile_data["referred_by_slug"] = data.referred_by_slug
                referral_valid = True
        except Exception as e:
            logger.warning("ref slug validation error: %s", type(e).__name__)

    try:
        supabase.table("profiles").insert(profile_data).execute()
    except Exception as e:
        logger.error("profile insert failed for user %s: %s", user_id, type(e).__name__)
        # Usuário existe no auth mas sem perfil — inconsistência gerenciável.
        # O perfil será criado no primeiro GET /users/me (ver users/service.py).
        # Registrar aqui para monitoramento; não falhar o cadastro.

    # Analytics: fire-and-forget, nunca bloqueia o cadastro
    track_event(supabase, "user.registered", user_id=user_id)
    if referral_valid:
        track_event(
            supabase, "referral.converted",
            user_id=user_id,
            metadata={"referred_by_slug": data.referred_by_slug},
        )

    # Mensagem genérica independente se o email já existia (anti-enumeração)
    return {"message": "Cadastro recebido! Verifique seu email para confirmar a conta."}


def login_user(supabase: Client, data: LoginRequest) -> TokenResponse:
    try:
        response = supabase.auth.sign_in_with_password(
            {"email": data.email, "password": data.password}
        )
    except Exception as e:
        logger.warning("sign_in failed: %s", type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
        )

    if not response.session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
        )

    # Analytics: registra login (user_id vem da sessão, nunca do cliente)
    session_user = getattr(response.session, "user", None)
    if session_user and getattr(session_user, "id", None):
        track_event(supabase, "user.logged_in", user_id=str(session_user.id))

    return TokenResponse(
        access_token=response.session.access_token,
        refresh_token=response.session.refresh_token,
        expires_in=response.session.expires_in or 3600,
    )


def refresh_access_token(supabase: Client, refresh_token: str) -> TokenResponse:
    try:
        response = supabase.auth.refresh_session(refresh_token)
    except Exception as e:
        logger.warning("refresh_session failed: %s", type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado",
        )

    if not response.session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado",
        )

    return TokenResponse(
        access_token=response.session.access_token,
        refresh_token=response.session.refresh_token,
        expires_in=response.session.expires_in or 3600,
    )
