from typing import List, Optional, Tuple, Dict, Any
from ..schemas.member import MemberCreate, MemberUpdate
from ..utils.date_utils import calculate_end_date
from pymysql.cursors import DictCursor


class MemberRepository:

    @staticmethod
    def set_active_status(cursor: DictCursor, member_id: int, is_active: bool):
        sql = """
         UPDATE members SET is_active = %s WHERE member_id = %s
        """
        cursor.execute(sql, (is_active, member_id))
        cursor.connection.commit()    
    
    @staticmethod
    def get_next_available_locker(cursor: DictCursor) -> Optional[int]:
        sql = """
        SELECT locker_number 
        FROM members 
        WHERE locker_number IS NOT NULL 
        AND locker_end_date >= CURDATE()
        AND is_active = TRUE
        """
        cursor.execute(sql)
        used_lockers = cursor.fetchall()
        used_numbers = {row['locker_number'] for row in used_lockers}
        
        for number in range(1, 101):
            if number not in used_numbers:
                return number
        return None 
    
    @staticmethod
    def get_next_member_rank(cursor: DictCursor) -> int:
        sql = "SELECT MAX(member_rank) as max_rank FROM members"
        cursor.execute(sql)
        result = cursor.fetchone()
        max_rank = result['max_rank'] if result and result['max_rank'] else 0
        return max_rank + 1
    
    @staticmethod
    def create_member(cursor: DictCursor, member_data: MemberCreate) -> dict:
        # [수정] phone -> phone_number, id -> member_id
        check_sql = "SELECT member_id FROM members WHERE phone_number = %s"
        cursor.execute(check_sql, (member_data.phone_number,))
        if cursor.fetchone():
            raise ValueError("이미 등록된 전화번호입니다.")
        
        member_rank = MemberRepository.get_next_member_rank(cursor)
        
        locker_number = None
        if member_data.locker_type:
            locker_number = MemberRepository.get_next_available_locker(cursor)
            if locker_number is None:
                raise ValueError("사용 가능한 락커가 없습니다.")
        
        membership_end_date = calculate_end_date(
            member_data.membership_start_date,
            member_data.membership_type
        )
        
        # [수정] INSERT 컬럼명 DB와 일치시킴
        sql = """
        INSERT INTO members (
            member_rank, name, phone_number, gender, membership_type, membership_start_date, membership_end_date,
            locker_number, locker_type, locker_start_date, locker_end_date,
            uniform_type, uniform_start_date, uniform_end_date,
            is_active, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, NOW())
        """
        
        cursor.execute(sql, (
            member_rank, member_data.name, member_data.phone_number, member_data.gender,
            member_data.membership_type, member_data.membership_start_date, membership_end_date,
            locker_number, member_data.locker_type, member_data.locker_start_date, member_data.locker_end_date,
            member_data.uniform_type, member_data.uniform_start_date, member_data.uniform_end_date
        ))
        
        member_id = cursor.lastrowid
        cursor.connection.commit()
        
        return MemberRepository.get_member_by_id(cursor, member_id)

    @staticmethod
    def get_member_by_id(cursor: DictCursor, member_id: int) -> Optional[dict]:
        """회원 ID로 조회 (입장/퇴장 상태 무관)"""
        sql = """
        SELECT 
            member_id, member_rank, name, phone_number, gender,
            membership_type, membership_start_date, membership_end_date,
            locker_number, locker_type, locker_start_date, locker_end_date,
            uniform_type, uniform_start_date, uniform_end_date, is_active, created_at,
            checkin_time, checkout_time
        FROM members
        WHERE member_id = %s
        """
        cursor.execute(sql, (member_id,))
        return cursor.fetchone()

    @staticmethod
    def get_member_by_phone(cursor: DictCursor, phone_number: str) -> Optional[dict]:
        """전화번호로 조회"""
        # [수정] phone -> phone_number
        sql = """
        SELECT 
            member_id, member_rank, name, phone_number, gender,
            membership_type, membership_start_date, membership_end_date,
            locker_number, locker_type, locker_start_date, locker_end_date,
            uniform_type, uniform_start_date, uniform_end_date, is_active, created_at
        FROM members
        WHERE phone_number = %s AND is_active = TRUE
        """
        cursor.execute(sql, (phone_number,))
        return cursor.fetchone()

    @staticmethod
    def list_members_by_phone_tail(cursor: DictCursor, last_four: str) -> List[dict]:
        """휴대폰 끝 4자리로 검색 (입장/퇴장 상태 무관)"""
        sql = """
        SELECT 
            member_id, member_rank, name, phone_number, gender,
            membership_type, membership_start_date, membership_end_date,
            locker_number, locker_type, locker_start_date, locker_end_date,
            uniform_type, uniform_start_date, uniform_end_date, is_active
        FROM members
        WHERE RIGHT(phone_number, 4) = %s
        ORDER BY name ASC
        """
        cursor.execute(sql, (last_four,))
        return cursor.fetchall()

    @staticmethod
    def update_member(cursor: DictCursor, member_id: int, update_data: Dict[str, Any]) -> dict:
        """회원 정보 수정"""
        if not update_data:
            return MemberRepository.get_member_by_id(cursor, member_id)
        
        member = MemberRepository.get_member_by_id(cursor, member_id)
        if not member:
            raise ValueError("회원을 찾을 수 없습니다.")
        
        # 락커 자동 배정 로직
        if 'locker_type' in update_data and update_data['locker_type']:
             if not member.get('locker_number'):
                locker_number = MemberRepository.get_next_available_locker(cursor)
                if locker_number is None:
                    raise ValueError("사용 가능한 락커가 없습니다.")
                update_data['locker_number'] = locker_number

        # [수정] 컬럼 매핑 (API 키 -> DB 컬럼)
        column_mapping = {
            'phone_number': 'phone_number', # 그대로
            'membership_start_date': 'membership_start_date', # 그대로
            'membership_end_date': 'membership_end_date', # 그대로
            'name': 'name',
            'gender': 'gender'
        }
        
        update_fields = []
        values = []
        
        for key, value in update_data.items():
            # 매핑된 컬럼명이 있거나, 락커/유니폼 관련 컬럼이면 사용
            db_col = column_mapping.get(key, key)
            
            # 값 유효성 체크 (None이어도 업데이트해야 하는 경우 등)
            if key in column_mapping or key.startswith('locker_') or key.startswith('uniform_') or key == 'membership_type':
                 update_fields.append(f"{db_col} = %s")
                 values.append(value)
        
        if not update_fields:
            return MemberRepository.get_member_by_id(cursor, member_id)
        
        # [수정] id -> member_id
        sql = f"UPDATE members SET {', '.join(update_fields)} WHERE member_id = %s AND is_active = TRUE"
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
        return MemberRepository.update_member(
            cursor, 
            member_id, 
            update_data.dict(exclude_unset=True)
        )

    @staticmethod
    def soft_delete_member(cursor: DictCursor, member_id: int) -> bool:
        # [수정] id -> member_id
        sql = "UPDATE members SET is_active = FALSE WHERE member_id = %s"
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
        status: Optional[str] = None,
        gender: Optional[str] = None,
        sort_by: Optional[str] = None
    ) -> Tuple[List[dict], int]:
        """회원 목록 조회"""
        conditions = []
        params = []

        # [수정] phone -> phone_number
        if search:
            conditions.append("(name LIKE %s OR phone_number LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])

        if gender:
            conditions.append("gender = %s")
            params.append(gender)

        # [수정] end_date -> membership_end_date
        if status == "active":
            conditions.append("is_active = TRUE")
            conditions.append("(membership_end_date IS NULL OR membership_end_date >= CURDATE())")
        elif status == "inactive":
            conditions.append("(is_active = FALSE OR (membership_end_date IS NOT NULL AND membership_end_date < CURDATE()))")
        elif status == "expiring_soon":
            conditions.extend([
                "is_active = TRUE",
                "membership_end_date IS NOT NULL",
                "membership_end_date >= CURDATE()",
                "membership_end_date <= DATE_ADD(CURDATE(), INTERVAL 7 DAY)"
            ])

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # 정렬
        order_clause = "created_at DESC"
        if sort_by == "recent_checkin":
            order_clause = "checkin_time DESC"
        elif sort_by == "name":
            order_clause = "name ASC"
        elif sort_by == "end_date":
            order_clause = "membership_end_date ASC"

        count_sql = f"SELECT COUNT(*) as total FROM members WHERE {where_clause}"
        cursor.execute(count_sql, tuple(params))
        result = cursor.fetchone()
        total = result['total'] if result else 0

        # [수정] 모든 컬럼명 DB와 일치 (id -> member_id 등)
        sql = f"""
        SELECT 
            member_id, member_rank, name, phone_number, gender,
            membership_type, membership_start_date, membership_end_date,
            locker_number, locker_type, locker_start_date, locker_end_date,
            uniform_type, uniform_start_date, uniform_end_date, is_active, created_at,
            checkin_time, checkout_time,
            CASE 
                WHEN membership_end_date IS NULL THEN NULL
                WHEN membership_end_date < CURDATE() THEN '만료'
                WHEN membership_end_date <= DATE_ADD(CURDATE(), INTERVAL 7 DAY) THEN '곧 만료'
                ELSE '활성'
            END as status_text
        FROM members
        WHERE {where_clause}
        ORDER BY {order_clause}
        LIMIT %s OFFSET %s
        """
        cursor.execute(sql, tuple(params + [limit, skip]))
        members = cursor.fetchall()

        return members, total

    @staticmethod
    def get_today_checkins(cursor: DictCursor) -> List[dict]:
        """당일 입장 회원 목록"""
        # [수정] id -> member_id, checkins 테이블 컬럼명 일치
        sql = """
        SELECT 
            cl.id as checkin_id, cl.member_id, cl.checkin_time, cl.checkout_time,
            m.name, m.phone_number, m.gender, m.membership_type,
            DATE_FORMAT(cl.checkin_time, '%H:%i') as checkin_time_formatted,
            CASE 
                WHEN cl.checkout_time IS NULL THEN '입장 중'
                ELSE DATE_FORMAT(cl.checkout_time, '%H:%i')
            END as checkout_time_formatted
        FROM checkins cl
        JOIN members m ON cl.member_id = m.member_id
        WHERE DATE(cl.checkin_time) = CURDATE()
        ORDER BY cl.checkin_time DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()

    @staticmethod
    def count_members(cursor: DictCursor) -> int:
        """전체 회원 수 조회"""
        sql = "SELECT COUNT(*) as total FROM members WHERE is_active = TRUE"
        cursor.execute(sql)
        result = cursor.fetchone()
        return result['total'] if result else 0
    