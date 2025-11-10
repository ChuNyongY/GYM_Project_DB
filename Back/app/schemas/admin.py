from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class AdminCreate(BaseModel):
    password: str

class AdminUpdate(BaseModel):
    current_password: str
    new_password: str

class AdminResponse(BaseModel):
    admin_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True