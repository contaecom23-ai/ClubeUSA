from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    us_state: Optional[str] = None
    city: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("full_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Full name cannot be empty")
        return stripped

    @field_validator("us_state", "city")
    @classmethod
    def max_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 100:
            raise ValueError("Field exceeds maximum length of 100 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ConfirmRequest(BaseModel):
    token_hash: str
    type: str = "email"


class ProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    us_state: Optional[str]
    city: Optional[str]
    email_confirmed: bool


class LoginResponse(BaseModel):
    message: str
    email_confirmed: bool


class MessageResponse(BaseModel):
    message: str
