from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("A senha deve ter no mínimo 8 caracteres.")
        if len(v) > 128:
            raise ValueError("Senha muito longa (máx. 128 caracteres).")
        return v

    @field_validator("full_name")
    @classmethod
    def strip_name(cls, v: str | None) -> str | None:
        return v.strip() if v else None


class RegisterResponse(BaseModel):
    message: str
    email: str


class ConfirmEmailRequest(BaseModel):
    token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("A senha deve ter no mínimo 8 caracteres.")
        if len(v) > 128:
            raise ValueError("Senha muito longa (máx. 128 caracteres).")
        return v
