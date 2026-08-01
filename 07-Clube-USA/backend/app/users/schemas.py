from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator
from ..auth.schemas import US_STATES
import re


class UserProfile(BaseModel):
    id: str
    email: EmailStr
    name: str
    estado: str | None
    cidade: str | None
    whatsapp: str | None
    email_confirmed: bool
    created_at: datetime
    last_login_at: datetime | None


class UpdateProfileRequest(BaseModel):
    name: str | None = None
    estado: str | None = None
    cidade: str | None = None
    whatsapp: str | None = None

    @field_validator("name")
    @classmethod
    def name_valid(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("nome não pode ser vazio")
        if len(v) > 100:
            raise ValueError("nome muito longo")
        return v

    @field_validator("estado")
    @classmethod
    def valid_state(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.upper().strip()
        if v not in US_STATES:
            raise ValueError(f"estado inválido: {v}")
        return v

    @field_validator("whatsapp")
    @classmethod
    def clean_whatsapp(cls, v: str | None) -> str | None:
        if v is None:
            return v
        digits = re.sub(r"\D", "", v)
        if digits and len(digits) < 8:
            raise ValueError("número de WhatsApp inválido")
        return digits or None
