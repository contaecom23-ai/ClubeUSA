from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter pelo menos 8 caracteres")
        if not any(c.isdigit() for c in v):
            raise ValueError("Senha deve conter pelo menos um número")
        if not any(c.isalpha() for c in v):
            raise ValueError("Senha deve conter pelo menos uma letra")
        return v

    @field_validator("full_name")
    @classmethod
    def full_name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nome completo deve ter pelo menos 2 caracteres")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ProfileResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    phone: str | None
    state_us: str | None
    city: str | None
    zip_code: str | None
    is_email_confirmed: bool
    created_at: datetime


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    state_us: str | None = None
    city: str | None = None
    zip_code: str | None = None

    @field_validator("full_name")
    @classmethod
    def full_name_not_empty(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if len(v) < 2:
                raise ValueError("Nome completo deve ter pelo menos 2 caracteres")
        return v

    @field_validator("zip_code")
    @classmethod
    def zip_code_format(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip().replace("-", "")
            if not v.isdigit() or len(v) != 5:
                raise ValueError("ZIP Code deve ter 5 dígitos numéricos (ex: 33101)")
        return v

    @field_validator("state_us")
    @classmethod
    def state_us_format(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip().upper()
            if len(v) != 2 or not v.isalpha():
                raise ValueError("Estado deve ser a sigla de 2 letras (ex: FL, TX, NY)")
        return v

    @field_validator("phone")
    @classmethod
    def phone_format(cls, v: str | None) -> str | None:
        if v is not None:
            digits = "".join(c for c in v if c.isdigit())
            if len(digits) < 10 or len(digits) > 15:
                raise ValueError("Telefone deve ter entre 10 e 15 dígitos")
        return v
