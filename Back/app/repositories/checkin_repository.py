from typing import List, Optional, Tuple
from datetime import datetime, date
from pymysql.cursors import DictCursor

class CheckInRepository:
    @staticmethod
    def create_checkin(cursor: DictCursor, member_id: int) -> dict:
        sql = """
        INSERT INTO checkin_logs (member_id, checkin_time)
        VALUES (%s, %s)
        """
        cursor.execute(sql, (member_id, datetime.now()))
        checkin_id = cursor.lastrowid
        return CheckInRepository.get_checkin_by_id(cursor, checkin_id)

    @staticmethod
    def update_checkout(cursor: DictCursor, checkin_id: int) -> dict:
        sql = """
        UPDATE checkin_logs
        SET checkout_time = %s
        WHERE checkin_id = %s
        """
        cursor.execute(sql, (datetime.now(), checkin_id))
        return CheckInRepository.get_checkin_by_id(cursor, checkin_id)

    @staticmethod
    def get_checkin_by_id(cursor: DictCursor, checkin_id: int) -> Optional[dict]:
        sql = "SELECT * FROM checkin_logs WHERE checkin_id = %s"
        cursor.execute(sql, (checkin_id,))
        return cursor.fetchone()

    @staticmethod
    def get_today_checkins(cursor: DictCursor, skip: int = 0, limit: int = 50) -> Tuple[List[dict], int]:
        today = date.today()
        count_sql = "SELECT COUNT(*) as total FROM checkin_logs WHERE DATE(checkin_time) = %s"
        cursor.execute(count_sql, (today,))
        total = cursor.fetchone()['total']

        sql = """
        SELECT * FROM checkin_logs
        WHERE DATE(checkin_time) = %s
        ORDER BY checkin_time DESC
        LIMIT %s OFFSET %s
        """
        cursor.execute(sql, (today, limit, skip))
        checkins = cursor.fetchall()
        return checkins, total

    @staticmethod
    def get_member_checkins(
        cursor: DictCursor,
        member_id: int,
        year: int,
        month: int
    ) -> List[dict]:
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        sql = """
        SELECT * FROM checkin_logs
        WHERE member_id = %s
        AND checkin_time >= %s
        AND checkin_time < %s
        ORDER BY checkin_time DESC
        """
        cursor.execute(sql, (member_id, start_date, end_date))
        return cursor.fetchall()

    @staticmethod
    def count_monthly_checkins(
        cursor: DictCursor,
        member_id: int,
        year: int,
        month: int
    ) -> int:
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        sql = """
        SELECT COUNT(*) as cnt FROM checkin_logs
        WHERE member_id = %s
        AND checkin_time >= %s
        AND checkin_time < %s
        """
        cursor.execute(sql, (member_id, start_date, end_date))
        return cursor.fetchone().get('cnt', 0)

    @staticmethod
    def get_active_checkin(cursor: DictCursor, member_id: int) -> Optional[dict]:
        """현재 입장 중인 기록 조회 (체크아웃하지 않은 기록)"""
        sql = "SELECT * FROM checkin_logs WHERE member_id = %s AND checkout_time IS NULL"
        cursor.execute(sql, (member_id,))
        return cursor.fetchone()