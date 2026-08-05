import re
from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    zip_code: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("A senha deve ter pelo menos 8 caracteres")
        return v

    @field_validator("zip_code")
    @classmethod
    def zip_format(cls, v: str) -> str:
        if not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError("ZIP code inválido (formato: 12345 ou 12345-6789)")
        return v

    @field_validator("full_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nome completo é obrigatório")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ConfirmEmailRequest(BaseModel):
    token: str


class ResendConfirmationRequest(BaseModel):
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email_confirmed: bool


class MessageResponse(BaseModel):
    message: str
