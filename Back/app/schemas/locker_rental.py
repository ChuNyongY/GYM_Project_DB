from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, validator

class LockerRentalCreate(BaseModel):
    locker_number: int
    rental_type: str

    @validator('locker_number')
    def validate_locker_number(cls, v):
        if not 1 <= v <= 100:
            raise ValueError('락커 번호는 1에서 100 사이여야 합니다')
        return v

    @validator('rental_type')
    def validate_rental_type(cls, v):
        valid_types = ["1개월", "3개월", "6개월", "1년"]
        if v not in valid_types:
            raise ValueError('올바른 대여 기간이 아닙니다')
        return v

class LockerRentalResponse(BaseModel):
    locker_rental_id: int
    member_id: int
    locker_number: int
    rental_type: str
    start_date: date
    end_date: date
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True