from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Dict, Optional, Union
from pydantic import BaseModel, field_validator
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
    locker_type: Optional[str] = None
    locker_start_date: Optional[Union[date, str]] = None
    locker_end_date: Optional[Union[date, str]] = None
    uniform_type: Optional[str] = None
    uniform_start_date: Optional[Union[date, str]] = None
    uniform_end_date: Optional[Union[date, str]] = None

    @field_validator('membership_type')
    @classmethod
    def validate_membership_type(cls, v):
        allowed = ['1개월', '3개월', '6개월', '1년']
        if v not in allowed:
            raise ValueError(f'회원권 종류는 {", ".join(allowed)} 중 하나여야 합니다.')
        return v

class MemberUpdateRequest(BaseModel):
    """회원 정보 수정 요청"""
    name: Optional[str] = None
    phone_number: Optional[str] = None
    membership_type: Optional[str] = None
    membership_start_date: Optional[Union[date, str]] = None
    membership_end_date: Optional[Union[date, str]] = None
    locker_type: Optional[str] = None
    locker_start_date: Optional[Union[date, str]] = None
    locker_end_date: Optional[Union[date, str]] = None
    uniform_type: Optional[str] = None
    uniform_start_date: Optional[Union[date, str]] = None
    uniform_end_date: Optional[Union[date, str]] = None

    @field_validator('membership_type')
    @classmethod
    def validate_membership_type(cls, v):
        if v is not None:
            allowed = ['1개월', '3개월', '6개월', '1년']
            if v not in allowed:
                raise ValueError(f'회원권 종류는 {", ".join(allowed)} 중 하나여야 합니다.')
        return v

    class Config:
        # ⭐ 추가 필드 허용
        extra = 'ignore'


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
    """새 회원 추가"""
    admin_service = AdminService(cursor)
    await admin_service.get_current_admin(token)
    
    # 기본 데이터
    member_dict = {
        'name': member_data.name,
        'phone_number': member_data.phone_number,
        'membership_type': member_data.membership_type,
        'membership_start_date': member_data.membership_start_date.isoformat() if isinstance(member_data.membership_start_date, date) else member_data.membership_start_date,
        'membership_end_date': member_data.membership_end_date.isoformat() if isinstance(member_data.membership_end_date, date) else member_data.membership_end_date
    }
    
    # 락커 정보
    if member_data.locker_type:
        member_dict['locker_type'] = member_data.locker_type
        if member_data.locker_start_date:
            member_dict['locker_start_date'] = member_data.locker_start_date.isoformat() if isinstance(member_data.locker_start_date, date) else member_data.locker_start_date
        if member_data.locker_end_date:
            member_dict['locker_end_date'] = member_data.locker_end_date.isoformat() if isinstance(member_data.locker_end_date, date) else member_data.locker_end_date
    
    # 회원복 정보
    if member_data.uniform_type:
        member_dict['uniform_type'] = member_data.uniform_type
        if member_data.uniform_start_date:
            member_dict['uniform_start_date'] = member_data.uniform_start_date.isoformat() if isinstance(member_data.uniform_start_date, date) else member_data.uniform_start_date
        if member_data.uniform_end_date:
            member_dict['uniform_end_date'] = member_data.uniform_end_date.isoformat() if isinstance(member_data.uniform_end_date, date) else member_data.uniform_end_date
    
    return admin_service.create_member(**member_dict)


