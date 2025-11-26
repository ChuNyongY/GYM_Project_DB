from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Dict, Optional, Union, Any, List
from pydantic import BaseModel, field_validator
from datetime import date, datetime
import traceback
from enum import Enum

from ..database import get_db
from ..services.admin_service import AdminService
from ..schemas.admin import AdminUpdate
from ..utils.security import oauth2_scheme

router = APIRouter(tags=["admin"])

# === Request Models ===

class GenderEnum(str, Enum):
    M = 'M'
    F = 'F'

class LoginRequest(BaseModel):
    password: str

class MemberCreateRequest(BaseModel):
    name: str
    phone_number: str
    gender: GenderEnum
    membership_type: str
    membership_start_date: date
    membership_end_date: date
    locker_number: Optional[int] = None
    locker_type: Optional[str] = None
    locker_start_date: Optional[Union[date, str]] = None
    locker_end_date: Optional[Union[date, str]] = None
    uniform_type: Optional[str] = None
    uniform_start_date: Optional[Union[date, str]] = None
    uniform_end_date: Optional[Union[date, str]] = None

    @field_validator('membership_type')
    @classmethod
    def validate_membership_type(cls, v):
        allowed = ['1개월', '3개월', '6개월', '1년', 'PT(1개월)', 'PT(3개월)', 'PT(6개월)', 'PT(1년)']
        if v not in allowed:
            raise ValueError(f'회원권 종류는 {", ".join(allowed)} 중 하나여야 합니다.')
        return v

# [422 에러 해결용] 유연한 업데이트 모델
class MemberUpdateRequest(BaseModel):
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
    locker_number: Optional[int] = None
    gender: Optional[str] = None

    @field_validator('membership_type')
    @classmethod
    def validate_membership_type(cls, v):
        if v is not None:
            allowed = ['1개월', '3개월', '6개월', '1년', 'PT(1개월)', 'PT(3개월)', 'PT(6개월)', 'PT(1년)']
            if v not in allowed:
                raise ValueError(f'회원권 종류는 {", ".join(allowed)} 중 하나여야 합니다.')
        return v

    class Config:
        extra = 'ignore'


# === API Endpoints ===

@router.post("/login")
def admin_login(request: LoginRequest, cursor=Depends(get_db)) -> Dict[str, Any]:
    admin_service = AdminService(cursor)
    return admin_service.verify_admin(request.password)

