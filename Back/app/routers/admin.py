from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Dict, Optional
from pydantic import BaseModel
from datetime import date
from ..database import get_db
from ..services.admin_service import AdminService
from ..schemas.admin import AdminUpdate
from ..utils.security import oauth2_scheme

router = APIRouter(tags=["admin"])

class LoginRequest(BaseModel):
    password: str

class MemberCreateRequest(BaseModel):
    """회원 추가 요청"""
    name: str
    phone_number: str
    membership_type: str
    membership_start_date: date
    membership_end_date: date

    class Config:
        json_schema_extra = {
            "example": {
                "name": "홍길동",
                "phone_number": "010-9876-5432",
                "membership_type": "3개월",
                "membership_start_date": "2025-01-07",
                "membership_end_date": "2025-04-07"
            }
        }

class MemberUpdateRequest(BaseModel):
    """회원 정보 수정 요청"""
    name: Optional[str] = None
    phone_number: Optional[str] = None
    membership_type: Optional[str] = None
    membership_start_date: Optional[date] = None
    membership_end_date: Optional[date] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "김철수",
                "phone_number": "010-1234-5678",
                "membership_type": "6개월",
                "membership_start_date": "2025-01-07",
                "membership_end_date": "2025-07-07"
            }
        }


# === 관리자 로그인 ===
@router.post("/login")
def admin_login(
    request: LoginRequest,
    cursor = Depends(get_db)
) -> Dict:
    admin_service = AdminService(cursor)
    return admin_service.verify_admin(request.password)


