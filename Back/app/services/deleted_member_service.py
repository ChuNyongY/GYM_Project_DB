from typing import List, Tuple, Optional, Any
from fastapi import HTTPException, status

from ..repositories.deleted_member_repository import DeletedMemberRepository


class DeletedMemberService:
    """삭제된 회원 관리 Service"""
    
    def __init__(self, db: Any):
        self.db = db
        self.deleted_member_repo = DeletedMemberRepository()
    
    def get_deleted_members_list(
        self,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None
    ) -> Tuple[List[dict], int]:
        """삭제된 회원 목록 조회"""
        skip = (page - 1) * size
        return self.deleted_member_repo.get_deleted_members_paginated(
            self.db,
            skip=skip,
            limit=size,
            search=search
        )
    
    def restore_member(self, member_id: int) -> dict:
        """회원 복원"""
        success = self.deleted_member_repo.restore_member(self.db, member_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="삭제된 회원을 찾을 수 없습니다."
            )
        return {"status": "success", "message": "회원이 복원되었습니다."}
    
    def permanent_delete_member(self, member_id: int) -> dict:
        """회원 영구 삭제"""
        success = self.deleted_member_repo.permanent_delete_member(self.db, member_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="삭제된 회원을 찾을 수 없습니다."
            )
        return {"status": "success", "message": "회원이 영구 삭제되었습니다."}
    
    def permanent_delete_all(self) -> dict:
        """모든 삭제된 회원 영구 삭제"""
        count = self.deleted_member_repo.permanent_delete_all(self.db)
        return {"status": "success", "message": f"{count}명의 회원이 영구 삭제되었습니다.", "count": count}
    
    def restore_all(self) -> dict:
        """모든 삭제된 회원 복원"""
        count = self.deleted_member_repo.restore_all(self.db)
        return {"status": "success", "message": f"{count}명의 회원이 복원되었습니다.", "count": count}
