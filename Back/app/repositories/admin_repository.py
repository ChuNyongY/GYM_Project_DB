from typing import Optional
from ..utils.security import hash_password, verify_password
from pymysql.cursors import DictCursor

class AdminRepository:
    @staticmethod
    def get_admin(cursor: DictCursor) -> Optional[dict]:
        sql = "SELECT * FROM admins LIMIT 1"
        cursor.execute(sql)
        return cursor.fetchone()

    @staticmethod
    def create_admin(cursor: DictCursor, password: str) -> dict:
        hashed = hash_password(password)
        sql = "INSERT INTO admins (password_hash) VALUES (%s)"
        cursor.execute(sql, (hashed,))
        admin_id = cursor.lastrowid
        cursor.execute("SELECT * FROM admins WHERE id = %s", (admin_id,))
        return cursor.fetchone()

    @staticmethod
    def verify_password(cursor: DictCursor, password: str) -> bool:
        admin = AdminRepository.get_admin(cursor)
        
        # 🔍 디버깅 로그
        print(f"🔍 Admin data: {admin}")
        print(f"🔍 Input password: {password}")
        
        if not admin:
            print("❌ No admin found!")
            return False
        
        stored_hash = admin.get('password_hash')  # ← 수정!
        print(f"🔍 Stored hash: {stored_hash}")
        
        result = verify_password(password, stored_hash)
        print(f"🔍 Verification result: {result}")
        return result

    @staticmethod
    def update_password(cursor: DictCursor, admin_id: int, new_password: str) -> bool:
        hashed = hash_password(new_password)
        sql = "UPDATE admins SET password_hash = %s WHERE id = %s"
        result = cursor.execute(sql, (hashed, admin_id))
        return result > 0