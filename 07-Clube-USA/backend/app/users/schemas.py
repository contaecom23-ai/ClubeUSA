from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str
    zip_code: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    email_confirmed: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    zip_code: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None

    def non_empty_fields(self) -> dict:
        data = self.model_dump(exclude_none=True)
        # Strip strings; drop empty strings
        return {k: v.strip() for k, v in data.items() if isinstance(v, str) and v.strip()}
