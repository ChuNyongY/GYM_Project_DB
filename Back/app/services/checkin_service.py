from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
from fastapi import HTTPException, status
from ..repositories.checkin_repository import CheckinRepository
from ..repositories.member_repository import MemberRepository

class CheckinService:
    def __init__(self, db: Any):
        self.db = db

    def process_checkin(self, member_id: int) -> Dict:
        """일반 입장 처리"""
        member = MemberRepository.get_member_by_id(self.db, member_id)
        if not member:
            raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다.")

        active_checkin = CheckinRepository.get_active_checkin(self.db, member_id)
        if active_checkin:
            print(f"❌ [체크인 실패] member_id={member_id}의 active_checkin 존재: {active_checkin}")
            raise HTTPException(status_code=400, detail="이미 입장 상태입니다.")

        print(f"✅ [체크인 시작] member_id={member_id}, 이전 기록 없음")
        
        today = datetime.now().date()
        membership_end = member.get('membership_end_date')
        
        if membership_end and membership_end < today:
            raise HTTPException(status_code=403, detail="회원권이 만료되었습니다.")

        checkin = CheckinRepository.create_checkin(self.db, member_id)

        # 입장 시 members 테이블 업데이트: checkin_time 설정, checkout_time NULL로 초기화
        update_sql = "UPDATE members SET checkin_time = %s, checkout_time = NULL WHERE member_id = %s"
        self.db.execute(update_sql, (checkin.get('checkin_time'), member_id))
        self.db.connection.commit()

        response = {
            "status": "success",
            "member_info": {
                "name": member.get('name'),
                "membership_end_date": membership_end
            },
            "checkin_time": checkin.get('checkin_time').strftime("%Y-%m-%d %H:%M:%S"),
            "warnings": []
        }

        days_to_expiry = (membership_end - today).days if membership_end else None
        if days_to_expiry is not None and 0 <= days_to_expiry <= 7:
            response["warnings"].append({
                "type": "membership_expiring",
                "message": f"회원권이 {days_to_expiry}일 후 만료됩니다.",
                "days_remaining": days_to_expiry
            })

        return response

    def process_checkout(self, checkin_id: int) -> Dict:
        """퇴장 처리"""
        checkin = CheckinRepository.get_checkin_by_id(self.db, checkin_id)
        if not checkin:
            raise HTTPException(status_code=404, detail="출입 기록을 찾을 수 없습니다.")

        if checkin.get('checkout_time'):
            raise HTTPException(status_code=400, detail="이미 퇴장 처리된 기록입니다.")

        print(f"🔵 [퇴장 시작] checkin_id={checkin_id}, member_id={checkin.get('member_id')}")
        
        updated_checkin = CheckinRepository.update_checkout(self.db, checkin_id)
        
        print(f"✅ [퇴장 완료] checkin_id={checkin_id}, checkout_time={updated_checkin.get('checkout_time')}")
        
        duration = updated_checkin.get('checkout_time') - updated_checkin.get('checkin_time')

        # 회원 정보 조회 (이름 반환용)
        member = MemberRepository.get_member_by_id(self.db, checkin.get('member_id'))

        # 퇴장 시에는 is_active를 변경하지 않음 (관리자가 삭제 버튼을 눌렀을 때만 변경)
        # members 테이블에서 checkin_time을 NULL로, checkout_time 업데이트
        update_sql = "UPDATE members SET checkin_time = NULL, checkout_time = %s WHERE member_id = %s"
        self.db.execute(update_sql, (updated_checkin.get('checkout_time'), checkin.get('member_id')))
        self.db.connection.commit()

        return {
            "status": "success",
            "checkin_id": checkin.get('id'),
            "member_id": checkin.get('member_id'),
            "member_name": member.get('name') if member else None,
            "membership_end_date": member.get('membership_end_date') if member else None,
            "checkin_time": checkin.get('checkin_time').strftime("%Y-%m-%d %H:%M:%S"),
            "checkout_time": updated_checkin.get('checkout_time').strftime("%Y-%m-%d %H:%M:%S"),
            "duration_minutes": int(duration.total_seconds() / 60)
        }

    def get_today_checkins(self, page: int = 1, size: int = 50) -> Tuple[List[dict], int]:
        skip = (page - 1) * size
        return CheckinRepository.get_today_checkins(self.db, skip, size)

    def get_member_checkins(self, member_id: int, year: int, month: int) -> List[dict]:
        if not MemberRepository.get_member_by_id(self.db, member_id):
            raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다.")
        return CheckinRepository.get_member_checkins(self.db, member_id, year, month)
    
    # [키오스크용 함수]
    def process_checkin_by_id(self, member_id: int):
        member = MemberRepository.get_member_by_id(self.db, member_id)
        if not member:
            raise ValueError("회원 정보가 없습니다.")
            
        if member['membership_end_date'] and member['membership_end_date'] < datetime.now().date():
             return {"status": "expired", "message": "회원권이 만료되었습니다."}

        CheckinRepository.create_checkin(self.db, member_id)
        
        return {
            "status": "success", 
            "message": f"{member['name']}님 환영합니다!",
            "member_name": member['name']
        }