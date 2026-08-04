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
            raise ValueError("A senha deve ter no mínimo 8 caracteres")
        return v

    @field_validator("full_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nome é obrigatório")
        return v

    @field_validator("zip_code")
    @classmethod
    def valid_zip(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if v and not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError("ZIP inválido — formato esperado: 10001 ou 10001-1234")
        return v or None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UpdateProfileRequest(BaseModel):
    full_name: str | None = None
    zip_code: str | None = None

    @field_validator("full_name")
    @classmethod
    def name_not_empty(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            raise ValueError("Nome não pode ser vazio")
        return v

    @field_validator("zip_code")
    @classmethod
    def valid_zip(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if v and not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError("ZIP inválido")
        return v or None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    zip_code: str | None
    referral_code: str
    email_confirmed: bool
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
