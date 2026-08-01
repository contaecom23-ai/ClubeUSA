import re
from pydantic import BaseModel, EmailStr, field_validator

US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
    "VA","WA","WV","WI","WY","DC",
}


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    estado: str | None = None
    cidade: str | None = None
    whatsapp: str | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("senha deve ter ao menos 8 caracteres")
        return v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("nome não pode ser vazio")
        if len(v) > 100:
            raise ValueError("nome muito longo")
        return v

    @field_validator("estado")
    @classmethod
    def valid_state(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.upper().strip()
        if v not in US_STATES:
            raise ValueError(f"estado inválido: {v}")
        return v

    @field_validator("whatsapp")
    @classmethod
    def clean_whatsapp(cls, v: str | None) -> str | None:
        if v is None:
            return v
        digits = re.sub(r"\D", "", v)
        if digits and len(digits) < 8:
            raise ValueError("número de WhatsApp inválido")
        return digits or None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class MessageResponse(BaseModel):
    message: str
