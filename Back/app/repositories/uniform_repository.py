from typing import Optional
from datetime import date
from ..utils.date_utils import calculate_end_date
from ..utils.validators import get_rental_months
from pymysql.cursors import DictCursor

class UniformRepository:
    @staticmethod
    def create_uniform_rental(
        cursor: DictCursor,
        member_id: int,
        uniform_data,
        start_date: date
    ) -> dict:
        duration_months = get_rental_months(uniform_data.rental_type)
        end_date = calculate_end_date(start_date, duration_months)
        sql = """
        INSERT INTO uniform_rentals (
            member_id, rental_type, start_date, end_date, is_active
        ) VALUES (%s, %s, %s, %s, TRUE)
        """
        cursor.execute(sql, (
            member_id,
            uniform_data.rental_type,
            start_date,
            end_date
        ))
        uniform_id = cursor.lastrowid
        cursor.execute("SELECT * FROM uniform_rentals WHERE id = %s", (uniform_id,))
        return cursor.fetchone()

    @staticmethod
    def get_uniform_by_member(cursor: DictCursor, member_id: int) -> Optional[dict]:
        sql = "SELECT * FROM uniform_rentals WHERE member_id = %s AND is_active = TRUE"
        cursor.execute(sql, (member_id,))
        return cursor.fetchone()

    @staticmethod
    def extend_uniform(cursor: DictCursor, uniform_id: int, rental_type: str, new_end_date: date) -> dict:
        sql = "UPDATE uniform_rentals SET rental_type = %s, end_date = %s WHERE id = %s"
        cursor.execute(sql, (rental_type, new_end_date, uniform_id))
        cursor.execute("SELECT * FROM uniform_rentals WHERE id = %s", (uniform_id,))
        return cursor.fetchone()

    @staticmethod
    def release_uniform(cursor: DictCursor, uniform_id: int) -> bool:
        sql = "UPDATE uniform_rentals SET is_active = FALSE WHERE id = %s"
        result = cursor.execute(sql, (uniform_id,))
        return result > 0