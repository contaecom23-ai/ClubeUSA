import re
from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str = ""
    zip_code: str = ""
    phone: str = ""
    referred_by_slug: str = ""

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha precisa de no mínimo 8 caracteres")
        return v

    @field_validator("first_name")
    @classmethod
    def first_name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nome é obrigatório")
        return v

    @field_validator("zip_code")
    @classmethod
    def zip_code_format(cls, v: str) -> str:
        v = v.strip()
        if v and not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError("CEP americano inválido (formato: 12345 ou 12345-6789)")
        return v

    @field_validator("referred_by_slug")
    @classmethod
    def referred_by_slug_format(cls, v: str) -> str:
        v = v.strip()
        if v and not re.match(r"^[a-zA-Z0-9_-]{3,24}$", v):
            raise ValueError("Código de referral inválido")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class MessageResponse(BaseModel):
    message: str
