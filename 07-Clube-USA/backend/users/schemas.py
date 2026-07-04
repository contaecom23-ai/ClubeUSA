import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class ProfileResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    phone: str
    zip_code: str
    state: str
    created_at: datetime
    updated_at: datetime


class ProfileUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    zip_code: Optional[str] = None
    state: Optional[str] = None

    @field_validator("first_name")
    @classmethod
    def first_name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Nome não pode ser vazio")
        return v

    @field_validator("zip_code")
    @classmethod
    def zip_code_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if v and not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError("CEP americano inválido (formato: 12345 ou 12345-6789)")
        return v
