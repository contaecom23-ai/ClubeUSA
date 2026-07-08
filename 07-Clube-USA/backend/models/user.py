import re
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator

_US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID",
    "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS",
    "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK",
    "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV",
    "WI", "WY", "DC",
}


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    zip_code: str

    @field_validator("full_name")
    @classmethod
    def name_valid(cls, v: str) -> str:
        v = v.strip()
        if not 2 <= len(v) <= 100:
            raise ValueError("Nome deve ter entre 2 e 100 caracteres")
        return v

    @field_validator("password")
    @classmethod
    def password_strong(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter pelo menos 8 caracteres")
        return v

    @field_validator("zip_code")
    @classmethod
    def zip_valid(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError("ZIP inválido. Use formato 12345 ou 12345-6789")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    zip_code: Optional[str] = None
    state_us: Optional[str] = None
    city: Optional[str] = None
    whatsapp: Optional[str] = None

    @field_validator("full_name")
    @classmethod
    def name_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not 2 <= len(v) <= 100:
                raise ValueError("Nome deve ter entre 2 e 100 caracteres")
        return v

    @field_validator("zip_code")
    @classmethod
    def zip_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not re.match(r"^\d{5}(-\d{4})?$", v):
                raise ValueError("ZIP inválido. Use formato 12345 ou 12345-6789")
        return v

    @field_validator("state_us")
    @classmethod
    def state_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.upper()
            if v not in _US_STATES:
                raise ValueError("Estado inválido")
        return v

    @field_validator("whatsapp")
    @classmethod
    def whatsapp_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = re.sub(r"[\s\-\(\)\+]", "", v)
            if not re.match(r"^\d{10,15}$", cleaned):
                raise ValueError("WhatsApp inválido")
        return v


class UserResponse(BaseModel):
    id: str
    email: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserResponse


class ProfileResponse(BaseModel):
    id: str
    full_name: str
    email: str
    zip_code: Optional[str] = None
    state_us: Optional[str] = None
    city: Optional[str] = None
    whatsapp: Optional[str] = None
    email_confirmed: bool
    created_at: str
