from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
import re


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str

    @field_validator("full_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nome deve ter ao menos 2 caracteres")
        if len(v) > 100:
            raise ValueError("Nome muito longo (máx 100 caracteres)")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter ao menos 8 caracteres")
        if len(v) > 128:
            raise ValueError("Senha muito longa")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    email_confirmed: bool


class MessageResponse(BaseModel):
    message: str


# ── Profile ───────────────────────────────────────────────────────────────────

class ProfileUpdate(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    bio: Optional[str] = None

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError("ZIP code inválido (ex: 10001 ou 10001-1234)")
        return v

    @field_validator("bio")
    @classmethod
    def bio_length(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 500:
            raise ValueError("Bio muito longa (máx 500 caracteres)")
        return v


class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str
    email_confirmed: bool
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime
