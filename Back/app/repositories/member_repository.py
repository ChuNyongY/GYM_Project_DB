from typing import List, Optional, Tuple
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
            name, phone_number, membership_type_id,
            membership_start_date, membership_end_date
        ) VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            member_data.name,
            member_data.phone_number,
            member_data.membership_type_id,
            member_data.membership_start_date,
            end_date
        ))
        member_id = cursor.lastrowid
        return MemberRepository.get_member_by_id(cursor, member_id)

    @staticmethod
    def get_member_by_id(cursor: DictCursor, member_id: int) -> Optional[dict]:
        sql = "SELECT * FROM members WHERE member_id = %s AND is_active = TRUE"
        cursor.execute(sql, (member_id,))
        return cursor.fetchone()

    @staticmethod
    def get_member_by_phone(cursor: DictCursor, phone_number: str) -> Optional[dict]:
        sql = "SELECT * FROM members WHERE phone_number = %s AND is_active = TRUE"
        cursor.execute(sql, (phone_number,))
        return cursor.fetchone()

    @staticmethod
    def search_by_last_four_digits(cursor: DictCursor, last_four: str) -> List[dict]:
        sql = """
        SELECT * FROM members 
        WHERE RIGHT(phone_number, 4) = %s 
        AND is_active = TRUE
        """
        cursor.execute(sql, (last_four,))
        return cursor.fetchall()

    @staticmethod
    def update_member(cursor: DictCursor, member_id: int, update_data: MemberUpdate) -> dict:
        update_fields = []
        values = []
        
        for key, value in update_data.dict(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{key} = %s")
                values.append(value)
        
        if not update_fields:
            return MemberRepository.get_member_by_id(cursor, member_id)
        
        sql = f"""
        UPDATE members 
        SET {', '.join(update_fields)}
        WHERE member_id = %s AND is_active = TRUE
        """
        values.append(member_id)
        cursor.execute(sql, tuple(values))
        return MemberRepository.get_member_by_id(cursor, member_id)

    @staticmethod
    def soft_delete_member(cursor: DictCursor, member_id: int) -> bool:
        sql = "UPDATE members SET is_active = FALSE WHERE member_id = %s"
        result = cursor.execute(sql, (member_id,))
        return result > 0

    @staticmethod
    def get_members_paginated(
        cursor: DictCursor,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> Tuple[List[dict], int]:
        conditions = []
        params = []

        if search:
            conditions.append("(m.name LIKE %s OR m.phone_number LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])

        if status == "active":
            conditions.append("m.is_active = TRUE")
        elif status == "inactive":
            conditions.append("m.is_active = FALSE")
        elif status == "expiring_soon":
            conditions.extend([
                "m.is_active = TRUE",
                "m.membership_end_date >= CURDATE()",
                "m.membership_end_date <= DATE_ADD(CURDATE(), INTERVAL 7 DAY)"
            ])

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # 전체 개수 조회
        count_sql = f"""
        SELECT COUNT(*) as total 
        FROM members m
        WHERE {where_clause}
        """
        cursor.execute(count_sql, tuple(params))
        total = cursor.fetchone()['total']

        # 회원 목록 조회
        sql = f"""
        SELECT m.*, mt.name as membership_type_name, mt.duration_months 
        FROM members m
        JOIN membership_types mt ON m.membership_type_id = mt.id
        WHERE {where_clause}
        ORDER BY m.member_id DESC
        LIMIT %s OFFSET %s
        """
        cursor.execute(sql, tuple(params + [limit, skip]))
        members = cursor.fetchall()

        return members, total
        query = query.filter(
            Member.is_active == True,
            Member.membership_end_date >= today,
            Member.membership_end_date <= today + 7
        )

        total = query.count()
        members = query.offset(skip).limit(limit).all()
        
        return members, total