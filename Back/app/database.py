import pymysql
from contextlib import contextmanager
from .config import get_settings

settings = get_settings()

def get_connection():
    """데이터베이스 연결을 생성합니다."""
    return pymysql.connect(
        host=settings.DB_HOST,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        db=settings.DB_NAME,
        port=settings.DB_PORT,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

@contextmanager
def get_cursor():
    """데이터베이스 커서를 컨텍스트 매니저로 제공합니다."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# FastAPI dependency
async def get_db():
    with get_cursor() as cursor:
        yield cursor