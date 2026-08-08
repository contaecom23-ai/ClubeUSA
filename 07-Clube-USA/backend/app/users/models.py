from typing import Optional
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserProfile(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str]
    city: Optional[str]
    state_abbr: Optional[str]
    email_confirmed: bool
    created_at: datetime


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    city: Optional[str] = None
    state_abbr: Optional[str] = None

    model_config = {"str_strip_whitespace": True}
