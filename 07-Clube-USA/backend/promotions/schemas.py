from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, field_validator

VALID_CATEGORIES = frozenset({
    "alimentacao", "compras", "saude", "beleza",
    "automoveis", "servicos", "entretenimento", "educacao", "outros",
})

CATEGORY_LABELS = {
    "alimentacao": "Alimentação",
    "compras": "Compras",
    "saude": "Saúde",
    "beleza": "Beleza",
    "automoveis": "Automóveis",
    "servicos": "Serviços",
    "entretenimento": "Entretenimento",
    "educacao": "Educação",
    "outros": "Outros",
}


class PromotionCreate(BaseModel):
    title: str
    description: str
    store: str
    category: str
    zip_code: Optional[str] = None
    expires_at: Optional[datetime] = None
    discount_url: Optional[str] = None
    discount_code: Optional[str] = None
    image_url: Optional[str] = None

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
        if len(v) > 1000:
            raise ValueError("Descrição máximo 1000 caracteres")
        return v

    @field_validator("store")
    @classmethod
    def store_valid(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Loja não pode ser vazia")
        if len(v) > 100:
            raise ValueError("Nome da loja máximo 100 caracteres")
        return v

    @field_validator("category")
    @classmethod
    def category_valid(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in VALID_CATEGORIES:
            raise ValueError(
                f"Categoria inválida. Use: {', '.join(sorted(VALID_CATEGORIES))}"
            )
        return v

    @field_validator("zip_code")
    @classmethod
    def zip_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().replace("-", "")
        if not v.isdigit() or len(v) != 5:
            raise ValueError("ZIP deve ter 5 dígitos (formato americano, ex: 90210)")
        return v

    @field_validator("discount_url", "image_url")
    @classmethod
    def url_must_be_http(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL deve começar com http:// ou https://")
        return v

    @field_validator("discount_code")
    @classmethod
    def code_length(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if len(v) > 50:
            raise ValueError("Código de desconto máximo 50 caracteres")
        return v or None


class PromotionResponse(BaseModel):
    id: str
    title: str
    description: str
    store: str
    category: str
    zip_code: Optional[str]
    expires_at: Optional[datetime]
    discount_url: Optional[str]
    discount_code: Optional[str]
    image_url: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class PromotionWithDistanceResponse(PromotionResponse):
    """PromotionResponse com distância em milhas (presente em buscas por ZIP)."""
    distance_miles: Optional[float] = None


class PromotionListResponse(BaseModel):
    items: List[PromotionResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class PromotionSearchResponse(BaseModel):
    """Resultado de busca geográfica — inclui distância e indica cobertura."""
    items: List[PromotionWithDistanceResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
    search_zip: str
    radius_miles: float
