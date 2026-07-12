from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, field_validator

VALID_LISTING_TYPES = frozenset({
    "quarto_disponivel",
    "precisa_quarto",
    "casa_disponivel",
})

LISTING_TYPE_LABELS = {
    "quarto_disponivel": "Quarto disponível",
    "precisa_quarto": "Procura quarto / roommate",
    "casa_disponivel": "Casa / Apartamento para alugar",
}

VALID_STATES = frozenset({
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC",
})


class HousingCreate(BaseModel):
    title: str
    description: str
    listing_type: str
    zip_code: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    rent_monthly_cents: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    furnished: bool = False
    utilities_included: bool = False
    pets_allowed: Optional[bool] = None
    available_from: Optional[datetime] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    image_url: Optional[str] = None
    expires_at: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def title_valid(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Título não pode ser vazio")
        if len(v) > 120:
            raise ValueError("Título máximo 120 caracteres")
        return v

    @field_validator("description")
    @classmethod
    def description_valid(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Descrição não pode ser vazia")
        if len(v) > 2000:
            raise ValueError("Descrição máximo 2000 caracteres")
        return v

    @field_validator("listing_type")
    @classmethod
    def listing_type_valid(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in VALID_LISTING_TYPES:
            raise ValueError(
                f"Tipo inválido. Use: {', '.join(sorted(VALID_LISTING_TYPES))}"
            )
        return v

    @field_validator("zip_code")
    @classmethod
    def zip_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().replace("-", "")
        if not v.isdigit() or len(v) != 5:
            raise ValueError("ZIP deve ter 5 dígitos (formato americano, ex: 33101)")
        return v

    @field_validator("state")
    @classmethod
    def state_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().upper()
        if v not in VALID_STATES:
            raise ValueError("Estado inválido — use sigla de 2 letras (ex: FL, NY, CA)")
        return v

    @field_validator("city")
    @classmethod
    def city_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if len(v) > 80:
            raise ValueError("Cidade máximo 80 caracteres")
        return v or None

    @field_validator("rent_monthly_cents")
    @classmethod
    def rent_valid(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        if v < 0:
            raise ValueError("Aluguel não pode ser negativo")
        if v > 1_000_000_00:
            raise ValueError("Aluguel não pode ultrapassar $1.000.000")
        return v

    @field_validator("bedrooms")
    @classmethod
    def bedrooms_valid(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        if v < 0 or v > 20:
            raise ValueError("Número de quartos deve ser entre 0 e 20")
        return v

    @field_validator("bathrooms")
    @classmethod
    def bathrooms_valid(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return v
        if v < 0 or v > 20:
            raise ValueError("Número de banheiros deve ser entre 0 e 20")
        return v

    @field_validator("contact_phone")
    @classmethod
    def phone_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) < 10 or len(digits) > 15:
            raise ValueError("Telefone deve ter entre 10 e 15 dígitos")
        return v.strip()

    @field_validator("image_url")
    @classmethod
    def url_must_be_http(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL deve começar com http:// ou https://")
        return v


class HousingResponse(BaseModel):
    id: str
    title: str
    description: str
    listing_type: str
    zip_code: Optional[str]
    city: Optional[str]
    state: Optional[str]
    rent_monthly_cents: Optional[int]
    bedrooms: Optional[int]
    bathrooms: Optional[float]
    furnished: bool
    utilities_included: bool
    pets_allowed: Optional[bool]
    available_from: Optional[datetime]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    image_url: Optional[str]
    expires_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class HousingWithDistanceResponse(HousingResponse):
    distance_miles: Optional[float] = None


class HousingListResponse(BaseModel):
    items: List[HousingResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class HousingSearchResponse(BaseModel):
    items: List[HousingWithDistanceResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
    search_zip: str
    radius_miles: float
