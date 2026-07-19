from typing import Optional
from pydantic import BaseModel
from datetime import datetime

# Estados americanos (validação básica de 2 letras)
_US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
    "VA","WA","WV","WI","WY","DC",
}


class ProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    city: Optional[str] = None
    state: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    phone: Optional[str] = None

    def model_post_init(self, _):
        if self.state and self.state.upper() not in _US_STATES:
            raise ValueError(f"Estado inválido: {self.state}")
        if self.state:
            self.state = self.state.upper()
        if self.full_name:
            self.full_name = self.full_name.strip()
            if len(self.full_name) < 2:
                raise ValueError("Nome deve ter ao menos 2 caracteres.")
