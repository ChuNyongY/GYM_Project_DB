from datetime import date
from typing import Dict, List, Optional, Tuple, Any
from fastapi import HTTPException, status
import re

from ..repositories.member_repository import MemberRepository
from ..schemas.member import MemberCreate, MemberUpdate

def validate_phone_number(phone: str) -> bool:
    pattern = r"^010-?\d{4}-?\d{4}$"
    return bool(re.match(pattern, phone))

class MemberService:
    def __init__(self, db: Any):
        # db is expected to be a cursor (DictCursor) from get_db()
        self.db = db
        self.member_repo = MemberRepository()

    def create_member(self, member_data: MemberCreate) -> dict:
        # 1. 전화번호 검증
        if not validate_phone_number(member_data.phone_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="잘못된 전화번호 형식입니다."
            )
            
        # 2. 전화번호 중복 체크
        if self.member_repo.get_member_by_phone(self.db, member_data.phone_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 전화번호입니다."
            )
            
        return self.member_repo.create_member(self.db, member_data)

    def get_member(self, member_id: int) -> dict:
        member = self.member_repo.get_member_by_id(self.db, member_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="회원을 찾을 수 없습니다."
            )
        return member

    def update_member(self, member_id: int, update_data: MemberUpdate) -> dict:
        member = self.get_member(member_id)

        # 전화번호 변경 시 검증 및 중복 체크
        if getattr(update_data, 'phone_number', None) and update_data.phone_number != member.get('phone_number'):
            if not validate_phone_number(update_data.phone_number):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="잘못된 전화번호 형식입니다."
                )
            if self.member_repo.get_member_by_phone(self.db, update_data.phone_number):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 등록된 전화번호입니다."
                )

        return self.member_repo.update_member_pydantic(self.db, member_id, update_data)

    def delete_member(self, member_id: int) -> bool:
        return self.member_repo.soft_delete_member(self.db, member_id)

    # 키오스크 호환용
    def search_by_last_four_digits(self, last_four: str) -> List[dict]:
        return self.member_repo.list_members_by_phone_tail(self.db, last_four)
    
    def search_by_phone_tail(self, tail: str):
         return self.search_by_last_four_digits(tail)

    # [수정] gender, sort_by 인자가 추가되었습니다. (500 에러 해결)
    def get_members_list(
        self,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        gender: Optional[str] = None,
        sort_by: Optional[str] = None
    ) -> Tuple[List[dict], int]:
        skip = (page - 1) * size
        return self.member_repo.get_members_paginated(
            self.db,
            skip=skip,
            limit=size,
            search=search,
            status=status,
            gender=gender,
            sort_by=sort_by
        )

    def check_member_validity(self, member_id: int) -> Dict:
        member = self.get_member(member_id)
        today = date.today()

        membership_end = member.get('membership_end_date')
        if membership_end and membership_end < today:
            return {
                "status": "expired",
                "message": "회원권이 만료되었습니다.",
                "member_info": {
                    "name": member.get('name'),
                    "membership_end_date": membership_end,
                }
            }

        warnings = []
        if membership_end:
            days_to_expiry = (membership_end - today).days
            if 0 <= days_to_expiry <= 7:
                warnings.append({
                    "type": "membership_expiring",
                    "message": f"회원권이 {days_to_expiry}일 후 만료됩니다.",
                    "days_remaining": days_to_expiry
                })

        return {
            "status": "active",
            "member_info": {
                "name": member.get('name'),
                "membership_end_date": membership_end,
            },
            "warnings": warnings
        }
    
    def extend_membership(self, member_id: int, membership_type_id: int):
         return {"status": "success", "message": "회원 정보 수정에서 기간을 변경해주세요."}