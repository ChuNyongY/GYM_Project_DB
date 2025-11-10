from datetime import timedelta
from typing import Dict, Optional, Any
from fastapi import HTTPException, status, Depends
from jose import JWTError
from ..repositories.admin_repository import AdminRepository
from ..utils.security import create_access_token, verify_token, oauth2_scheme
from ..config import get_settings

settings = get_settings()


class AdminService:
    def __init__(self, db: Any):
        # db is expected to be a cursor (DictCursor)
        self.db = db
        self.admin_repo = AdminRepository()

    def verify_admin(self, password: str) -> Dict:
        if not self.admin_repo.verify_password(self.db, password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="비밀번호가 일치하지 않습니다."
            )

        access_token = create_access_token(
            data={"sub": "admin"},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return {
            "status": "success",
            "token": access_token,
            "message": "인증 성공"
        }

    def change_password(self, current_password: str, new_password: str) -> Dict:
        admin = self.admin_repo.get_admin(self.db)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="관리자 계정이 존재하지 않습니다."
            )

        if not self.admin_repo.verify_password(self.db, current_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="현재 비밀번호가 일치하지 않습니다."
            )

        self.admin_repo.update_password(self.db, admin.get('id'), new_password)

        return {
            "status": "success",
            "message": "비밀번호가 변경되었습니다."
        }

    async def get_current_admin(self, token: str = Depends(oauth2_scheme)) -> Dict:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = verify_token(token)
            if payload.get("sub") != "admin":
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        admin = self.admin_repo.get_admin(self.db)
        if not admin:
            raise credentials_exception

        return {"admin_id": admin.get('id')}