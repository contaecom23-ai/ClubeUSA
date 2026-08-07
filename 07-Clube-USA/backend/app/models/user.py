from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=100)

    @field_validator("full_name")
    @classmethod
    def full_name_no_html(cls, v: str) -> str:
        if "<" in v or ">" in v:
            raise ValueError("Nome inválido.")
        return v.strip()


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    zip_code: str | None = Field(default=None, max_length=10)
    state: str | None = Field(default=None, max_length=2)
    city: str | None = Field(default=None, max_length=100)
    bio: str | None = Field(default=None, max_length=300)

    @field_validator("full_name", "city", "bio", mode="before")
    @classmethod
    def strip_and_no_html(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if "<" in v or ">" in v:
            raise ValueError("Valor inválido.")
        return v.strip()


class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str
    phone: str | None
    zip_code: str | None
    state: str | None
    city: str | None
    bio: str | None
    email_confirmed: bool
    created_at: datetime

    @classmethod
    def from_db(cls, row: dict) -> "UserProfile":
        return cls(
            id=row["id"],
            email=row["email"],
            full_name=row["full_name"],
            phone=row.get("phone"),
            zip_code=row.get("zip_code"),
            state=row.get("state"),
            city=row.get("city"),
            bio=row.get("bio"),
            email_confirmed=row.get("email_confirmed", False),
            created_at=row["created_at"],
        )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


class MessageResponse(BaseModel):
    message: str