# === 회원 목록 조회 ===
@router.get("/members")
async def get_members(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    cursor = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """회원 목록 조회"""
    admin_service = AdminService(cursor)
    await admin_service.get_current_admin(token)
    
    # 기본 쿼리
    sql = """
        SELECT 
            m.id as member_id,
            m.name,
            m.phone as phone_number,
            m.start_date as membership_start_date,
            m.end_date as membership_end_date,
            m.membership_type,
            m.locker_type,
            m.locker_start_date,
            m.locker_end_date,
            m.uniform_type,
            m.uniform_start_date,
            m.uniform_end_date,
            m.is_active,
            m.created_at,
            RANK() OVER (ORDER BY m.id ASC) AS member_rank
    """
    
    if sort_by == 'recent_checkin':
        sql += """
            , MAX(c.created_at) as last_checkin
        FROM members m
        LEFT JOIN checkins c ON m.id = c.member_id
        """
    else:
        sql += " FROM members m "
    
    sql += " WHERE 1=1"
    params = []
    
    # 검색 조건
    if search:
        sql += " AND (m.name LIKE %s OR m.phone LIKE %s)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param])
    
    # 상태 필터
    if status == 'active':
        sql += " AND m.is_active = TRUE AND m.end_date >= CURDATE()"
    elif status == 'inactive':
        sql += " AND m.is_active = FALSE"
    elif status == 'expiring_soon':
        sql += """ AND m.is_active = TRUE AND (
            m.end_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 4 DAY)
            OR m.locker_end_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 4 DAY)
            OR m.uniform_end_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 4 DAY)
        )"""
    
    if sort_by == 'recent_checkin':
        sql += " GROUP BY m.id, m.name, m.phone, m.start_date, m.end_date, m.membership_type, m.locker_type, m.locker_start_date, m.locker_end_date, m.uniform_type, m.uniform_start_date, m.uniform_end_date, m.is_active, m.created_at"
    
    # 정렬 조건
    if sort_by == 'recent_checkin':
        sql += " ORDER BY last_checkin DESC, m.created_at DESC"
    elif sort_by == '-member_id':
        sql += " ORDER BY m.id DESC"
    else:
        # 기본값 (최근 가입순)
        sql += " ORDER BY m.created_at DESC"
    
    # 페이지네이션
    offset = (page - 1) * size
    sql += " LIMIT %s OFFSET %s"
    params.extend([size, offset])
    
    cursor.execute(sql, params)
    members = cursor.fetchall()
    
    # 전체 개수
    count_sql = "SELECT COUNT(*) as count FROM members m WHERE 1=1"
    count_params = []
    
    if search:
        count_sql += " AND (m.name LIKE %s OR m.phone LIKE %s)"
        count_params.extend([search_param, search_param])
    
    if status == 'active':
        count_sql += " AND m.is_active = TRUE AND m.end_date >= CURDATE()"
    elif status == 'inactive':
        count_sql += " AND m.is_active = FALSE"
    elif status == 'expiring_soon':
        count_sql += """ AND m.is_active = TRUE AND (
            m.end_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 4 DAY)
            OR m.locker_end_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 4 DAY)
            OR m.uniform_end_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 4 DAY)
        )"""
    
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
    """회원별 출입 기록 조회"""
    admin_service = AdminService(cursor)
    await admin_service.get_current_admin(token)
    
    try:
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
        
        checkins = []
        for record in raw_checkins:
            created_at = record['created_at']
            
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
    """회원 정보 수정"""
    admin_service = AdminService(cursor)
    await admin_service.get_current_admin(token)
    
    # ⭐ 업데이트 데이터 구성
    update_dict = {}
    
    if update_data.name is not None:
        update_dict['name'] = update_data.name
    if update_data.phone_number is not None:
        update_dict['phone_number'] = update_data.phone_number
    if update_data.membership_type is not None:
        update_dict['membership_type'] = update_data.membership_type
    if update_data.membership_start_date is not None:
        update_dict['membership_start_date'] = update_data.membership_start_date.isoformat() if isinstance(update_data.membership_start_date, date) else update_data.membership_start_date
    if update_data.membership_end_date is not None:
        update_dict['membership_end_date'] = update_data.membership_end_date.isoformat() if isinstance(update_data.membership_end_date, date) else update_data.membership_end_date
    
    # 락커 정보
    if update_data.locker_type is not None:
        update_dict['locker_type'] = update_data.locker_type
    if update_data.locker_start_date is not None:
        update_dict['locker_start_date'] = update_data.locker_start_date.isoformat() if isinstance(update_data.locker_start_date, date) else update_data.locker_start_date
    if update_data.locker_end_date is not None:
        update_dict['locker_end_date'] = update_data.locker_end_date.isoformat() if isinstance(update_data.locker_end_date, date) else update_data.locker_end_date
    
    # 회원복 정보
    if update_data.uniform_type is not None:
        update_dict['uniform_type'] = update_data.uniform_type
    if update_data.uniform_start_date is not None:
        update_dict['uniform_start_date'] = update_data.uniform_start_date.isoformat() if isinstance(update_data.uniform_start_date, date) else update_data.uniform_start_date
    if update_data.uniform_end_date is not None:
        update_dict['uniform_end_date'] = update_data.uniform_end_date.isoformat() if isinstance(update_data.uniform_end_date, date) else update_data.uniform_end_date
    
    result = admin_service.update_member(member_id=member_id, **update_dict)
    
    return result


# === 회원 삭제 ===
@router.delete("/members/{member_id}")
async def delete_member(
    member_id: int,
    cursor = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """회원 삭제"""
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