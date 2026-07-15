import logging
import secrets
from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, Request, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from supabase import Client

from ..config import Settings
from .email_service import EmailService

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_INVALID_CREDS = {"status_code": status.HTTP_401_UNAUTHORIZED, "detail": "Email ou senha inválidos"}


class AuthService:
    def __init__(self, supabase: Client, settings: Settings):
        self.db = supabase
        self.settings = settings
        self.email_svc = EmailService(settings)

    # ── Passwords ─────────────────────────────────────────────────────────────

    def _hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def _verify_password(self, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    # ── JWT ───────────────────────────────────────────────────────────────────

    def _create_token(self, user_id: str, email: str) -> str:
        now = datetime.now(tz=timezone.utc)
        payload = {
            "sub": user_id,
            "email": email,
            "iat": now,
            "exp": now + timedelta(days=self.settings.access_token_expire_days),
        }
        return jwt.encode(payload, self.settings.secret_key, algorithm=self.settings.algorithm)

    def _decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(
                token,
                self.settings.secret_key,
                algorithms=[self.settings.algorithm],
            )
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou expirado",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

    def get_current_user_id(self, request: Request) -> str:
        """Extrai user_id do JWT. user_id vem sempre do servidor, nunca do body."""
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header ausente ou inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = auth_header.removeprefix("Bearer ").strip()
        payload = self._decode_token(token)
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token sem identificador de usuário",
            )
        return user_id

    # ── Register ──────────────────────────────────────────────────────────────

    async def register(self, data) -> dict:
        # Verificar duplicata — retornar 409 com mensagem genérica (não vazar existência via timing)
        existing = (
            self.db.table("users")
            .select("id")
            .eq("email", data.email.lower())
            .execute()
        )
        if existing.data:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email já cadastrado")

        # Resolver referral (inválido → ignora, não bloqueia cadastro)
        referred_by_id: str | None = None
        if data.referral_code:
            ref = (
                self.db.table("users")
                .select("id")
                .eq("referral_code", data.referral_code.strip().upper())
                .execute()
            )
            if ref.data:
                referred_by_id = ref.data[0]["id"]

        confirmation_token = secrets.token_urlsafe(32)
        referral_code = secrets.token_urlsafe(6).upper()
        expires_at = (datetime.now(tz=timezone.utc) + timedelta(hours=24)).isoformat()

        result = (
            self.db.table("users")
            .insert(
                {
                    "email": data.email.lower(),
                    "password_hash": self._hash_password(data.password),
                    "full_name": data.full_name,
                    "zip_code": data.zip_code,
                    "phone": data.phone,
                    "email_confirmed": False,
                    "email_confirmation_token": confirmation_token,
                    "email_confirmation_expires_at": expires_at,
                    "referral_code": referral_code,
                    "referred_by_id": referred_by_id,
                }
            )
            .execute()
        )

        if not result.data:
            logger.error("Falha ao inserir usuário: %s", result)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao criar conta. Tente novamente.",
            )

        user = result.data[0]
        confirm_url = f"{self.settings.app_base_url}/auth/confirm-email?token={confirmation_token}"

        await self.email_svc.send_confirmation_email(
            to=user["email"],
            full_name=user["full_name"],
            confirm_url=confirm_url,
        )

        return {
            "message": "Conta criada! Verifique seu email para confirmar o cadastro.",
            "user_id": user["id"],
            "email": user["email"],
        }

    # ── Login ─────────────────────────────────────────────────────────────────

    async def login(self, email: str, password: str) -> dict:
        result = (
            self.db.table("users")
            .select("id, email, password_hash, full_name, email_confirmed")
            .eq("email", email.lower())
            .execute()
        )

        # Mesma mensagem de erro para usuário inexistente e senha errada — evita user enumeration
        if not result.data or not self._verify_password(password, result.data[0]["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha inválidos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = result.data[0]
        token = self._create_token(user_id=user["id"], email=user["email"])

        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "email_confirmed": user["email_confirmed"],
        }

    # ── Confirm Email ─────────────────────────────────────────────────────────

    async def confirm_email(self, token: str) -> dict:
        result = (
            self.db.table("users")
            .select("id, email, email_confirmed, email_confirmation_expires_at")
            .eq("email_confirmation_token", token)
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de confirmação inválido",
            )

        user = result.data[0]

        if user["email_confirmed"]:
            return {"message": "Email já confirmado anteriormente"}

        expires_str = user.get("email_confirmation_expires_at")
        if expires_str:
            expires_at = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
            if datetime.now(tz=timezone.utc) > expires_at:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token de confirmação expirado. Solicite um novo email.",
                )

        # Confirma e invalida o token (previne reutilização)
        self.db.table("users").update(
            {
                "email_confirmed": True,
                "email_confirmation_token": None,
                "email_confirmation_expires_at": None,
            }
        ).eq("id", user["id"]).execute()

        return {"message": "Email confirmado com sucesso! Agora você pode fazer login."}

    # ── Get Profile ───────────────────────────────────────────────────────────

    async def get_profile(self, user_id: str) -> dict:
        """user_id vem sempre do token JWT (servidor), nunca do cliente."""
        result = (
            self.db.table("users")
            .select("id, email, full_name, zip_code, phone, email_confirmed, referral_code, created_at")
            .eq("id", user_id)
            .execute()
        )

        if not result.data:
            # 404 para IDs de outros usuários — não vaza existência
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

        return result.data[0]
