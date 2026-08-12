import re
from typing import Optional

from pydantic import BaseModel, field_validator


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    zip_code: Optional[str] = None
    state: Optional[str] = None

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if len(v) < 2 or len(v) > 120:
            raise ValueError("Nome deve ter entre 2 e 120 caracteres.")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not re.match(r"^\+?[0-9\s\-\(\)]{7,20}$", v):
            raise ValueError("Telefone inválido.")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip_code(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not re.match(r"^[0-9]{5}(-[0-9]{4})?$", v):
            raise ValueError("ZIP code inválido (ex: 90210 ou 90210-1234).")
        return v

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.upper().strip()
        valid_states = {
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
            "DC",
        }
        if v not in valid_states:
            raise ValueError("Estado inválido. Use a sigla de 2 letras (ex: FL, NY).")
        return v


class ProfileResponse(BaseModel):
    id: str
    full_name: str
    phone: Optional[str] = None
    zip_code: Optional[str] = None
    state: Optional[str] = None
    created_at: str
    updated_at: str
