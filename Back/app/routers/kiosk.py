from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List
from pydantic import BaseModel
from ..database import get_db
from ..services.member_service import MemberService
from ..services.checkin_service import CheckinService

# 1️⃣ main.py에서 prefix="/api/kiosk"를 설정했으므로 여기서는 지웁니다.
router = APIRouter(tags=["kiosk"])

# 2️⃣ 요청 데이터 정의 (수정됨)
# 'phone' 대신 더 명확한 'phone_number' 사용
class PhoneSearchRequest(BaseModel):
    phone_number: str 

@router.post("/search-by-phone")
def search_by_phone(
    request: PhoneSearchRequest, 
    db = Depends(get_db)
) -> Dict:
    # 3️⃣ request.phone_number로 접근
    search_query = request.phone_number
    
    # 혹시 모를 공백 제거
    search_query = search_query.strip()

    # 입력값이 전체 번호일 수도 있고 뒷자리일 수도 있으니
    # 안전하게 뒤에서 4자리만 자릅니다.
    if len(search_query) > 4:
        search_query = search_query[-4:] 

    # 유효성 검사 (숫자인지, 4자리인지)
    if not search_query.isdigit() or len(search_query) != 4:
        raise HTTPException(
            status_code=400,
            detail="전화번호 뒷자리 4자리를 정확히 입력해주세요."
        )

    member_service = MemberService(db)
    # 서비스 호출 (뒷자리 4개로 검색)
    members = member_service.search_by_last_four_digits(search_query)

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
                # DB에서 가져온 실제 컬럼명도 phone_number 일치
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
    checkin_service = CheckinService(db)

    # 회원 상태 확인
    validity = member_service.check_member_validity(member_id)
    if validity["status"] == "expired":
        return validity

    # 입장 처리
    checkin_result = checkin_service.process_checkin(member_id)
    return checkin_result

@router.post("/checkout/{member_id}")
def member_checkout(
    member_id: int,
    db = Depends(get_db)
) -> Dict:
    checkin_service = CheckinService(db)
    # 현재 입장 중인 체크인 기록 찾기
    from ..repositories.checkin_repository import CheckinRepository
    active_checkin = CheckinRepository.get_active_checkin(db, member_id)
    if not active_checkin:
        raise HTTPException(status_code=400, detail="입장 중인 기록이 없습니다.")
    # 퇴장 처리
    result = checkin_service.process_checkout(active_checkin['id'])
    # 회원 정보도 함께 반환
    from ..repositories.member_repository import MemberRepository
    member = MemberRepository.get_member_by_id(db, member_id)
    result['member_name'] = member.get('name') if member else None
    result['membership_end_date'] = member.get('membership_end_date') if member else None
    return result