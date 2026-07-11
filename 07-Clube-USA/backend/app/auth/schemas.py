import re
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


_PASSWORD_MIN_LEN = 8


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=_PASSWORD_MIN_LEN, max_length=128)
    zip_code: Optional[str] = Field(None, pattern=r"^\d{5}(-\d{4})?$")
    state_abbr: Optional[str] = Field(None, min_length=2, max_length=2)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        return v

    @field_validator("state_abbr")
    @classmethod
    def uppercase_state(cls, v: Optional[str]) -> Optional[str]:
        return v.upper() if v else v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., min_length=32, max_length=256)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class MessageResponse(BaseModel):
    message: str
