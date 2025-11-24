import re
from typing import Optional

def validate_phone_number(phone: str) -> bool:
    """
    전화번호 형식 검증 (01012345678 형식)
    """
    if not phone:
        return False
    return bool(re.match(r"^01[0-9]{9}$", phone))

def validate_last_four_digits(digits: str) -> bool:
    """
    전화번호 뒤 4자리 검증
    """
    if not digits:
        return False
    return bool(re.match(r"^\d{4}$", digits))

def validate_locker_number(locker_num: int) -> bool:
    """
    락커 번호 범위 검증 (1-100)
    """
    return 1 <= locker_num <= 100

def validate_rental_type(rental_type: str) -> bool:
    """
    대여 기간 유효성 검증
    """
    valid_types = ["1개월", "3개월", "6개월", "1년"]
    return rental_type in valid_types

def get_rental_months(rental_type: str) -> Optional[int]:
    """
    대여 기간 문자열을 개월 수로 변환
    """
    rental_months = {
        "1개월": 1,
        "3개월": 3,
        "6개월": 6,
        "1년": 12
    }
    return rental_months.get(rental_type)