from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from ..database import get_db
from ..services.member_service import MemberService
from ..services.checkin_service import CheckInService
from ..schemas.member import MemberCreate, MemberUpdate, MemberResponse
from ..schemas.checkin_log import CheckInLogCreate, CheckInLogResponse

router = APIRouter(prefix="/api/kiosk", tags=["kiosk"])

@router.post("/search-by-phone")
def search_by_phone(
    last_four_digits: str,
    db = Depends(get_db)
) -> Dict:
    if not last_four_digits.isdigit() or len(last_four_digits) != 4:
        raise HTTPException(
            status_code=400,
            detail="전화번호 뒷자리 4자리를 입력해주세요."
        )

    member_service = MemberService(db)
    members = member_service.search_by_last_four_digits(last_four_digits)

    if not members:
        return {
            "status": "not_found",
            "message": "등록된 회원이 없습니다."
        }

    response = {
        "status": "success" if len(members) == 1 else "duplicate",
        "count": len(members),
        "members": [
            {
                "member_id": m.get('member_id'),
                "name": m.get('name'),
                "phone_number": m.get('phone_number')
            }
            for m in members
        ]
    }

    return response

@router.post("/checkin/{member_id}")
def member_checkin(
    member_id: int,
    db = Depends(get_db)
) -> Dict:
    member_service = MemberService(db)
    checkin_service = CheckInService(db)

    # 회원 상태 확인
    validity = member_service.check_member_validity(member_id)
    if validity["status"] == "expired":
        return validity

    # 입장 처리
    checkin_result = checkin_service.process_checkin(member_id)
    return checkin_result