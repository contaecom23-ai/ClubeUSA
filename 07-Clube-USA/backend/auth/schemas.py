import re
from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Mínimo de 8 caracteres")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Deve conter ao menos uma letra maiúscula")
        if not re.search(r"[0-9]", v):
            raise ValueError("Deve conter ao menos um número")
        return v

    @field_validator("full_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nome deve ter ao menos 2 caracteres")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ResendConfirmationRequest(BaseModel):
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


class UserResponse(BaseModel):
    id: str
    email: str
    email_confirmed: bool
    full_name: str | None = None
