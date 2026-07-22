from typing import Optional
from pydantic import BaseModel, field_validator


class ProfileUpdate(BaseModel):
    zip_code: Optional[str] = None
    city: Optional[str] = None
    state_code: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None

    @field_validator("state_code")
    @classmethod
    def validate_state_code(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip().upper()
            if len(v) != 2:
                raise ValueError("state_code deve ter 2 letras (ex: FL, NY, TX)")
        return v

    @field_validator("bio")
    @classmethod
    def validate_bio(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 500:
            raise ValueError("Bio deve ter no máximo 500 caracteres")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if v and not v.replace("-", "").isdigit():
                raise ValueError("ZIP code inválido")
        return v


class ProfileResponse(BaseModel):
    zip_code: Optional[str] = None
    city: Optional[str] = None
    state_code: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class MeResponse(BaseModel):
    id: str
    email: str
    full_name: str
    email_confirmed: bool
    profile: Optional[ProfileResponse] = None
