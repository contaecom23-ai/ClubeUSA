import re
from typing import Optional

from pydantic import BaseModel, field_validator


class ProfileResponse(BaseModel):
    user_id: str
    email: str
    email_confirmed: bool
    full_name: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None

    @field_validator("zip_code")
    @classmethod
    def zip_format(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError("ZIP code inválido")
        return v

    @field_validator("bio")
    @classmethod
    def bio_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 500:
            raise ValueError("Bio deve ter no máximo 500 caracteres")
        return v
