import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

# Estados dos EUA (validação server-side)
_US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN",
    "IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV",
    "NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN",
    "TX","UT","VT","VA","WA","WV","WI","WY","DC",
}

_ZIP_RE = re.compile(r"^\d{5}(-\d{4})?$")


class ProfileResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    zip_code: Optional[str]
    us_state: Optional[str]
    bio: Optional[str]
    email_confirmed: bool
    created_at: datetime
    last_login_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    zip_code: Optional[str] = None
    us_state: Optional[str] = None
    bio: Optional[str] = None

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if len(v) > 255:
            raise ValueError("Nome muito longo (máx. 255 caracteres).")
        return v or None

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not _ZIP_RE.match(v):
            raise ValueError("ZIP Code inválido. Use formato 12345 ou 12345-6789.")
        return v

    @field_validator("us_state")
    @classmethod
    def validate_state(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().upper()
        if v not in _US_STATES:
            raise ValueError("Estado americano inválido.")
        return v

    @field_validator("bio")
    @classmethod
    def clean_bio(cls, v: str | None) -> str | None:
        if v is None:
            return None
        # Remove tags HTML básicas (anti-XSS básico; para produção usar bleach)
        v = re.sub(r"<[^>]+>", "", v).strip()
        if len(v) > 500:
            raise ValueError("Bio muito longa (máx. 500 caracteres).")
        return v or None
