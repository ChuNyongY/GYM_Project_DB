from fastapi import APIRouter, Depends, Query
from typing import Dict, Optional
from ..database import get_db
from ..services.member_service import MemberService
from ..schemas.member import MemberCreate, MemberUpdate, MemberResponse
from ..utils.security import oauth2_scheme

# [수정] prefix 제거
router = APIRouter()

@router.post("/", response_model=MemberResponse)
async def create_member(member_data: MemberCreate, db = Depends(get_db), token: str = Depends(oauth2_scheme)):
    member_service = MemberService(db)
    return member_service.create_member(member_data)

@router.get("/", response_model=Dict)
async def list_members(
    page: int = Query(1), size: int = Query(20), 
    search: Optional[str] = None, status: Optional[str] = None,
    gender: Optional[str] = None, sort_by: Optional[str] = None,
    membership_filter: Optional[str] = None, checkin_status: Optional[str] = None,
    locker_filter: bool = Query(False), uniform_filter: bool = Query(False),
    db = Depends(get_db), token: str = Depends(oauth2_scheme)
):
    member_service = MemberService(db)
    # 500 에러 방지용 파라미터 전달
    members, total = member_service.get_members_list(
        page, size, search, status, gender, sort_by, membership_filter, checkin_status,
        locker_filter, uniform_filter
    )
    return {"total": total, "page": page, "size": size, "members": members}

@router.get("/{member_id}", response_model=MemberResponse)
async def get_member(member_id: int, db = Depends(get_db), token: str = Depends(oauth2_scheme)):
    member_service = MemberService(db)
    return member_service.get_member(member_id)

@router.put("/{member_id}", response_model=MemberResponse)
async def update_member(member_id: int, update_data: MemberUpdate, db = Depends(get_db), token: str = Depends(oauth2_scheme)):
    member_service = MemberService(db)
    return member_service.update_member(member_id, update_data)

@router.post("/{member_id}/extend-membership")
async def extend_membership(member_id: int, membership_type_id: int, db = Depends(get_db), token: str = Depends(oauth2_scheme)):
    member_service = MemberService(db)
    return member_service.extend_membership(member_id, membership_type_id)