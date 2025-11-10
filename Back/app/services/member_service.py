from datetime import date
from typing import Dict, List, Optional, Tuple, Any
from fastapi import HTTPException, status
from ..repositories.member_repository import MemberRepository
from ..repositories.checkin_repository import CheckInRepository
from ..schemas.member import MemberCreate, MemberUpdate
from ..utils.validators import validate_phone_number

class MemberService:
    def __init__(self, db: Any):
        # db is expected to be a cursor (DictCursor) from get_db()
        self.db = db
        self.member_repo = MemberRepository()
        self.checkin_repo = CheckInRepository()

    def create_member(self, member_data: MemberCreate) -> dict:
        # 전화번호 검증
        if not validate_phone_number(member_data.phone_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="잘못된 전화번호 형식입니다."
            )
        # 전화번호 중복 체크
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

        # 전화번호 변경 시 중복 체크
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

        return self.member_repo.update_member(self.db, member_id, update_data)

    def delete_member(self, member_id: int) -> bool:
        # soft delete by member_id
        return self.member_repo.soft_delete_member(self.db, member_id)

    def search_by_last_four_digits(self, last_four: str) -> List[dict]:
        members = self.member_repo.search_by_last_four_digits(self.db, last_four)
        return members

    def get_members_list(
        self,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> Tuple[List[dict], int]:
        skip = (page - 1) * size
        return self.member_repo.get_members_paginated(
            self.db,
            skip=skip,
            limit=size,
            search=search,
            status=status
        )

    def check_member_validity(self, member_id: int) -> Dict:
        member = self.get_member(member_id)
        today = date.today()

        # 회원권 만료 체크
        membership_end = member.get('membership_end_date')
        if membership_end and membership_end < today:
            return {
                "status": "expired",
                "message": "회원권이 만료되었습니다.",
                "member_info": {
                    "name": member.get('name'),
                    "membership_end_date": membership_end,
                    "locker_rental": None,
                    "uniform_rental": None
                }
            }

        # 만료 임박 경고
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
                "locker_rental": None,
                "uniform_rental": None
            },
            "warnings": warnings
        }