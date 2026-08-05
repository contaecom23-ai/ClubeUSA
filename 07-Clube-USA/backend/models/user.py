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
            raise ValueError("Senha deve ter ao menos 8 caracteres.")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Senha deve conter ao menos uma letra.")
        if not re.search(r"\d", v):
            raise ValueError("Senha deve conter ao menos um número.")
        return v

    @field_validator("full_name")
    @classmethod
    def name_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nome deve ter ao menos 2 caracteres.")
        if len(v) > 100:
            raise ValueError("Nome deve ter no máximo 100 caracteres.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserProfile(BaseModel):
    user_id: str
    email: str
    full_name: str
    email_confirmed: bool


class UpdateProfileRequest(BaseModel):
    full_name: str

    @field_validator("full_name")
    @classmethod
    def name_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nome deve ter ao menos 2 caracteres.")
        if len(v) > 100:
            raise ValueError("Nome deve ter no máximo 100 caracteres.")
        return v
