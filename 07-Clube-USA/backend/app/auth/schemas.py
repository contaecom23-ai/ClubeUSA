import re

from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    zip_code: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter ao menos 8 caracteres")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Senha deve conter ao menos uma letra")
        if not re.search(r"\d", v):
            raise ValueError("Senha deve conter ao menos um número")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nome muito curto")
        if len(v) > 100:
            raise ValueError("Nome muito longo")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not re.match(r"^\d{5}(-\d{4})?$", v):
                raise ValueError("ZIP code inválido (ex: 10001 ou 10001-1234)")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ResendConfirmationRequest(BaseModel):
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str
    zip_code: str | None
    email_confirmed: bool
    created_at: str


class MessageResponse(BaseModel):
    message: str
