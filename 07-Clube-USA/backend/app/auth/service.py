"""
Lógica de autenticação via Supabase Auth.
Toda operação acontece server-side — nunca expõe service_role ao cliente.
"""
from fastapi import HTTPException, status
from gotrue.errors import AuthApiError
from app.database import get_auth_client
from app.auth.schemas import RegisterRequest, LoginRequest, TokenResponse


def register_user(data: RegisterRequest) -> dict:
    """
    Cria usuário no Supabase Auth.
    O trigger do banco cria a linha em public.profiles automaticamente.
    Retorna mensagem — o token só é emitido após verificar email.
    """
    client = get_auth_client()
    try:
        resp = client.auth.sign_up({
            "email": data.email,
            "password": data.password,
            "options": {
                "data": {"full_name": data.full_name},
            },
        })
    except AuthApiError as e:
        msg = str(e).lower()
        if "already registered" in msg or "already exists" in msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este e-mail já está cadastrado.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao criar conta. Tente novamente.",
        )

    if resp.user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível criar a conta.",
        )

    return {"message": "Cadastro realizado! Verifique seu e-mail para ativar a conta."}


def login_user(data: LoginRequest) -> TokenResponse:
    client = get_auth_client()
    try:
        resp = client.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password,
        })
    except AuthApiError as e:
        msg = str(e).lower()
        if "invalid" in msg or "credentials" in msg:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha incorretos.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao fazer login. Tente novamente.",
        )

    session = resp.session
    if session is None:
        # Email ainda não confirmado
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="E-mail não verificado. Confirme seu e-mail antes de fazer login.",
        )

    return TokenResponse(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        expires_in=session.expires_in or 3600,
    )


def refresh_token(refresh_token: str) -> TokenResponse:
    client = get_auth_client()
    try:
        resp = client.auth.refresh_session(refresh_token)
    except AuthApiError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado.",
        )

    session = resp.session
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Sessão inválida.")

    return TokenResponse(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        expires_in=session.expires_in or 3600,
    )


def verify_email(token_hash: str, type_: str) -> dict:
    client = get_auth_client()
    try:
        client.auth.verify_otp({"token_hash": token_hash, "type": type_})
    except AuthApiError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Link de verificação inválido ou expirado.",
        )
    return {"message": "E-mail verificado com sucesso! Você já pode fazer login."}


def resend_verification(email: str) -> dict:
    client = get_auth_client()
    try:
        client.auth.resend({"type": "signup", "email": email})
    except AuthApiError:
        pass  # silencioso: não revela se e-mail existe
    return {"message": "Se o e-mail estiver cadastrado, você receberá um novo link de verificação."}
