from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, validator

class UniformRentalCreate(BaseModel):
    rental_type: str

    @validator('rental_type')
    def validate_rental_type(cls, v):
        valid_types = ["1개월", "3개월", "6개월", "1년"]
        if v not in valid_types:
            raise ValueError('올바른 대여 기간이 아닙니다')
        return v

class UniformRentalResponse(BaseModel):
    uniform_rental_id: int
    member_id: int
    rental_type: str
    start_date: date
    end_date: date
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True