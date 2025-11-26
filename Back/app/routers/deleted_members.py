from fastapi import APIRouter, Depends, Query
from typing import Dict, Optional
from ..database import get_db
from ..services.deleted_member_service import DeletedMemberService
from ..utils.security import oauth2_scheme

router = APIRouter()


@router.get("/", response_model=Dict)
async def list_deleted_members(
    page: int = Query(1),
    size: int = Query(20),
    search: Optional[str] = None,
    db=Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """삭제된 회원 목록 조회"""
    service = DeletedMemberService(db)
    members, total = service.get_deleted_members_list(page, size, search)
    return {"total": total, "page": page, "size": size, "members": members}


@router.post("/{member_id}/restore")
async def restore_member(
    member_id: int,
    db=Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """회원 복원"""
    service = DeletedMemberService(db)
    return service.restore_member(member_id)


@router.post("/restore-all")
async def restore_all_members(
    db=Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """모든 삭제된 회원 복원"""
    service = DeletedMemberService(db)
    return service.restore_all()


@router.delete("/{member_id}")
async def permanent_delete_member(
    member_id: int,
    db=Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """회원 영구 삭제"""
    service = DeletedMemberService(db)
    return service.permanent_delete_member(member_id)


@router.delete("/")
async def permanent_delete_all_members(
    db=Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """모든 삭제된 회원 영구 삭제"""
    service = DeletedMemberService(db)
    return service.permanent_delete_all()
