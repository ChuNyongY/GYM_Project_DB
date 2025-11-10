from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Optional, Any
from ..database import get_db
from ..services.member_service import MemberService
from ..services.rental_service import RentalService
from ..schemas.member import MemberCreate, MemberUpdate, MemberResponse
from ..schemas.locker_rental import LockerRentalCreate
from ..schemas.uniform_rental import UniformRentalCreate
from ..utils.security import oauth2_scheme

router = APIRouter(prefix="/api/members", tags=["members"])

@router.post("/", response_model=MemberResponse)
async def create_member(
    member_data: MemberCreate,
    db = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> MemberResponse:
    member_service = MemberService(db)
    return member_service.create_member(member_data)

@router.get("/", response_model=Dict)
async def list_members(
    page: int = Query(1, gt=0),
    size: int = Query(20, gt=0),
    search: Optional[str] = None,
    status: Optional[str] = None,
    db = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Dict:
    member_service = MemberService(db)
    members, total = member_service.get_members_list(page, size, search, status)
    
    return {
        "total": total,
        "page": page,
        "size": size,
        "members": members
    }

@router.get("/{member_id}", response_model=MemberResponse)
async def get_member(
    member_id: int,
    db = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> MemberResponse:
    member_service = MemberService(db)
    return member_service.get_member(member_id)

@router.put("/{member_id}", response_model=MemberResponse)
async def update_member(
    member_id: int,
    update_data: MemberUpdate,
    db = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> MemberResponse:
    member_service = MemberService(db)
    return member_service.update_member(member_id, update_data)

@router.post("/{member_id}/extend-membership")
async def extend_membership(
    member_id: int,
    membership_type_id: int,
    db = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Dict:
    member_service = MemberService(db)
    return member_service.extend_membership(member_id, membership_type_id)