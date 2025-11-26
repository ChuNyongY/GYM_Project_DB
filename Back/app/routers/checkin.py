from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict
from pydantic import BaseModel
from datetime import datetime
from ..database import get_db
from ..services.checkin_service import CheckinService
from ..utils.security import oauth2_scheme

# [수정] prefix와 tags는 main.py에서 설정하므로 여기서는 비워둡니다.
router = APIRouter()


class KioskCheckinRequest(BaseModel):
    phone_last_four: str
    candidate_id: int | None = None

# ==================== 키오스크 체크인 ====================

@router.post("")
async def kiosk_checkin(
    request: KioskCheckinRequest,
    db = Depends(get_db)
) -> Dict:
    phone_tail = request.phone_last_four.strip()
    candidate_id = request.candidate_id
    print(f"🔍 [키오스크] 검색 요청: {phone_tail}, 후보 id: {candidate_id}")

    if len(phone_tail) != 4 or not phone_tail.isdigit():
        raise HTTPException(status_code=400, detail="숫자 4자리를 입력해주세요.")

    try:
        # 먼저 삭제된 회원인지 확인
        deleted_check_sql = """
        SELECT member_id, name FROM deleted_members
        WHERE RIGHT(phone_number, 4) = %s
        """
        db.execute(deleted_check_sql, (phone_tail,))
        deleted_member = db.fetchone()
        if deleted_member:
            raise HTTPException(
                status_code=403, 
                detail=f"휴면회원입니다. 카운터에 문의하세요."
            )
        
        # 후보 id가 있으면 해당 회원으로 체크인
        if candidate_id:
            sql = """
            SELECT member_id, name, phone_number, membership_end_date, is_active
            FROM members
            WHERE member_id = %s AND RIGHT(phone_number, 4) = %s
            """
            db.execute(sql, (candidate_id, phone_tail))
            member = db.fetchone()
            if not member:
                raise HTTPException(status_code=404, detail="선택한 회원을 찾을 수 없습니다.")
        else:
            # 후보 id 없으면 4자리로 전체 검색
            sql = """
            SELECT member_id, name, phone_number, membership_end_date, is_active
            FROM members
            WHERE RIGHT(phone_number, 4) = %s
            """
            db.execute(sql, (phone_tail,))
            members = db.fetchall()
            if not members:
                raise HTTPException(status_code=404, detail="등록된 회원이 없습니다.")
            if len(members) > 1:
                # 동명이인 후보 리스트 반환
                candidates = [
                    {
                        "member_id": m["member_id"],
                        "name": m["name"],
                        "phone_number": m["phone_number"],
                        "is_active": m["is_active"]
                    }
                    for m in members
                ]
                return {"status": "duplicate", "members": candidates}
            member = members[0]

        # CheckinService를 사용하여 체크인 처리
        checkin_service = CheckinService(db)
        return checkin_service.process_checkin(member['member_id'])

    except HTTPException:
        raise
    except Exception as e:
        db.connection.rollback()
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="서버 오류")

# ==================== 관리자용 ====================
@router.get("/today")
async def get_today_checkins(page: int = Query(1), size: int = Query(50), db = Depends(get_db)):
    checkin_service = CheckinService(db)
    checkins, total = checkin_service.get_today_checkins(page, size)
    return {"total": total, "page": page, "size": size, "checkins": checkins}

@router.put("/{checkin_id}/checkout")
async def process_checkout(checkin_id: int, db = Depends(get_db)):
    checkin_service = CheckinService(db)
    return checkin_service.process_checkout(checkin_id)

@router.get("/member/{member_id}")
async def get_member_checkins(member_id: int, year: int = Query(...), month: int = Query(...), db = Depends(get_db)):
    checkin_service = CheckinService(db)
    checkins = checkin_service.get_member_checkins(member_id, year, month)
    return {"checkins": checkins}