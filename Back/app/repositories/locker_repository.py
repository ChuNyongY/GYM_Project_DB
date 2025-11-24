from typing import List, Optional
from datetime import date
from ..utils.date_utils import calculate_end_date
from ..utils.validators import get_rental_months
from pymysql.cursors import DictCursor

class LockerRepository:
    @staticmethod
    def create_locker_rental(
        cursor: DictCursor,
        member_id: int,
        locker_data,
        start_date: date
    ) -> dict:
        duration_months = get_rental_months(locker_data.rental_type)
        end_date = calculate_end_date(start_date, duration_months)
        sql = """
        INSERT INTO locker_rentals (
            member_id, locker_number, rental_type, start_date, end_date, is_active
        ) VALUES (%s, %s, %s, %s, %s, TRUE)
        """
        cursor.execute(sql, (
            member_id,
            locker_data.locker_number,
            locker_data.rental_type,
            start_date,
            end_date
        ))
        locker_id = cursor.lastrowid
        return LockerRepository.get_locker_by_member(cursor, member_id)

    @staticmethod
    def get_locker_by_member(cursor: DictCursor, member_id: int) -> Optional[dict]:
        sql = "SELECT * FROM locker_rentals WHERE member_id = %s AND is_active = TRUE"
        cursor.execute(sql, (member_id,))
        return cursor.fetchone()

    @staticmethod
    def extend_locker(
        cursor: DictCursor,
        locker_id: int,
        rental_type: str,
        new_end_date: date
    ) -> dict:
        sql = """
        UPDATE locker_rentals SET rental_type = %s, end_date = %s WHERE locker_id = %s
        """
        cursor.execute(sql, (rental_type, new_end_date, locker_id))
        # return updated record
        cursor.execute("SELECT * FROM locker_rentals WHERE locker_id = %s", (locker_id,))
        return cursor.fetchone()

    @staticmethod
    def get_available_lockers(cursor: DictCursor) -> List[int]:
        sql = "SELECT locker_number FROM locker_rentals WHERE is_active = TRUE"
        cursor.execute(sql)
        used = cursor.fetchall()
        used_numbers = {row['locker_number'] for row in used}
        return [i for i in range(1, 101) if i not in used_numbers]

    @staticmethod
    def is_locker_available(cursor: DictCursor, locker_number: int) -> bool:
        sql = "SELECT 1 FROM locker_rentals WHERE locker_number = %s AND is_active = TRUE"
        cursor.execute(sql, (locker_number,))
        return cursor.fetchone() is None

    @staticmethod
    def release_locker(cursor: DictCursor, locker_id: int) -> bool:
        sql = "UPDATE locker_rentals SET is_active = FALSE WHERE locker_id = %s"
        result = cursor.execute(sql, (locker_id,))
        return result > 0