# === 회원 추가 ===
@router.post("/members")
async def create_member(
    member_data: MemberCreateRequest,
    cursor = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    새 회원 추가
    
    - **name**: 이름 (필수)
    - **phone_number**: 전화번호 (필수)
    - **membership_type**: 회원권 종류 (3개월, 6개월, 1년)
    - **membership_start_date**: 시작일 (필수)
    - **membership_end_date**: 종료일 (필수)
    """
    admin_service = AdminService(cursor)
    await admin_service.get_current_admin(token)
    
    return admin_service.create_member(
        name=member_data.name,
        phone_number=member_data.phone_number,
        membership_type=member_data.membership_type,
        membership_start_date=member_data.membership_start_date.isoformat(),
        membership_end_date=member_data.membership_end_date.isoformat()
    )


# === 회원 목록 조회 ===
@router.get("/members")
async def get_members(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    cursor = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """회원 목록 조회"""
    admin_service = AdminService(cursor)
    await admin_service.get_current_admin(token)
    
    # 기본 쿼리
    sql = """
        SELECT 
            id as member_id,
            name,
            phone as phone_number,
            start_date as membership_start_date,
            end_date as membership_end_date,
            membership_type,
            is_active,
            created_at
        FROM members
        WHERE 1=1
    """
    params = []
    
    # 검색 조건
    if search:
        sql += " AND (name LIKE %s OR phone LIKE %s)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param])
    
    # 상태 필터
    if status == 'active':
        sql += " AND is_active = TRUE AND end_date >= CURDATE()"
    elif status == 'inactive':
        sql += " AND is_active = FALSE"
    elif status == 'expiring_soon':
        sql += " AND is_active = TRUE AND end_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)"
    
    # 정렬 및 페이지네이션
    offset = (page - 1) * size
    sql += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params.extend([size, offset])
    
    cursor.execute(sql, params)
    members = cursor.fetchall()
    
    # 전체 개수
    count_sql = "SELECT COUNT(*) as count FROM members WHERE 1=1"
    count_params = []
    
    if search:
        count_sql += " AND (name LIKE %s OR phone LIKE %s)"
        count_params.extend([search_param, search_param])
    
    if status == 'active':
        count_sql += " AND is_active = TRUE AND end_date >= CURDATE()"
    elif status == 'inactive':
        count_sql += " AND is_active = FALSE"
    elif status == 'expiring_soon':
        count_sql += " AND is_active = TRUE AND end_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)"
    
    cursor.execute(count_sql, count_params)
    result = cursor.fetchone()
    total = result['count'] if result else 0
    
    return {
        "members": members,
        "total": total,
        "page": page,
        "size": size,
        "total_pages": (total + size - 1) // size
    }


# === 회원 정보 조회 (단일) ===
@router.get("/members/{member_id}")
async def get_member(
    member_id: int,
    cursor = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """회원 상세 정보 조회"""
    admin_service = AdminService(cursor)
    await admin_service.get_current_admin(token)
    
    return admin_service.get_member(member_id)


# === 회원별 출입 기록 조회 ===
@router.get("/members/{member_id}/checkins")
async def get_member_checkins(
    member_id: int,
    cursor = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    회원별 출입 기록 조회
    
    - **member_id**: 회원 ID
    """
    admin_service = AdminService(cursor)
    await admin_service.get_current_admin(token)
    
    try:
        # ⭐ 단순화된 SQL 쿼리
        sql = """
        SELECT 
            id,
            member_id,
            created_at
        FROM checkins
        WHERE member_id = %s
        ORDER BY created_at DESC
        LIMIT 50
        """
        cursor.execute(sql, (member_id,))
        raw_checkins = cursor.fetchall()
        
        # ⭐ Python에서 date, time, type 필드 추가
        checkins = []
        for record in raw_checkins:
            created_at = record['created_at']
            
            # datetime 객체로 변환
            if isinstance(created_at, str):
                from datetime import datetime
                created_at = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
            
            checkins.append({
                'id': record['id'],
                'member_id': record['member_id'],
                'date': created_at.strftime('%Y-%m-%d'),
                'time': created_at.strftime('%H:%M'),
                'type': '입장',
                'created_at': created_at.isoformat()
            })
        
        return {
            "status": "success",
            "checkins": checkins,
            "total": len(checkins)
        }
        
    except Exception as e:
        import traceback
        print("===== 출입 기록 조회 에러 =====")
        print(f"member_id: {member_id}")
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        print("==============================")
        
        raise HTTPException(
            status_code=500,
            detail=f"출입 기록 조회 실패: {str(e)}"
        )


# === 회원 정보 수정 ===
@router.put("/members/{member_id}")
async def update_member(
    member_id: int,
    update_data: MemberUpdateRequest,
    cursor = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    회원 정보 수정
    
    - **member_id**: 수정할 회원 ID
    - **name**: 이름 (선택)
    - **phone_number**: 전화번호 (선택)
    - **membership_type**: 회원권 종류 (3개월, 6개월, 1년)
    - **membership_start_date**: 시작일 (선택)
    - **membership_end_date**: 종료일 (선택)
    """
    admin_service = AdminService(cursor)
    await admin_service.get_current_admin(token)
    
    start_date_str = update_data.membership_start_date.isoformat() if update_data.membership_start_date else None
    end_date_str = update_data.membership_end_date.isoformat() if update_data.membership_end_date else None
    
    result = admin_service.update_member(
        member_id=member_id,
        name=update_data.name,
        phone_number=update_data.phone_number,
        membership_type=update_data.membership_type,
        membership_start_date=start_date_str,
        membership_end_date=end_date_str
    )
    
    return result


# === 회원 삭제 ===
@router.delete("/members/{member_id}")
async def delete_member(
    member_id: int,
    cursor = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    회원 삭제 (완전 삭제)
    
    - **member_id**: 삭제할 회원 ID
    """
    admin_service = AdminService(cursor)
    await admin_service.get_current_admin(token)
    
    return admin_service.delete_member(member_id)


# === 당일 입장 회원 조회 ===
@router.get("/today-checkins")
async def get_today_checkins(
    cursor = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """당일 입장한 회원 목록 조회"""
    admin_service = AdminService(cursor)
    await admin_service.get_current_admin(token)
    
    return {
        "status": "success",
        "checkins": admin_service.get_today_checkins()
    }


# === 비밀번호 변경 ===
@router.put("/change-password")
async def change_admin_password(
    update_data: AdminUpdate,
    cursor = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Dict:
    admin_service = AdminService(cursor)
    await admin_service.get_current_admin(token)
    
    return admin_service.change_password(
        update_data.current_password,
        update_data.new_password
    )