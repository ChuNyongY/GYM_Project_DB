from datetime import datetime
from pydantic import BaseModel

class MembershipTypeCreate(BaseModel):
    name: str
    duration_months: int

class MembershipTypeResponse(BaseModel):
    membership_type_id: int
    name: str
    duration_months: int
    created_at: datetime

    class Config:
        from_attributes = True