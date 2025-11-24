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
        # 후보 id가 있으면 해당 회원으로 체크인
        if candidate_id:
            sql = """
            SELECT member_id, name, phone_number, membership_end_date, is_active
            FROM members
            WHERE member_id = %s AND RIGHT(phone_number, 4) = %s AND is_active = TRUE
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
            WHERE RIGHT(phone_number, 4) = %s AND is_active = TRUE
            """
            db.execute(sql, (phone_tail,))
            members = db.fetchall()
            if not members:
                raise HTTPException(status_code=404, detail="등록된 회원이 없습니다.")
            if len(members) > 1:
                # 동명이인 후보 리스트 반환
                candidates = [
                    {
                        "id": m["member_id"],
                        "name": m["name"],
                        "phone_masked": m["phone_number"][:3] + "-****-" + m["phone_number"][-4:]
                    }
                    for m in members
                ]
                return {"status": "select", "candidates": candidates}
            member = members[0]

        # 만료 체크
        if member['membership_end_date']:
            end_date = member['membership_end_date']
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            elif hasattr(end_date, 'date'):
                end_date = end_date.date() if callable(end_date.date) else end_date
            if end_date < datetime.now().date():
                raise HTTPException(status_code=403, detail=f"{member['name']}님, 만료되었습니다.")

        # 1. 출입 로그 저장
        checkin_sql = "INSERT INTO checkins (member_id, checkin_time) VALUES (%s, NOW())"
        db.execute(checkin_sql, (member['member_id'],))

        # 2. 멤버 상태 업데이트 (관리자 페이지 실시간 반영용)
        update_sql = "UPDATE members SET checkin_time = NOW() WHERE member_id = %s"
        db.execute(update_sql, (member['member_id'],))

        db.connection.commit()

        # 남은 일수 계산
        days_left = None
        if member['membership_end_date']:
            end_date = member['membership_end_date']
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            elif hasattr(end_date, 'date'):
                end_date = end_date.date() if callable(end_date.date) else end_date
            days_left = (end_date - datetime.now().date()).days

        return {
            "status": "success",
            "message": f"{member['name']}님 환영합니다!",
            "member": {"id": member['member_id'], "name": member['name'], "days_left": days_left}
        }

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