import re
from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    zip_code: str | None = None

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter pelo menos 8 caracteres")
        return v

    @field_validator("full_name")
    @classmethod
    def full_name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nome não pode ser vazio")
        return v

    @field_validator("zip_code")
    @classmethod
    def zip_code_format(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if v and not re.match(r"^\d{5}(-\d{4})?$", v):
                raise ValueError("ZIP code inválido (formato: 12345 ou 12345-6789)")
        return v or None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str
    zip_code: str | None
    email_confirmed: bool
    created_at: str


class UpdateProfileRequest(BaseModel):
    full_name: str | None = None
    zip_code: str | None = None

    @field_validator("full_name")
    @classmethod
    def full_name_not_blank(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Nome não pode ser vazio")
        return v

    @field_validator("zip_code")
    @classmethod
    def zip_code_format(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if v and not re.match(r"^\d{5}(-\d{4})?$", v):
                raise ValueError("ZIP code inválido (formato: 12345 ou 12345-6789)")
        return v or None


class ResendConfirmationRequest(BaseModel):
    email: EmailStr
