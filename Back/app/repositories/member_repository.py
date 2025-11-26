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
            member_rank, member_data.name, member_data.phone_number, member_data.gender.value if member_data.gender else None,
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
    def get_member_by_phone(cursor: DictCursor, phone_number: str, check_all: bool = False) -> Optional[dict]:
        """전화번호로 조회"""
        # [수정] phone -> phone_number
        sql = """
        SELECT 
            member_id, member_rank, name, phone_number, gender,
            membership_type, membership_start_date, membership_end_date,
            locker_number, locker_type, locker_start_date, locker_end_date,
            uniform_type, uniform_start_date, uniform_end_date, is_active, created_at
        FROM members
        WHERE phone_number = %s
        """
        # check_all이 False면 활성 회원만, True면 모든 회원 조회
        if not check_all:
            sql += " AND is_active = TRUE"
        
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
            uniform_type, uniform_start_date, uniform_end_date, is_active,
            checkin_time, checkout_time
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
            
            # Enum 타입 처리 (gender 등)
            if hasattr(value, 'value'):
                value = value.value
            
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
        """회원 소프트 삭제 (deleted_members로 이동)"""
        try:
            # 1. 회원 정보 조회 (is_active 상관없이)
            select_sql = """
            SELECT 
                member_id, member_rank, name, phone_number, gender,
                membership_type, membership_start_date, membership_end_date,
                locker_number, locker_type, locker_start_date, locker_end_date,
                uniform_type, uniform_start_date, uniform_end_date, created_at, is_active
            FROM members
            WHERE member_id = %s
            """
            cursor.execute(select_sql, (member_id,))
            member = cursor.fetchone()
            
            if not member:
                return False
            
            # 이미 비활성화된 회원인지 확인
            if not member['is_active']:
                # 이미 deleted_members에 있는지 확인
                check_sql = "SELECT member_id FROM deleted_members WHERE member_id = %s"
                cursor.execute(check_sql, (member_id,))
                if cursor.fetchone():
                    return True  # 이미 삭제 처리됨
            
            # 2. deleted_members에 삽입
            insert_sql = """
            INSERT INTO deleted_members (
                member_id, member_rank, name, phone_number, gender,
                membership_type, membership_start_date, membership_end_date,
                locker_number, locker_type, locker_start_date, locker_end_date,
                uniform_type, uniform_start_date, uniform_end_date,
                created_at, deleted_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE deleted_at = NOW()
            """
            cursor.execute(insert_sql, (
                member['member_id'], member['member_rank'], member['name'],
                member['phone_number'], member['gender'],
                member['membership_type'], member['membership_start_date'],
                member['membership_end_date'], member['locker_number'],
                member['locker_type'], member['locker_start_date'],
                member['locker_end_date'], member['uniform_type'],
                member['uniform_start_date'], member['uniform_end_date'],
                member['created_at']
            ))
            
            # 3. members 테이블에서 is_active를 FALSE로 변경
            update_sql = "UPDATE members SET is_active = FALSE WHERE member_id = %s"
            result = cursor.execute(update_sql, (member_id,))
            
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
        sort_by: Optional[str] = None,
        membership_filter: Optional[str] = None,
        checkin_status: Optional[str] = None,
        locker_filter: bool = False,
        uniform_filter: bool = False
    ) -> Tuple[List[dict], int]:
        """회원 목록 조회 (활성 회원만)"""
        where_conditions = ["is_active = TRUE"]  # 활성 회원만 조회
        print(f"🟢 [DEBUG] Initial where_conditions: {where_conditions}")
        
        # 검색 (공백 제거)
        if search:
            search_clean = search.replace(" ", "")
            where_conditions.append(f"(REPLACE(name, ' ', '') LIKE '%{search_clean}%' OR REPLACE(phone_number, ' ', '') LIKE '%{search_clean}%')")
        
        # 성별
        if gender:
            where_conditions.append(f"gender = '{gender}'")
        
        # 라커룸 필터
        if locker_filter:
            where_conditions.append("locker_type IS NOT NULL")
        
        # 회원복 필터
        if uniform_filter:
            where_conditions.append("uniform_type IS NOT NULL")
        
        # 활성/비활성
        if checkin_status == "active":
            where_conditions.append("checkin_time IS NOT NULL")
        elif checkin_status == "inactive":
            where_conditions.append("checkout_time IS NOT NULL")
        
        # PT권 / 회원권 필터 추가
        if membership_filter == "pt":
            where_conditions.append("membership_type LIKE 'PT%'")
        elif membership_filter == "membership":
            where_conditions.append("membership_type NOT LIKE 'PT%' AND membership_type IS NOT NULL")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # 정렬 (단순화)
        print(f"🔴 [DEBUG] Final where_clause: {where_clause}")
        
        if sort_by == "member_rank_asc":
            order_clause = "member_id ASC"
        elif sort_by == "member_rank_desc":
            order_clause = "member_id DESC"
        elif sort_by == "membership_type_asc":
            # PT권 정렬: PT(1개월), PT(3개월), PT(6개월), PT(1년) 순서
            order_clause = """CASE 
                WHEN membership_type = 'PT(1개월)' THEN 1
                WHEN membership_type = 'PT(3개월)' THEN 2
                WHEN membership_type = 'PT(6개월)' THEN 3
                WHEN membership_type = 'PT(1년)' THEN 4
                WHEN membership_type = '1개월' THEN 5
                WHEN membership_type = '3개월' THEN 6
                WHEN membership_type = '6개월' THEN 7
                WHEN membership_type = '1년' THEN 8
                ELSE 9
            END ASC"""
        elif sort_by == "locker_type_asc":
            order_clause = "locker_type ASC"
        elif sort_by == "uniform_type_asc":
            order_clause = "uniform_type ASC"
        elif sort_by == "checkin_time_desc":
            order_clause = "checkin_time DESC"
        elif sort_by == "checkout_time_desc":
            order_clause = "checkout_time DESC"
        else:
            order_clause = "member_id DESC"

        # 디버깅 로그
        print(f"🔍 [DEBUG] membership_filter: {membership_filter}")
        print(f"🔍 [DEBUG] sort_by: {sort_by}")
        print(f"🔍 [DEBUG] where_clause: {where_clause}")
        print(f"🔍 [DEBUG] order_clause: {order_clause}")

        count_sql = f"SELECT COUNT(*) as total FROM members WHERE {where_clause}"
        cursor.execute(count_sql)
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
        LIMIT {limit} OFFSET {skip}
        """
        cursor.execute(sql)
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
    