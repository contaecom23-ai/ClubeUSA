from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProfileResponse(BaseModel):
    id: str
    email: str
    name: str
    zip_code: Optional[str]
    state_abbr: Optional[str]
    email_verified: bool
    created_at: datetime


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    zip_code: Optional[str] = Field(None, pattern=r"^\d{5}(-\d{4})?$")
    state_abbr: Optional[str] = Field(None, min_length=2, max_length=2)