@router.post("/members")
async def create_member(
    member_data: MemberCreateRequest,
    cursor=Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    admin_service = AdminService(cursor)
    await admin_service.get_current_admin(token)

    member_dict: Dict[str, Any] = {
        'name': member_data.name,
        'phone_number': member_data.phone_number,
        'gender': getattr(member_data, 'gender', None),
        'membership_type': member_data.membership_type,
        'membership_start_date': member_data.membership_start_date.isoformat() if isinstance(member_data.membership_start_date, date) else member_data.membership_start_date,
        'membership_end_date': member_data.membership_end_date.isoformat() if isinstance(member_data.membership_end_date, date) else member_data.membership_end_date,
        'locker_number': getattr(member_data, 'locker_number', None),
    }

    if member_data.locker_type is not None:
        member_dict['locker_type'] = member_data.locker_type
        member_dict['locker_start_date'] = member_data.locker_start_date.isoformat() if isinstance(member_data.locker_start_date, date) else member_data.locker_start_date if member_data.locker_start_date else None
        member_dict['locker_end_date'] = member_data.locker_end_date.isoformat() if isinstance(member_data.locker_end_date, date) else member_data.locker_end_date if member_data.locker_end_date else None

    if member_data.uniform_type is not None:
        member_dict['uniform_type'] = member_data.uniform_type
        member_dict['uniform_start_date'] = member_data.uniform_start_date.isoformat() if isinstance(member_data.uniform_start_date, date) else member_data.uniform_start_date if member_data.uniform_start_date else None
        member_dict['uniform_end_date'] = member_data.uniform_end_date.isoformat() if isinstance(member_data.uniform_end_date, date) else member_data.uniform_end_date if member_data.uniform_end_date else None

    return admin_service.create_member(**member_dict)

@router.get("/members")
async def get_members(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    membership_filter: Optional[str] = Query(None),
    locker_filter: bool = Query(False),
    uniform_filter: bool = Query(False),
    checkin_status: Optional[str] = Query(None),
    cursor=Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    admin_service = AdminService(cursor)
    await admin_service.get_current_admin(token)
    return admin_service.get_members(
        page=page, size=size, search=search, status_filter=status, sort_by=sort_by, 
        gender=gender, membership_filter=membership_filter, locker_filter=locker_filter, uniform_filter=uniform_filter,
        checkin_status=checkin_status
    )

@router.get("/members/{member_id}")
async def get_member(
    member_id: int, cursor=Depends(get_db), token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    admin_service = AdminService(cursor)
    await admin_service.get_current_admin(token)
    return admin_service.get_member(member_id)

# ✅ [복구 완료] 출입 기록 조회 기능
# Repository 의존성을 제거하고, 직접 SQL을 사용하여 가장 안전하게 복구했습니다.
@router.get("/members/{member_id}/checkins")
async def get_member_checkins(
    member_id: int,
    cursor=Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """회원별 최근 출입 기록 조회"""
    admin_service = AdminService(cursor)
    await admin_service.get_current_admin(token)

    try:
        # 1. 실제 DB 컬럼(checkin_time)을 사용하는 올바른 SQL
        sql = """
        SELECT 
            id,
            member_id,
            checkin_time,
            checkout_time
        FROM checkins
        WHERE member_id = %s
        ORDER BY checkin_time DESC
        LIMIT 50
        """
        cursor.execute(sql, (member_id,))
        raw_checkins = cursor.fetchall()

        checkins = []
        for record in raw_checkins:
            # 2. 데이터 가져오기 (컬럼명 checkin_time)
            checkin_dt = record.get('checkin_time')
            
            if checkin_dt is None:
                continue

            # 3. 날짜 변환 (datetime 객체인지 문자열인지 확인 후 처리)
            # MySQL 설정에 따라 datetime 객체로 올 수도 있고 문자열로 올 수도 있음
            if isinstance(checkin_dt, str):
                checkin_dt = datetime.strptime(checkin_dt, '%Y-%m-%d %H:%M:%S')

            # 4. 프론트엔드가 원하는 포맷(date, time 키)으로 변환
            checkins.append({
                'id': record['id'],
                'member_id': record['member_id'],
                'date': checkin_dt.strftime('%Y-%m-%d'),  # 예: 2024-11-25
                'time': checkin_dt.strftime('%H:%M'),     # 예: 14:30
                'type': '입장',
                # 프론트엔드 MemberDrawer.tsx에서 new Date(record.date)를 쓰므로 
                # 위 date 필드가 'YYYY-MM-DD' 형식이면 정상 작동합니다.
            })

        return {
            "status": "success",
            "checkins": checkins,
            "total": len(checkins)
        }

    except Exception as e:
        print(f"❌ 출입 기록 조회 실패: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"출입 기록 조회 실패: {str(e)}")


# ✅ [유지] 422 에러 해결된 수정 기능
@router.put("/members/{member_id}")
async def update_member(
    member_id: int,
    update_data: MemberUpdateRequest,
    cursor=Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    admin_service = AdminService(cursor)
    await admin_service.get_current_admin(token)

    # 422 에러 원인이었던 update_raw 제거 및 데이터 정제 로직
    update_dict = update_data.dict(exclude_unset=True)

    for key, value in update_dict.items():
        if isinstance(value, date):
            update_dict[key] = value.isoformat()

    if 'gender' in update_dict and update_dict['gender'] == '':
        update_dict['gender'] = None

    return admin_service.update_member(member_id=member_id, **update_dict)


@router.delete("/members/{member_id}")
async def delete_member(
    member_id: int, cursor=Depends(get_db), token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    admin_service = AdminService(cursor)
    await admin_service.get_current_admin(token)
    return admin_service.delete_member(member_id)

@router.get("/today-checkins")
async def get_today_checkins(
    cursor=Depends(get_db), token: str = Depends(oauth2_scheme)
):
    admin_service = AdminService(cursor)
    await admin_service.get_current_admin(token)
    return {"status": "success", "checkins": admin_service.get_today_checkins()}

@router.put("/change-password")
async def change_admin_password(
    update_data: AdminUpdate, cursor=Depends(get_db), token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    admin_service = AdminService(cursor)
    await admin_service.get_current_admin(token)
    return admin_service.change_password(update_data.current_password, update_data.new_password)