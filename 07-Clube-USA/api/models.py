from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: str | None = None
    state: str | None = None
    city: str | None = None
    zip_code: str | None = None
    referral_code: str | None = None  # Fase 0.2: atribuição de indicação

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter pelo menos 8 caracteres")
        return v

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nome é obrigatório")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ResendConfirmationRequest(BaseModel):
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str


class UserProfile(BaseModel):
    id: str
    email: str
    name: str
    phone: str | None
    state: str | None
    city: str | None
    zip_code: str | None
    email_confirmed: bool
    referral_code: str | None
    created_at: str


class ReferralStats(BaseModel):
    referral_code: str | None
    referral_count: int
    referral_url: str | None


class RegistrationValidity(BaseModel):
    is_valid: bool
    email_confirmed: bool
    has_location: bool
    required_actions: list[str]


class UsersMetrics(BaseModel):
    total: int
    confirmed: int
    unconfirmed: int
    confirmation_rate: float
    new_last_7d: int
    new_last_30d: int
    valid_registrations: int  # confirmados + localização preenchida
    valid_rate: float


class ReferralMetrics(BaseModel):
    total_attributed: int
    attribution_rate: float


class EventMetrics(BaseModel):
    logins_last_7d: int
    logins_last_30d: int
    registrations_last_7d: int
    registrations_last_30d: int


class AdminMetrics(BaseModel):
    users: UsersMetrics
    referrals: ReferralMetrics
    events: EventMetrics
    as_of: str


class PromotionCategory(str, Enum):
    supermercado = "supermercado"
    restaurante = "restaurante"
    roupa = "roupa"
    eletronica = "eletronica"
    servicos = "servicos"
    saude = "saude"
    educacao = "educacao"
    transporte = "transporte"
    outros = "outros"


class CreatePromotionRequest(BaseModel):
    title: str
    description: str
    url: str
    image_url: str | None = None
    category: PromotionCategory
    zip_code: str | None = None
    state: str | None = None
    expires_at: str | None = None
    is_featured: bool = False

    @field_validator("title", "description")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Campo não pode estar vazio")
        return v


class UpdatePromotionRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    url: str | None = None
    image_url: str | None = None
    category: PromotionCategory | None = None
    zip_code: str | None = None
    state: str | None = None
    expires_at: str | None = None
    is_featured: bool | None = None
    is_active: bool | None = None


class PromotionResponse(BaseModel):
    id: str
    title: str
    description: str
    url: str
    image_url: str | None
    category: str
    zip_code: str | None
    state: str | None
    expires_at: str | None
    is_featured: bool
    is_urgent: bool
    is_active: bool
    created_at: str

    @classmethod
    def from_db(cls, p: dict) -> "PromotionResponse":
        is_urgent = False
        if p.get("expires_at"):
            try:
                raw = p["expires_at"]
                exp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                delta = (exp - datetime.now(timezone.utc)).total_seconds()
                is_urgent = 0 <= delta <= 86400
            except Exception:
                pass
        return cls(
            id=p["id"],
            title=p["title"],
            description=p["description"],
            url=p["url"],
            image_url=p.get("image_url"),
            category=p["category"],
            zip_code=p.get("zip_code"),
            state=p.get("state"),
            expires_at=p.get("expires_at"),
            is_featured=p.get("is_featured", False),
            is_urgent=is_urgent,
            is_active=p.get("is_active", True),
            created_at=p["created_at"],
        )


class PromotionListResponse(BaseModel):
    items: list[PromotionResponse]
    total: int


class UpdateProfileRequest(BaseModel):
    name: str | None = None
    phone: str | None = None
    state: str | None = None
    city: str | None = None
    zip_code: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Nome não pode ser vazio")
        return v
