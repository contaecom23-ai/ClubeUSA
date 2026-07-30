from pydantic import BaseModel


class ProfileResponse(BaseModel):
    user_id: str
    full_name: str
    email: str
    phone: str | None
    zip_code: str | None
    state: str | None
    city: str | None
    bio: str | None
    email_confirmed: bool


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    zip_code: str | None = None
    state: str | None = None
    city: str | None = None
    bio: str | None = None
