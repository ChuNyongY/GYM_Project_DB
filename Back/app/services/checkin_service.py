from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from fastapi import HTTPException, status
from ..repositories.checkin_repository import CheckInRepository
from ..repositories.member_repository import MemberRepository
from ..utils.date_utils import format_datetime_kst


class CheckInService:
    def __init__(self, db: Any):
        # db is expected to be a cursor (DictCursor)
        self.db = db
        self.checkin_repo = CheckInRepository()
        self.member_repo = MemberRepository()

    def process_checkin(self, member_id: int) -> Dict:
        # 회원 존재 여부 확인
        member = self.member_repo.get_member_by_id(self.db, member_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="회원을 찾을 수 없습니다."
            )

        # 이미 입장한 상태인지 확인
        active_checkin = self.checkin_repo.get_active_checkin(self.db, member_id)
        if active_checkin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 입장 상태입니다."
            )

        # 회원권 만료 여부 확인
        today = datetime.now().date()
        # member is a dict; membership_end_date may be a datetime.date
        membership_end = member.get('membership_end_date')
        if membership_end and membership_end < today:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="회원권이 만료되었습니다."
            )

        # 입장 처리
        checkin = self.checkin_repo.create_checkin(self.db, member_id)

        response = {
            "status": "success",
            "member_info": {
                "name": member.get('name'),
                "membership_end_date": membership_end
            },
            "checkin_time": format_datetime_kst(checkin.get('checkin_time')),
            "warnings": []
        }

        # 만료 임박 경고
        days_to_expiry = (membership_end - today).days if membership_end else None
        if days_to_expiry is not None and 0 <= days_to_expiry <= 7:
            response["warnings"].append({
                "type": "membership_expiring",
                "message": f"회원권이 {days_to_expiry}일 후 만료됩니다.",
                "days_remaining": days_to_expiry
            })

        return response

    def process_checkout(self, checkin_id: int) -> Dict:
        checkin = self.checkin_repo.get_checkin_by_id(self.db, checkin_id)
        if not checkin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="출입 기록을 찾을 수 없습니다."
            )

        if checkin.get('checkout_time'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 퇴장 처리된 기록입니다."
            )

        updated_checkin = self.checkin_repo.update_checkout(self.db, checkin_id)
        duration = updated_checkin.get('checkout_time') - updated_checkin.get('checkin_time')

        return {
            "status": "success",
            "checkin_id": checkin.get('checkin_id'),
            "member_id": checkin.get('member_id'),
            "checkin_time": format_datetime_kst(checkin.get('checkin_time')),
            "checkout_time": format_datetime_kst(updated_checkin.get('checkout_time')),
            "duration_minutes": int(duration.total_seconds() / 60)
        }

    def get_today_checkins(
        self,
        page: int = 1,
        size: int = 50
    ) -> Tuple[List[dict], int]:
        skip = (page - 1) * size
        return self.checkin_repo.get_today_checkins(self.db, skip, size)

    def get_member_checkins(
        self,
        member_id: int,
        year: int,
        month: int
    ) -> List[dict]:
        if not self.member_repo.get_member_by_id(self.db, member_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="회원을 찾을 수 없습니다."
            )
        return self.checkin_repo.get_member_checkins(self.db, member_id, year, month)