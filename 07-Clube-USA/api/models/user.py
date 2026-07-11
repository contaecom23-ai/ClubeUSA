"""Pydantic request/response models for user data."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Request bodies ─────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=100)

    @field_validator("full_name")
    @classmethod
    def name_no_script(cls, v: str) -> str:
        # Basic XSS guard on user-supplied name
        forbidden = ["<", ">", "&", '"', "'", "/"]
        for ch in forbidden:
            if ch in v:
                raise ValueError("full_name contains invalid characters")
        return v.strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., min_length=36, max_length=36)  # UUID format


class ResendConfirmationRequest(BaseModel):
    email: EmailStr


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)

    @field_validator("full_name")
    @classmethod
    def name_no_script(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        forbidden = ["<", ">", "&", '"', "'", "/"]
        for ch in forbidden:
            if ch in v:
                raise ValueError("full_name contains invalid characters")
        return v.strip()


# ── Response bodies ────────────────────────────────────────────────────────────

class UserPublic(BaseModel):
    """Safe subset of user data returned to clients. Never exposes password_hash."""
    id: str
    email: str
    full_name: str
    email_confirmed: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_days: int


class MessageResponse(BaseModel):
    message: str
