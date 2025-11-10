from datetime import date, datetime
from typing import Optional, Annotated
from pydantic import BaseModel, Field

# 회원 생성 스키마
class MemberCreate(BaseModel):
    name: str
    phone_number: Annotated[str, Field(pattern=r"^01[0-9]{9}$")]  # 010xxxxxxxx 형식
    membership_type_id: int
    membership_start_date: date
    
class MemberUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[Annotated[str, Field(pattern=r"^01[0-9]{9}$")]] = None

class MemberResponse(BaseModel):
    member_id: int
    name: str
    phone_number: str
    membership_type_id: int
    membership_start_date: date
    membership_end_date: date
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True