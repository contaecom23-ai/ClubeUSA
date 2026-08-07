import re
from pydantic import BaseModel, EmailStr, field_validator


# ------------------------------------------------------------------ Auth
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter pelo menos 8 caracteres")
        if not re.search(r"[0-9!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", v):
            raise ValueError("Senha deve conter ao menos um número ou caractere especial")
        return v

    @field_validator("full_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nome não pode ser vazio")
        if len(v) > 120:
            raise ValueError("Nome muito longo (máx 120 chars)")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ------------------------------------------------------------------ Profile
class ProfileUpdate(BaseModel):
    full_name: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    phone: str | None = None
    bio: str | None = None
    avatar_url: str | None = None

    @field_validator("bio")
    @classmethod
    def bio_max_length(cls, v: str | None) -> str | None:
        if v and len(v) > 500:
            raise ValueError("Bio deve ter no máximo 500 caracteres")
        return v

    @field_validator("zip_code")
    @classmethod
    def zip_format(cls, v: str | None) -> str | None:
        if v and not re.fullmatch(r"\d{5}(-\d{4})?", v):
            raise ValueError("ZIP code inválido (use 12345 ou 12345-6789)")
        return v

    @field_validator("avatar_url")
    @classmethod
    def avatar_https(cls, v: str | None) -> str | None:
        if v and not v.startswith("https://"):
            raise ValueError("avatar_url deve ser HTTPS")
        return v


class ProfileResponse(BaseModel):
    user_id: str
    email: str
    full_name: str | None
    city: str | None
    state: str | None
    zip_code: str | None
    phone: str | None
    bio: str | None
    avatar_url: str | None
    is_email_confirmed: bool
