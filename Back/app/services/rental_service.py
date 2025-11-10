from datetime import date
from typing import Dict, Optional, Any
from fastapi import HTTPException, status
from ..repositories.locker_repository import LockerRepository
from ..repositories.uniform_repository import UniformRepository
from ..repositories.member_repository import MemberRepository
from ..schemas.locker_rental import LockerRentalCreate
from ..schemas.uniform_rental import UniformRentalCreate
from ..utils.validators import validate_rental_type, validate_locker_number, get_rental_months
from ..utils.date_utils import calculate_end_date


class RentalService:
    def __init__(self, db: Any):
        # db is expected to be a cursor (DictCursor)
        self.db = db
        self.locker_repo = LockerRepository()
        self.uniform_repo = UniformRepository()
        self.member_repo = MemberRepository()

    def create_locker_rental(
        self,
        member_id: int,
        locker_data: LockerRentalCreate
    ) -> Dict:
        # 회원 확인
        member = self.member_repo.get_member_by_id(self.db, member_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="회원을 찾을 수 없습니다."
            )

        # 기존 락커 대여 확인
        if self.locker_repo.get_locker_by_member(self.db, member_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 락커를 대여 중입니다."
            )

        # 락커 번호 유효성 검증
        if not validate_locker_number(locker_data.locker_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="잘못된 락커 번호입니다."
            )

        # 락커 사용 가능 여부 확인
        if not self.locker_repo.is_locker_available(self.db, locker_data.locker_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 사용 중인 락커입니다."
            )

        # 대여 기간 유효성 검증
        if not validate_rental_type(locker_data.rental_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="잘못된 대여 기간입니다."
            )

        locker = self.locker_repo.create_locker_rental(
            self.db,
            member_id,
            locker_data,
            date.today()
        )

        return {
            "status": "success",
            "message": "락커가 대여되었습니다.",
            "locker_rental": {
                "locker_number": locker.get('locker_number'),
                "start_date": locker.get('start_date'),
                "end_date": locker.get('end_date')
            }
        }

    def create_uniform_rental(
        self,
        member_id: int,
        uniform_data: UniformRentalCreate
    ) -> Dict:
        # 회원 확인
        member = self.member_repo.get_member_by_id(self.db, member_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="회원을 찾을 수 없습니다."
            )

        # 기존 회원복 대여 확인
        if self.uniform_repo.get_uniform_by_member(self.db, member_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 회원복을 대여 중입니다."
            )

        # 대여 기간 유효성 검증
        if not validate_rental_type(uniform_data.rental_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="잘못된 대여 기간입니다."
            )

        uniform = self.uniform_repo.create_uniform_rental(
            self.db,
            member_id,
            uniform_data,
            date.today()
        )

        return {
            "status": "success",
            "message": "회원복이 대여되었습니다.",
            "uniform_rental": {
                "start_date": uniform.get('start_date'),
                "end_date": uniform.get('end_date')
            }
        }

    def extend_locker_rental(
        self,
        member_id: int,
        rental_type: str
    ) -> Dict:
        # 대여 정보 확인
        locker = self.locker_repo.get_locker_by_member(self.db, member_id)
        if not locker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="대여 중인 락커가 없습니다."
            )

        # 대여 기간 유효성 검증
        if not validate_rental_type(rental_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="잘못된 대여 기간입니다."
            )

        # 연장 처리
        months = get_rental_months(rental_type)
        new_end_date = calculate_end_date(locker.get('end_date'), months)
        updated_locker = self.locker_repo.extend_locker(
            self.db,
            locker.get('locker_id'),
            rental_type,
            new_end_date
        )

        return {
            "status": "success",
            "message": "락커 대여가 연장되었습니다.",
            "locker_number": updated_locker.get('locker_number'),
            "previous_end_date": locker.get('end_date'),
            "new_end_date": updated_locker.get('end_date')
        }

    def extend_uniform_rental(
        self,
        member_id: int,
        rental_type: str
    ) -> Dict:
        # 대여 정보 확인
        uniform = self.uniform_repo.get_uniform_by_member(self.db, member_id)
        if not uniform:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="대여 중인 회원복이 없습니다."
            )

        # 대여 기간 유효성 검증
        if not validate_rental_type(rental_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="잘못된 대여 기간입니다."
            )

        # 연장 처리
        months = get_rental_months(rental_type)
        new_end_date = calculate_end_date(uniform.get('end_date'), months)
        updated_uniform = self.uniform_repo.extend_uniform(
            self.db,
            uniform.get('id'),
            rental_type,
            new_end_date
        )

        return {
            "status": "success",
            "message": "회원복 대여가 연장되었습니다.",
            "previous_end_date": uniform.get('end_date'),
            "new_end_date": updated_uniform.get('end_date')
        }

    def get_available_lockers(self) -> Dict:
        available = self.locker_repo.get_available_lockers(self.db)
        return {
            "available_lockers": available,
            "total_available": len(available),
            "total_lockers": 100
        }