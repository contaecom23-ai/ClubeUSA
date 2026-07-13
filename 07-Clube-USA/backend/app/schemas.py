from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    zip_code: str | None = Field(default=None, max_length=10)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=2)
    referral_code: str | None = Field(default=None, max_length=20)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if v.isdigit():
            raise ValueError("Senha não pode ser só números.")
        if len(set(v)) < 4:
            raise ValueError("Senha muito fraca.")
        return v

    @field_validator("state")
    @classmethod
    def state_upper(cls, v: str | None) -> str | None:
        return v.upper() if v else v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos


class RefreshRequest(BaseModel):
    refresh_token: str


class MessageResponse(BaseModel):
    message: str


# ── Users ─────────────────────────────────────────────────────────────────────

class UserProfile(BaseModel):
    id: UUID
    email: str
    full_name: str
    phone: str | None
    zip_code: str | None
    city: str | None
    state: str | None
    country: str
    email_confirmed: bool
    referral_code: str
    created_at: datetime
    last_login_at: datetime | None


class UpdateProfileRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    zip_code: str | None = Field(default=None, max_length=10)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=2)

    @field_validator("state")
    @classmethod
    def state_upper(cls, v: str | None) -> str | None:
        return v.upper() if v else v
