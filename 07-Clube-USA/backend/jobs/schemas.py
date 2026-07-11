from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, field_validator

VALID_CATEGORIES = frozenset({
    "construcao",
    "limpeza",
    "restaurante",
    "motorista",
    "cuidado",
    "beleza",
    "vendas",
    "escritorio",
    "tecnologia",
    "saude",
    "outros",
})

CATEGORY_LABELS = {
    "construcao": "Construção / Obras",
    "limpeza": "Limpeza / Zeladoria",
    "restaurante": "Restaurante / Alimentação",
    "motorista": "Motorista / Entrega",
    "cuidado": "Cuidado / Babá / Idosos",
    "beleza": "Beleza / Salão",
    "vendas": "Vendas / Varejo",
    "escritorio": "Escritório / Administrativo",
    "tecnologia": "Tecnologia / TI",
    "saude": "Saúde",
    "outros": "Outros",
}

VALID_JOB_TYPES = frozenset({"full_time", "part_time", "contract", "gig"})

JOB_TYPE_LABELS = {
    "full_time": "Tempo integral",
    "part_time": "Meio período",
    "contract": "Contrato / Freelance",
    "gig": "Bico / Temporário",
}


class JobCreate(BaseModel):
    title: str
    company: str
    description: str
    category: str
    job_type: str
    zip_code: Optional[str] = None
    salary_range: Optional[str] = None
    apply_url: Optional[str] = None
    contact_email: Optional[EmailStr] = None
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

    @field_validator("company")
    @classmethod
    def company_valid(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Empresa não pode ser vazia")
        if len(v) > 100:
            raise ValueError("Nome da empresa máximo 100 caracteres")
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

    @field_validator("category")
    @classmethod
    def category_valid(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in VALID_CATEGORIES:
            raise ValueError(
                f"Categoria inválida. Use: {', '.join(sorted(VALID_CATEGORIES))}"
            )
        return v

    @field_validator("job_type")
    @classmethod
    def job_type_valid(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in VALID_JOB_TYPES:
            raise ValueError(
                f"Tipo de vaga inválido. Use: {', '.join(sorted(VALID_JOB_TYPES))}"
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

    @field_validator("salary_range")
    @classmethod
    def salary_range_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if len(v) > 100:
            raise ValueError("Faixa salarial máximo 100 caracteres")
        return v or None

    @field_validator("apply_url")
    @classmethod
    def url_must_be_http(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL deve começar com http:// ou https://")
        return v


class JobResponse(BaseModel):
    id: str
    title: str
    company: str
    description: str
    category: str
    job_type: str
    zip_code: Optional[str]
    salary_range: Optional[str]
    apply_url: Optional[str]
    contact_email: Optional[str]
    expires_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class JobWithDistanceResponse(JobResponse):
    distance_miles: Optional[float] = None


class JobListResponse(BaseModel):
    items: List[JobResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class JobSearchResponse(BaseModel):
    items: List[JobWithDistanceResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
    search_zip: str
    radius_miles: float
