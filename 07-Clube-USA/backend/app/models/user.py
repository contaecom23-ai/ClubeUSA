from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
import re


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    zip_code: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("A senha deve ter pelo menos 8 caracteres.")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("A senha deve conter pelo menos uma letra.")
        if not re.search(r"\d", v):
            raise ValueError("A senha deve conter pelo menos um número.")
        return v

    @field_validator("zip_code")
    @classmethod
    def zip_code_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # ZIP simples (5 dígitos) ou ZIP+4 (9 dígitos)
        if not re.match(r"^\d{5}(-\d{4})?$", v.strip()):
            raise ValueError("ZIP code inválido. Use o formato 12345 ou 12345-6789.")
        return v.strip()

    @field_validator("full_name")
    @classmethod
    def full_name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nome completo muito curto.")
        if len(v) > 100:
            raise ValueError("Nome completo muito longo.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos até expirar o access token


class RefreshRequest(BaseModel):
    refresh_token: str


class ConfirmEmailRequest(BaseModel):
    token: str


class ProfileResponse(BaseModel):
    id: str
    email: str
    email_confirmed: bool
    full_name: Optional[str]
    zip_code: Optional[str]
    phone: Optional[str]
    created_at: datetime
    last_login_at: Optional[datetime]


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None

    @field_validator("full_name")
    @classmethod
    def full_name_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nome completo muito curto.")
        if len(v) > 100:
            raise ValueError("Nome completo muito longo.")
        return v

    @field_validator("zip_code")
    @classmethod
    def zip_code_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not re.match(r"^\d{5}(-\d{4})?$", v.strip()):
            raise ValueError("ZIP code inválido.")
        return v.strip()

    @field_validator("phone")
    @classmethod
    def phone_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Aceita formatos comuns nos EUA: +1 (555) 555-5555, 5555555555, etc.
        cleaned = re.sub(r"[\s\-\(\)\+]", "", v)
        if not re.match(r"^1?\d{10}$", cleaned):
            raise ValueError("Telefone inválido. Use um número de telefone dos EUA.")
        return v.strip()


class MessageResponse(BaseModel):
    message: str
