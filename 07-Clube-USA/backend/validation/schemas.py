from typing import List
from pydantic import BaseModel


class ValidationStatusResponse(BaseModel):
    is_valid: bool
    email_confirmed: bool
    has_real_action: bool
    reasons: List[str]
