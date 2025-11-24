from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from enum import Enum

class GenderEnum(str, Enum):
    M = "M"
    F = "F"

class MemberCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone_number: str = Field(..., pattern=r"^010-?\d{4}-?\d{4}$")
    gender: GenderEnum  # 성별 필수
    membership_type: str
    membership_start_date: date
    membership_end_date: date
    locker_type: Optional[str] = None
    locker_start_date: Optional[date] = None
    locker_end_date: Optional[date] = None
    uniform_type: Optional[str] = None
    uniform_start_date: Optional[date] = None
    uniform_end_date: Optional[date] = None

class MemberUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    gender: Optional[GenderEnum] = None
    membership_type: Optional[str] = None
    membership_start_date: Optional[date] = None
    membership_end_date: Optional[date] = None
    locker_number: Optional[int] = None
    locker_type: Optional[str] = None
    locker_start_date: Optional[date] = None
    locker_end_date: Optional[date] = None
    uniform_type: Optional[str] = None
    uniform_start_date: Optional[date] = None
    uniform_end_date: Optional[date] = None

class MemberResponse(BaseModel):
    member_id: int
    member_rank: int
    name: str
    phone_number: str
    gender: GenderEnum # Enum(M/F)로 강제
    membership_type: Optional[str]
    membership_start_date: Optional[date]
    membership_end_date: Optional[date]
    locker_number: Optional[int]
    locker_type: Optional[str]
    locker_start_date: Optional[date]
    locker_end_date: Optional[date]
    uniform_type: Optional[str]
    uniform_start_date: Optional[date]
    uniform_end_date: Optional[date]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True