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


# =============================================================
# Fase 1.3 — Programa de Influenciadores
# =============================================================

BADGE_THRESHOLDS: list[tuple[int, str]] = [
    (1000, "hall_da_fama"),
    (250, "embaixador"),
    (50, "parceiro"),
]


def compute_badge(valid_referrals: int) -> tuple[str, str | None, int | None]:
    """Retorna (badge_atual, proximo_badge, referrals_para_proximo)."""
    current = "none"
    for threshold, badge in BADGE_THRESHOLDS:
        if valid_referrals >= threshold:
            current = badge
            break
    # próximo badge
    for threshold, badge in reversed(BADGE_THRESHOLDS):
        if valid_referrals < threshold:
            return current, badge, threshold
    return current, None, None


class InfluencerStatus(BaseModel):
    valid_referrals: int
    badge: str
    next_badge: str | None
    next_badge_at: int | None            # quantos referrals faltam para o próximo nível
    estimated_earning_usd: float | None  # None = taxa não configurada pelo dono
    total_paid_usd: float


class LeaderboardEntry(BaseModel):
    rank: int
    display_name: str
    city: str | None
    state: str | None
    valid_referrals: int
    badge: str


class InfluencerLeaderboard(BaseModel):
    entries: list[LeaderboardEntry]
    payout_rate_usd: float | None  # None = programa ainda sem valor definido


class InfluencerPendingItem(BaseModel):
    user_id: str
    display_name: str
    valid_referrals: int
    badge: str
    estimated_owed_usd: float   # (valid_referrals * rate) - total_paid
    total_paid_usd: float


class RegisterPayoutRequest(BaseModel):
    user_id: str
    amount_usd: float
    payment_method: str  # paypal | venmo | zelle | check | other
    payment_ref: str | None = None
    notes: str | None = None

    @field_validator("amount_usd")
    @classmethod
    def positive_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Valor do pagamento deve ser positivo")
        return round(v, 2)

    @field_validator("payment_method")
    @classmethod
    def valid_method(cls, v: str) -> str:
        allowed = {"paypal", "venmo", "zelle", "check", "other"}
        if v.lower() not in allowed:
            raise ValueError(f"Método inválido. Use: {', '.join(sorted(allowed))}")
        return v.lower()


class PayoutResponse(BaseModel):
    id: str
    user_id: str
    valid_referrals: int
    amount_usd: float
    payment_method: str
    payment_ref: str | None
    notes: str | None
    created_at: str


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
