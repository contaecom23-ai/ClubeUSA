import re
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if len(v) > 128:
            raise ValueError("Password must be at most 128 characters")
        return v

    @field_validator("full_name")
    @classmethod
    def name_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Full name must be at least 2 characters")
        if len(v) > 100:
            raise ValueError("Full name must be at most 100 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None

    @field_validator("zip_code")
    @classmethod
    def valid_zip(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if v and not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError("Invalid US ZIP code (expected 12345 or 12345-6789)")
        return v or None

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        digits = re.sub(r"[^\d]", "", v)
        if digits and (len(digits) < 7 or len(digits) > 15):
            raise ValueError("Phone number must have 7–15 digits")
        return v.strip() or None

    @field_validator("full_name", "state", "city")
    @classmethod
    def strip_and_limit(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        return v or None


class ProfileResponse(BaseModel):
    user_id: str
    email: str
    full_name: Optional[str]
    phone: Optional[str]
    state: Optional[str]
    city: Optional[str]
    zip_code: Optional[str]
    is_email_verified: bool
    created_at: str
