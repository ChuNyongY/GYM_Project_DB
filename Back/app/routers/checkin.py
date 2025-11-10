from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Dict, Optional, Any
from pydantic import BaseModel
from datetime import datetime
from ..database import get_db
from ..services.member_service import MemberService
from ..services.checkin_service import CheckInService
from ..utils.security import oauth2_scheme

router = APIRouter(tags=["checkin"])


# ==================== Pydantic 모델 ====================

class KioskCheckinRequest(BaseModel):
    """키오스크 체크인 요청"""
    phone_last_four: str

    class Config:
        json_schema_extra = {
            "example": {
                "phone_last_four": "5678"
            }
        }


# ==================== 키오스크 체크인 (인증 불필요) ⭐ 새로 추가 ====================

@router.post("")
async def kiosk_checkin(
    request: KioskCheckinRequest,
    db = Depends(get_db)
) -> Dict:
    """
    키오스크 체크인 (전화번호 뒷자리 4자리)
    
    - **phone_last_four**: 전화번호 뒷자리 4자리
    - 인증 불필요 (키오스크용)
    """
    phone_last_four = request.phone_last_four.strip()
    
    # 4자리 숫자인지 검증
    if len(phone_last_four) != 4 or not phone_last_four.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="전화번호 뒷자리 4자리를 정확히 입력해주세요."
        )
    
    try:
        # 전화번호 뒷자리로 회원 찾기
        sql = """
        SELECT id, name, phone, end_date, is_active
        FROM members
        WHERE phone LIKE %s AND is_active = TRUE
        """
        db.execute(sql, (f"%{phone_last_four}",))
        members = db.fetchall()
        
        if not members:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="등록된 회원을 찾을 수 없습니다. 프론트 데스크에 문의하세요."
            )
        
        if len(members) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="여러 명의 회원이 검색되었습니다. 프론트 데스크에 문의하세요."
            )
        
        member = members[0]
        
        # 회원권 만료 확인
        if member['end_date']:
            end_date = member['end_date']
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            elif hasattr(end_date, 'date'):
                end_date = end_date.date() if callable(end_date.date) else end_date
            
            if end_date < datetime.now().date():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"{member['name']}님, 회원권이 만료되었습니다. 프론트 데스크에서 갱신해주세요."
                )
        
        # 출입 기록 저장
        checkin_sql = """
        INSERT INTO checkins (member_id, created_at)
        VALUES (%s, NOW())
        """
        db.execute(checkin_sql, (member['id'],))
        db.connection.commit()
        
        return {
            "status": "success",
            "message": f"{member['name']}님 환영합니다! 😊",
            "member": {
                "id": member['id'],
                "name": member['name'],
                "phone": member['phone']
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"체크인 처리 실패: {str(e)}"
        )


# ==================== 기존 엔드포인트 ====================

@router.get("/today")
async def get_today_checkins(
    page: int = Query(1, gt=0),
    size: int = Query(50, gt=0),
    db = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """당일 체크인 목록 조회 (관리자용)"""
    checkin_service = CheckInService(db)
    checkins, total = checkin_service.get_today_checkins(page, size)

    return {
        "total": total,
        "page": page,
        "size": size,
        "checkins": checkins
    }


@router.put("/{checkin_id}/checkout")
async def process_checkout(
    checkin_id: int,
    db = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """체크아웃 처리 (관리자용)"""
    checkin_service = CheckInService(db)
    return checkin_service.process_checkout(checkin_id)


@router.get("/member/{member_id}")
async def get_member_checkins(
    member_id: int,
    year: int = Query(...),
    month: int = Query(...),
    db = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """회원별 체크인 기록 조회 (관리자용)"""
    checkin_service = CheckInService(db)
    checkins = checkin_service.get_member_checkins(member_id, year, month)

    return {
        "member_id": member_id,
        "year": year,
        "month": month,
        "total_checkins": len(checkins),
        "checkins": checkins
    }