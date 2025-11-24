from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class CheckInLogCreate(BaseModel):
    member_id: int

class CheckInLogResponse(BaseModel):
    checkin_id: int
    member_id: int
    checkin_time: datetime
    checkout_time: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True