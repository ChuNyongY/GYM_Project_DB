from datetime import timedelta
from typing import Dict, Optional, Any, List
from fastapi import HTTPException, status, Depends
from jose import JWTError
from ..repositories.admin_repository import AdminRepository
from ..repositories.member_repository import MemberRepository
from ..utils.security import create_access_token, verify_token, oauth2_scheme
from ..config import get_settings

settings = get_settings()


class AdminService:
    def __init__(self, db: Any):
        self.db = db
        self.admin_repo = AdminRepository()
        self.member_repo = MemberRepository()

    def verify_admin(self, password: str) -> Dict:
        if not self.admin_repo.verify_password(self.db, password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="비밀번호가 일치하지 않습니다."
            )

        access_token = create_access_token(
            data={"sub": "admin", "role": "admin"},
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

    # ==================== 회원 관리 메서드 ====================

    def get_members(
        self, 
        page: int = 1, 
        size: int = 20, 
        search: Optional[str] = None,
        status_filter: str = 'all'
    ) -> Dict:
        """회원 목록 조회 (페이징, 검색, 필터)"""
        try:
            offset = (page - 1) * size
            
            members, total = self.member_repo.get_members_paginated(
                self.db,
                skip=offset,
                limit=size,
                search=search,
                status=status_filter if status_filter != 'all' else None
            )
            
            return {
                "members": members,
                "total": total,
                "page": page,
                "size": size
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"회원 목록 조회 실패: {str(e)}"
            )

    def get_member(self, member_id: int) -> Dict:
        """회원 정보 조회"""
        member = self.member_repo.get_member_by_id(self.db, member_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="회원을 찾을 수 없습니다."
            )
        return member

    def create_member(
        self,
        name: str,
        phone_number: str,
        membership_type: str,
        membership_start_date: str,
        membership_end_date: str,
        locker_type: Optional[str] = None,
        locker_start_date: Optional[str] = None,
        locker_end_date: Optional[str] = None,
        uniform_type: Optional[str] = None,
        uniform_start_date: Optional[str] = None,
        uniform_end_date: Optional[str] = None
    ) -> Dict:
        """회원 추가"""
        existing = self.member_repo.get_member_by_phone(self.db, phone_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 전화번호입니다."
            )

        if membership_type not in ['1개월', '3개월', '6개월', '1년']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="회원권 종류는 1개월, 3개월, 6개월, 1년 중 하나여야 합니다."
            )

        try:
            # ⭐ SQL 수정 - 락커/회원복 컬럼 포함
            sql = """
            INSERT INTO members (
                name, phone, membership_type, start_date, end_date,
                locker_type, locker_start_date, locker_end_date,
                uniform_type, uniform_start_date, uniform_end_date,
                is_active, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, NOW())
            """
            self.db.execute(sql, (
                name,
                phone_number,
                membership_type,
                membership_start_date,
                membership_end_date,
                locker_type,  # ⭐ 추가
                locker_start_date,  # ⭐ 추가
                locker_end_date,  # ⭐ 추가
                uniform_type,  # ⭐ 추가
                uniform_start_date,  # ⭐ 추가
                uniform_end_date  # ⭐ 추가
            ))
            self.db.connection.commit()
            
            member_id = self.db.lastrowid
            new_member = self.member_repo.get_member_by_id(self.db, member_id)
            
            return {
                "status": "success",
                "message": "회원이 추가되었습니다.",
                "member": new_member
            }
        except Exception as e:
            self.db.connection.rollback()
            print(f"❌ 회원 추가 실패: {str(e)}")  # ⭐ 디버깅
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"회원 추가 실패: {str(e)}"
            )

    def update_member(
        self, 
        member_id: int, 
        name: Optional[str] = None,
        phone_number: Optional[str] = None,
        membership_type: Optional[str] = None,
        membership_start_date: Optional[str] = None,
        membership_end_date: Optional[str] = None,
        locker_type: Optional[str] = None,
        locker_start_date: Optional[str] = None,
        locker_end_date: Optional[str] = None,
        uniform_type: Optional[str] = None,
        uniform_start_date: Optional[str] = None,
        uniform_end_date: Optional[str] = None
    ) -> Dict:
        """회원 정보 수정"""
        member = self.member_repo.get_member_by_id(self.db, member_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="회원을 찾을 수 없습니다."
            )

        if phone_number and phone_number != member.get('phone_number'):
            existing = self.member_repo.get_member_by_phone(self.db, phone_number)
            if existing and existing.get('member_id') != member_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 사용 중인 전화번호입니다."
                )

        if membership_type and membership_type not in ['1개월', '3개월', '6개월', '1년']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="회원권 종류는 1개월, 3개월, 6개월, 1년 중 하나여야 합니다."
            )

        # UPDATE SQL 구성
        update_fields = []
        update_values = []
        
        if name is not None:
            update_fields.append("name = %s")
            update_values.append(name)
        if phone_number is not None:
            update_fields.append("phone = %s")
            update_values.append(phone_number)
        if membership_type is not None:
            update_fields.append("membership_type = %s")
            update_values.append(membership_type)
        if membership_start_date is not None:
            update_fields.append("start_date = %s")
            update_values.append(membership_start_date)
        if membership_end_date is not None:
            update_fields.append("end_date = %s")
            update_values.append(membership_end_date)
        
        # ⭐ 락커 정보 - None도 업데이트 (선택 해제 처리)
        # locker_type이 키에 있으면 (None이어도) 업데이트
        import inspect
        frame = inspect.currentframe()
        args_info = inspect.getargvalues(frame)
        
        # 간단한 방법: kwargs 사용
        # locker_type이 전달되었는지 확인 (None이어도 업데이트)
        update_fields.append("locker_type = %s")
        update_values.append(locker_type)
        update_fields.append("locker_start_date = %s")
        update_values.append(locker_start_date)
        update_fields.append("locker_end_date = %s")
        update_values.append(locker_end_date)
        
        # ⭐ 회원복 정보 - None도 업데이트 (선택 해제 처리)
        update_fields.append("uniform_type = %s")
        update_values.append(uniform_type)
        update_fields.append("uniform_start_date = %s")
        update_values.append(uniform_start_date)
        update_fields.append("uniform_end_date = %s")
        update_values.append(uniform_end_date)

        if not update_fields:
            return {
                "status": "success",
                "message": "변경사항이 없습니다.",
                "member": member
            }

        try:
            sql = f"UPDATE members SET {', '.join(update_fields)} WHERE id = %s"
            update_values.append(member_id)
            
            print(f"🔧 UPDATE SQL: {sql}")
            print(f"🔧 VALUES: {update_values}")
            
            self.db.execute(sql, tuple(update_values))
            self.db.connection.commit()
            
            updated_member = self.member_repo.get_member_by_id(self.db, member_id)
            return {
                "status": "success",
                "message": "회원 정보가 수정되었습니다.",
                "member": updated_member
            }
        except Exception as e:
            self.db.connection.rollback()
            print(f"❌ 회원 수정 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"회원 정보 수정 실패: {str(e)}"
            )

    def delete_member(self, member_id: int) -> Dict:
        """
        회원 완전 삭제 (하드 삭제)
        """
        try:
            # 1. 먼저 회원이 존재하는지 간단히 확인
            check_sql = "SELECT id, name FROM members WHERE id = %s"
            self.db.execute(check_sql, (member_id,))
            member = self.db.fetchone()
        
            if not member:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="회원을 찾을 수 없습니다."
                )
        
            member_name = member.get('name', '알 수 없는 회원')
        
            # 2. 출입 기록이 있다면 먼저 삭제 (외래 키 오류 방지)
            try:
                delete_checkins_sql = "DELETE FROM checkins WHERE member_id = %s"
                self.db.execute(delete_checkins_sql, (member_id,))
            except Exception:
                # checkins 테이블이 없거나 오류가 나도 계속 진행
                pass
        
            # 3. 회원 삭제
            delete_member_sql = "DELETE FROM members WHERE id = %s"
            self.db.execute(delete_member_sql, (member_id,))
        
            # 4. 커밋
            self.db.connection.commit()
        
            return {
                "status": "success",
                "message": f"{member_name} 회원이 삭제되었습니다.",
                "member_id": member_id
            }
        
        except HTTPException:
            # HTTPException은 그대로 다시 발생
            raise
        except Exception as e:
            # 다른 오류가 발생하면 롤백
            self.db.connection.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"회원 삭제 실패: {str(e)}"
            )

    def get_today_checkins(self) -> List[Dict]:
        """당일 입장 회원 목록"""
        try:
            checkins = self.member_repo.get_today_checkins(self.db)
            return checkins
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"당일 입장 회원 조회 실패: {str(e)}"
            )