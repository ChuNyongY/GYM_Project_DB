from typing import List, Optional, Tuple, Dict, Any
from ..schemas.member import MemberCreate, MemberUpdate
from ..utils.date_utils import calculate_end_date
from pymysql.cursors import DictCursor


class MemberRepository:
    @staticmethod
    def create_member(cursor: DictCursor, member_data: MemberCreate) -> dict:
        end_date = calculate_end_date(
            member_data.membership_start_date,
            member_data.membership_type.duration_months
        )
        sql = """
        INSERT INTO members (
            name, phone, membership_type,
            start_date, end_date
        ) VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            member_data.name,
            member_data.phone_number,
            member_data.membership_type,
            member_data.membership_start_date,
            end_date
        ))
        member_id = cursor.lastrowid
        return MemberRepository.get_member_by_id(cursor, member_id)

    @staticmethod
    def get_member_by_id(cursor: DictCursor, member_id: int) -> Optional[dict]:
        """회원 ID로 조회 ⭐ 컬럼명 수정"""
        sql = """
        SELECT 
            id as member_id,
            name,
            phone as phone_number,
            membership_type,
            start_date as membership_start_date,
            end_date as membership_end_date,
            is_active,
            created_at
        FROM members
        WHERE id = %s AND is_active = TRUE
        """
        cursor.execute(sql, (member_id,))
        return cursor.fetchone()

    @staticmethod
    def get_member_by_phone(cursor: DictCursor, phone_number: str) -> Optional[dict]:
        """전화번호로 조회 ⭐ 컬럼명 수정"""
        sql = """
        SELECT 
            id as member_id,
            name,
            phone as phone_number,
            membership_type,
            start_date as membership_start_date,
            end_date as membership_end_date,
            is_active,
            created_at
        FROM members
        WHERE phone = %s AND is_active = TRUE
        """
        cursor.execute(sql, (phone_number,))
        return cursor.fetchone()

    @staticmethod
    def search_by_last_four_digits(cursor: DictCursor, last_four: str) -> List[dict]:
        """휴대폰 끝 4자리로 검색 ⭐ 컬럼명 수정"""
        sql = """
        SELECT 
            id as member_id,
            name,
            phone as phone_number,
            membership_type,
            start_date as membership_start_date,
            end_date as membership_end_date,
            is_active
        FROM members
        WHERE RIGHT(phone, 4) = %s 
        AND is_active = TRUE
        ORDER BY name ASC
        """
        cursor.execute(sql, (last_four,))
        return cursor.fetchall()

    @staticmethod
    def update_member(cursor: DictCursor, member_id: int, update_data: Dict[str, Any]) -> dict:
        """
        회원 정보 수정 (딕셔너리 방식) ⭐ 컬럼명 매핑
        """
        if not update_data:
            return MemberRepository.get_member_by_id(cursor, member_id)
        
        # 컬럼명 매핑 (API → DB)
        column_mapping = {
            'phone_number': 'phone',
            'membership_start_date': 'start_date',
            'membership_end_date': 'end_date'
        }
        
        # 매핑된 컬럼명으로 변경
        mapped_data = {}
        for key, value in update_data.items():
            db_column = column_mapping.get(key, key)
            mapped_data[db_column] = value
        
        update_fields = []
        values = []
        
        for key, value in mapped_data.items():
            if value is not None:
                update_fields.append(f"{key} = %s")
                values.append(value)
        
        if not update_fields:
            return MemberRepository.get_member_by_id(cursor, member_id)
        
        sql = f"""
        UPDATE members 
        SET {', '.join(update_fields)}
        WHERE id = %s AND is_active = TRUE
        """
        values.append(member_id)
        
        try:
            cursor.execute(sql, tuple(values))
            cursor.connection.commit()
        except Exception as e:
            cursor.connection.rollback()
            raise e
        
        return MemberRepository.get_member_by_id(cursor, member_id)

    @staticmethod
    def update_member_pydantic(cursor: DictCursor, member_id: int, update_data: MemberUpdate) -> dict:
        """
        회원 정보 수정 (Pydantic 모델 방식)
        """
        # 컬럼명 매핑
        column_mapping = {
            'phone_number': 'phone',
            'membership_start_date': 'start_date',
            'membership_end_date': 'end_date'
        }
        
        update_fields = []
        values = []
        
        for key, value in update_data.dict(exclude_unset=True).items():
            if value is not None:
                db_column = column_mapping.get(key, key)
                update_fields.append(f"{db_column} = %s")
                values.append(value)
        
        if not update_fields:
            return MemberRepository.get_member_by_id(cursor, member_id)
        
        sql = f"""
        UPDATE members 
        SET {', '.join(update_fields)}
        WHERE id = %s AND is_active = TRUE
        """
        values.append(member_id)
        
        try:
            cursor.execute(sql, tuple(values))
            cursor.connection.commit()
        except Exception as e:
            cursor.connection.rollback()
            raise e
        
        return MemberRepository.get_member_by_id(cursor, member_id)

    @staticmethod
    def soft_delete_member(cursor: DictCursor, member_id: int) -> bool:
        """회원 비활성화 (소프트 삭제) ⭐ 컬럼명 수정"""
        sql = "UPDATE members SET is_active = FALSE WHERE id = %s"
        
        try:
            result = cursor.execute(sql, (member_id,))
            cursor.connection.commit()
            return result > 0
        except Exception as e:
            cursor.connection.rollback()
            raise e

    @staticmethod
    def get_members_paginated(
        cursor: DictCursor,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> Tuple[List[dict], int]:
        """회원 목록 조회 ⭐ 컬럼명 수정"""
        conditions = []
        params = []

        # 검색 조건
        if search:
            conditions.append("(name LIKE %s OR phone LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])

        # 상태 필터
        if status == "active":
            conditions.append("is_active = TRUE")
            conditions.append("(end_date IS NULL OR end_date >= CURDATE())")
        elif status == "inactive":
            conditions.append("(is_active = FALSE OR (end_date IS NOT NULL AND end_date < CURDATE()))")
        elif status == "expiring_soon":
            conditions.extend([
                "is_active = TRUE",
                "end_date IS NOT NULL",
                "end_date >= CURDATE()",
                "end_date <= DATE_ADD(CURDATE(), INTERVAL 7 DAY)"
            ])

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # 전체 개수 조회
        count_sql = f"""
        SELECT COUNT(*) as total 
        FROM members
        WHERE {where_clause}
        """
        cursor.execute(count_sql, tuple(params))
        result = cursor.fetchone()
        total = result['total'] if result else 0

        # 회원 목록 조회
        sql = f"""
        SELECT 
            id as member_id,
            name,
            phone as phone_number,
            membership_type,
            start_date as membership_start_date,
            end_date as membership_end_date,
            is_active,
            created_at,
            CASE 
                WHEN end_date IS NULL THEN NULL
                WHEN end_date < CURDATE() THEN '만료'
                WHEN end_date <= DATE_ADD(CURDATE(), INTERVAL 7 DAY) THEN '곧 만료'
                ELSE '활성'
            END as status_text
        FROM members
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        cursor.execute(sql, tuple(params + [limit, skip]))
        members = cursor.fetchall()

        return members, total

    @staticmethod
    def get_today_checkins(cursor: DictCursor) -> List[dict]:
        """당일 입장 회원 목록 ⭐ 컬럼명 수정"""
        sql = """
        SELECT 
            cl.id as checkin_id,
            cl.member_id,
            cl.checkin_time,
            cl.checkout_time,
            m.name,
            m.phone as phone_number,
            m.membership_type,
            DATE_FORMAT(cl.checkin_time, '%H:%i') as checkin_time_formatted,
            CASE 
                WHEN cl.checkout_time IS NULL THEN '입장 중'
                ELSE DATE_FORMAT(cl.checkout_time, '%H:%i')
            END as checkout_time_formatted
        FROM checkin_log cl
        JOIN members m ON cl.member_id = m.id
        WHERE DATE(cl.checkin_time) = CURDATE()
        ORDER BY cl.checkin_time DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()

    @staticmethod
    def count_members(
        cursor: DictCursor,
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        """전체 회원 수 조회 ⭐ 컬럼명 수정"""
        conditions = []
        params = []

        if search:
            conditions.append("(name LIKE %s OR phone LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])

        if status == "active":
            conditions.append("is_active = TRUE")
            conditions.append("(end_date IS NULL OR end_date >= CURDATE())")
        elif status == "inactive":
            conditions.append("(is_active = FALSE OR (end_date IS NOT NULL AND end_date < CURDATE()))")
        elif status == "expiring_soon":
            conditions.extend([
                "is_active = TRUE",
                "end_date IS NOT NULL",
                "end_date >= CURDATE()",
                "end_date <= DATE_ADD(CURDATE(), INTERVAL 7 DAY)"
            ])

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        sql = f"SELECT COUNT(*) as total FROM members WHERE {where_clause}"
        cursor.execute(sql, tuple(params))
        result = cursor.fetchone()
        return result['total'] if result else 0