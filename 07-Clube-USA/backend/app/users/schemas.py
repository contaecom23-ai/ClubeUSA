from typing import Optional
from pydantic import BaseModel


class UserProfile(BaseModel):
    id: str
    email: str
    email_confirmed: bool
    full_name: str
    phone: Optional[str] = None
    zip_code: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    created_at: str


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    zip_code: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
