from typing import List, Optional, Tuple
from datetime import datetime, date
from pymysql.cursors import DictCursor

class CheckinRepository:
    
    @staticmethod
    def create_checkin(cursor: DictCursor, member_id: int) -> dict:
        """입장 기록 생성 (checkins 테이블 사용)"""
        # checkins 테이블은 id(PK), member_id(FK) 구조임 (사진 확인됨)
        sql = """
        INSERT INTO checkins (member_id, checkin_time)
        VALUES (%s, NOW())
        """
        cursor.execute(sql, (member_id,))
        checkin_id = cursor.lastrowid
        cursor.connection.commit()
        
        return CheckinRepository.get_checkin_by_id(cursor, checkin_id)

    @staticmethod
    def update_checkout(cursor: DictCursor, checkin_id: int) -> dict:
        """퇴장 시간 업데이트"""
        sql = """
        UPDATE checkins
        SET checkout_time = NOW()
        WHERE id = %s
        """
        cursor.execute(sql, (checkin_id,))
        cursor.connection.commit()
        
        return CheckinRepository.get_checkin_by_id(cursor, checkin_id)

    @staticmethod
    def get_checkin_by_id(cursor: DictCursor, checkin_id: int) -> Optional[dict]:
        """ID로 기록 조회"""
        sql = "SELECT * FROM checkins WHERE id = %s"
        cursor.execute(sql, (checkin_id,))
        return cursor.fetchone()

    @staticmethod
    def get_member_by_phone_tail(cursor: DictCursor, phone_tail: str) -> Optional[dict]:
        """
        [중요 수정] 키오스크 검색용
        members 테이블에서 조회하므로 'id'가 아니라 'member_id'를 써야 합니다.
        """
        sql = """
        SELECT * FROM members 
        WHERE phone_number LIKE %s AND is_active = TRUE
        ORDER BY created_at DESC 
        LIMIT 1
        """
        cursor.execute(sql, (f"%{phone_tail}",))
        return cursor.fetchone()

    @staticmethod
    def get_active_checkin(cursor: DictCursor, member_id: int) -> Optional[dict]:
        """현재 입장 중인 기록 조회"""
        # checkins 테이블은 id 컬럼을 가짐
        sql = """
        SELECT * FROM checkins 
        WHERE member_id = %s AND checkout_time IS NULL
        ORDER BY checkin_time DESC 
        LIMIT 1
        """
        cursor.execute(sql, (member_id,))
        return cursor.fetchone()

    @staticmethod
    def get_today_checkins(cursor: DictCursor, skip: int = 0, limit: int = 50) -> Tuple[List[dict], int]:
        """오늘 출입 기록 조회"""
        today = date.today()
        
        count_sql = "SELECT COUNT(*) as total FROM checkins WHERE DATE(checkin_time) = %s"
        cursor.execute(count_sql, (today,))
        total_res = cursor.fetchone()
        total = total_res['total'] if total_res else 0

        # [수정] 조인 시 m.id가 아니라 m.member_id 사용!
        sql = """
        SELECT 
            c.id as checkin_id,
            c.member_id,
            c.checkin_time,
            c.checkout_time,
            m.name,
            m.phone_number
        FROM checkins c
        LEFT JOIN members m ON c.member_id = m.member_id
        WHERE DATE(c.checkin_time) = %s
        ORDER BY c.checkin_time DESC
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
        """회원별 월간 기록"""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        sql = """
        SELECT * FROM checkins
        WHERE member_id = %s
        AND checkin_time >= %s
        AND checkin_time < %s
        ORDER BY checkin_time DESC
        """
        cursor.execute(sql, (member_id, start_date, end_date))
        return cursor.fetchall()