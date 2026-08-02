import re

from pydantic import BaseModel, field_validator


class ProfileResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    zip_code: str
    phone: str | None
    created_at: str
    updated_at: str


class UpdateProfileRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    zip_code: str | None = None
    phone: str | None = None

    @field_validator("zip_code")
    @classmethod
    def zip_code_format(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError("ZIP code inválido (use 12345 ou 12345-6789)")
        return v

    @field_validator("first_name", "last_name")
    @classmethod
    def name_not_empty(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Campo não pode ser vazio")
        if len(v) > 100:
            raise ValueError("Máximo de 100 caracteres")
        return v

    @field_validator("phone")
    @classmethod
    def phone_format(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        if not re.match(r"^\+?[\d\s\-().]{7,20}$", v):
            raise ValueError("Telefone inválido")
        return v
