import re
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    zip_code: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("A senha deve ter pelo menos 8 caracteres")
        return v

    @field_validator("first_name", "last_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Campo obrigatório")
        return v.strip()[:100]

    @field_validator("zip_code")
    @classmethod
    def valid_zip(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError("CEP/ZIP inválido (use 12345 ou 12345-6789)")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    zip_code: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Campo não pode ser vazio")
        return v.strip()[:100] if v else v

    @field_validator("zip_code")
    @classmethod
    def valid_zip(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError("CEP/ZIP inválido")
        return v


class UserProfile(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    zip_code: Optional[str]
    email_confirmed: bool
    created_at: str
