from typing import List, Optional, Tuple
from pymysql.cursors import DictCursor


class DeletedMemberRepository:
    """삭제된 회원 관리 Repository (Raw Query 사용)"""
    
    @staticmethod
    def get_deleted_members_paginated(
        cursor: DictCursor,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None
    ) -> Tuple[List[dict], int]:
        """삭제된 회원 목록 조회 (페이지네이션) - Raw Query"""
        params = []
        where_clause = "1=1"
        
        # 검색 (공백 제거) - Raw Query
        if search:
            search_clean = search.replace(" ", "")
            where_clause += " AND (REPLACE(name, ' ', '') LIKE %s OR REPLACE(phone_number, ' ', '') LIKE %s)"
            params.extend([f"%{search_clean}%", f"%{search_clean}%"])
        
        # 총 개수 조회 - Raw Query
        count_sql = f"SELECT COUNT(*) as total FROM deleted_members WHERE {where_clause}"
        cursor.execute(count_sql, tuple(params))
        result = cursor.fetchone()
        total = result['total'] if result else 0
        
        # 목록 조회 - Raw Query
        sql = f"""
        SELECT 
            member_id, member_rank, name, phone_number, gender,
            membership_type, membership_start_date, membership_end_date,
            locker_number, locker_type, locker_start_date, locker_end_date,
            uniform_type, uniform_start_date, uniform_end_date,
            created_at, deleted_at
        FROM deleted_members
        WHERE {where_clause}
        ORDER BY deleted_at DESC
        LIMIT %s OFFSET %s
        """
        params.extend([limit, skip])
        cursor.execute(sql, tuple(params))
        members = cursor.fetchall()
        
        return members, total
    
    @staticmethod
    def restore_member(cursor: DictCursor, member_id: int) -> bool:
        """회원 복원 (deleted_members -> members) - Raw Query"""
        # 1. deleted_members에서 데이터 조회 - Raw Query
        sql = """
        SELECT 
            member_id, member_rank, name, phone_number, gender,
            membership_type, membership_start_date, membership_end_date,
            locker_number, locker_type, locker_start_date, locker_end_date,
            uniform_type, uniform_start_date, uniform_end_date,
            created_at
        FROM deleted_members
        WHERE member_id = %s
        """
        cursor.execute(sql, (member_id,))
        deleted_member = cursor.fetchone()
        
        if not deleted_member:
            return False
        
        # 2. members 테이블에 복원 (is_active = TRUE) - Raw Query
        insert_sql = """
        INSERT INTO members (
            member_id, member_rank, name, phone_number, gender,
            membership_type, membership_start_date, membership_end_date,
            locker_number, locker_type, locker_start_date, locker_end_date,
            uniform_type, uniform_start_date, uniform_end_date,
            is_active, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s)
        ON DUPLICATE KEY UPDATE
            is_active = TRUE,
            member_rank = VALUES(member_rank),
            name = VALUES(name),
            phone_number = VALUES(phone_number),
            gender = VALUES(gender),
            membership_type = VALUES(membership_type),
            membership_start_date = VALUES(membership_start_date),
            membership_end_date = VALUES(membership_end_date),
            locker_number = VALUES(locker_number),
            locker_type = VALUES(locker_type),
            locker_start_date = VALUES(locker_start_date),
            locker_end_date = VALUES(locker_end_date),
            uniform_type = VALUES(uniform_type),
            uniform_start_date = VALUES(uniform_start_date),
            uniform_end_date = VALUES(uniform_end_date)
        """
        cursor.execute(insert_sql, (
            deleted_member['member_id'],
            deleted_member['member_rank'],
            deleted_member['name'],
            deleted_member['phone_number'],
            deleted_member['gender'],
            deleted_member['membership_type'],
            deleted_member['membership_start_date'],
            deleted_member['membership_end_date'],
            deleted_member['locker_number'],
            deleted_member['locker_type'],
            deleted_member['locker_start_date'],
            deleted_member['locker_end_date'],
            deleted_member['uniform_type'],
            deleted_member['uniform_start_date'],
            deleted_member['uniform_end_date'],
            deleted_member['created_at']
        ))
        
        # 3. deleted_members에서 삭제 - Raw Query
        delete_sql = "DELETE FROM deleted_members WHERE member_id = %s"
        cursor.execute(delete_sql, (member_id,))
        
        cursor.connection.commit()
        return True
    
    @staticmethod
    def permanent_delete_member(cursor: DictCursor, member_id: int) -> bool:
        """회원 영구 삭제 - Raw Query (deleted_members와 members 모두에서 삭제)"""
        # 1. deleted_members에서 삭제
        sql1 = "DELETE FROM deleted_members WHERE member_id = %s"
        cursor.execute(sql1, (member_id,))
        
        # 2. members에서도 삭제
        sql2 = "DELETE FROM members WHERE member_id = %s"
        result = cursor.execute(sql2, (member_id,))
        
        cursor.connection.commit()
        return result > 0
    
    @staticmethod
    def permanent_delete_all(cursor: DictCursor) -> int:
        """모든 삭제된 회원 영구 삭제 - Raw Query (deleted_members와 members 모두에서 삭제)"""
        # 1. deleted_members에서 member_id 목록 가져오기
        sql_select = "SELECT member_id FROM deleted_members"
        cursor.execute(sql_select)
        member_ids = [row['member_id'] for row in cursor.fetchall()]
        
        # 2. deleted_members에서 모두 삭제
        sql1 = "DELETE FROM deleted_members"
        cursor.execute(sql1)
        
        # 3. members에서도 해당 member_id들 삭제
        if member_ids:
            placeholders = ', '.join(['%s'] * len(member_ids))
            sql2 = f"DELETE FROM members WHERE member_id IN ({placeholders})"
            cursor.execute(sql2, tuple(member_ids))
        
        cursor.connection.commit()
        return len(member_ids)
    
    @staticmethod
    def restore_all(cursor: DictCursor) -> int:
        """모든 삭제된 회원 복원 - Raw Query"""
        # 1. deleted_members에서 모든 데이터 조회
        sql_select = """
        SELECT 
            member_id, member_rank, name, phone_number, gender,
            membership_type, membership_start_date, membership_end_date,
            locker_number, locker_type, locker_start_date, locker_end_date,
            uniform_type, uniform_start_date, uniform_end_date,
            created_at
        FROM deleted_members
        """
        cursor.execute(sql_select)
        deleted_members = cursor.fetchall()
        
        if not deleted_members:
            return 0
        
        # 2. members 테이블에 복원
        insert_sql = """
        INSERT INTO members (
            member_id, member_rank, name, phone_number, gender,
            membership_type, membership_start_date, membership_end_date,
            locker_number, locker_type, locker_start_date, locker_end_date,
            uniform_type, uniform_start_date, uniform_end_date,
            is_active, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s)
        ON DUPLICATE KEY UPDATE
            is_active = TRUE,
            member_rank = VALUES(member_rank),
            name = VALUES(name),
            phone_number = VALUES(phone_number),
            gender = VALUES(gender),
            membership_type = VALUES(membership_type),
            membership_start_date = VALUES(membership_start_date),
            membership_end_date = VALUES(membership_end_date),
            locker_number = VALUES(locker_number),
            locker_type = VALUES(locker_type),
            locker_start_date = VALUES(locker_start_date),
            locker_end_date = VALUES(locker_end_date),
            uniform_type = VALUES(uniform_type),
            uniform_start_date = VALUES(uniform_start_date),
            uniform_end_date = VALUES(uniform_end_date)
        """
        
        for member in deleted_members:
            cursor.execute(insert_sql, (
                member['member_id'],
                member['member_rank'],
                member['name'],
                member['phone_number'],
                member['gender'],
                member['membership_type'],
                member['membership_start_date'],
                member['membership_end_date'],
                member['locker_number'],
                member['locker_type'],
                member['locker_start_date'],
                member['locker_end_date'],
                member['uniform_type'],
                member['uniform_start_date'],
                member['uniform_end_date'],
                member['created_at']
            ))
        
        # 3. deleted_members에서 삭제
        delete_sql = "DELETE FROM deleted_members"
        cursor.execute(delete_sql)
        
        cursor.connection.commit()
        return len(deleted_members)
