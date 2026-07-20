import re
from typing import Optional
from pydantic import BaseModel, field_validator

US_STATES = frozenset(
    "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD "
    "MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC "
    "SD TN TX UT VT VA WA WV WI WY DC".split()
)


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None

    @field_validator("full_name")
    @classmethod
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if len(v) < 2:
                raise ValueError("Nome deve ter ao menos 2 caracteres")
        return v

    @field_validator("state")
    @classmethod
    def valid_state(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip().upper()
            if v not in US_STATES:
                raise ValueError("Código de estado americano inválido (ex: FL, TX, CA)")
        return v

    @field_validator("city")
    @classmethod
    def city_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if len(v) < 2:
                raise ValueError("Cidade deve ter ao menos 2 caracteres")
        return v

    @field_validator("zip_code")
    @classmethod
    def valid_zip(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.fullmatch(r"\d{5}(-\d{4})?", v.strip()):
            raise ValueError("ZIP code deve estar no formato 12345 ou 12345-6789")
        return v.strip() if v else v


class ProfileResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
