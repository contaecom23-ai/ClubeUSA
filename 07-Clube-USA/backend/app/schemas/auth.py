import re

from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    zip_code: str
    phone: str | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter pelo menos 8 caracteres")
        return v

    @field_validator("zip_code")
    @classmethod
    def zip_code_format(cls, v: str) -> str:
        if not re.match(r"^\d{5}(-\d{4})?$", v.strip()):
            raise ValueError("ZIP code inválido (use 12345 ou 12345-6789)")
        return v.strip()

    @field_validator("first_name", "last_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Campo obrigatório")
        if len(v) > 100:
            raise ValueError("Máximo de 100 caracteres")
        return v

    @field_validator("phone")
    @classmethod
    def phone_format(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        if not re.match(r"^\+?[\d\s\-().]{7,20}$", v):
            raise ValueError("Telefone inválido")
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
