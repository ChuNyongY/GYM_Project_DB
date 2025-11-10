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
        if not admin:
            return False
        return verify_password(password, admin.get('password_hash'))

    @staticmethod
    def update_password(cursor: DictCursor, admin_id: int, new_password: str) -> bool:
        hashed = hash_password(new_password)
        sql = "UPDATE admins SET password_hash = %s WHERE id = %s"
        result = cursor.execute(sql, (hashed, admin_id))
        return result > 0