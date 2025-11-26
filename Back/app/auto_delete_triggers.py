"""
자동 삭제 트리거 및 이벤트 설정 스크립트
기존 database_setup.py 기능을 그대로 이전
"""
from .database import get_connection


def setup_deleted_members_table():
    """deleted_members 테이블 생성"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            CREATE TABLE IF NOT EXISTS deleted_members (
                member_id INT PRIMARY KEY,
                member_rank INT,
                name VARCHAR(100),
                phone_number VARCHAR(20),
                gender CHAR(1),
                membership_type VARCHAR(50),
                membership_start_date DATE,
                membership_end_date DATE,
                locker_number INT,
                locker_type VARCHAR(50),
                locker_start_date DATE,
                locker_end_date DATE,
                uniform_type VARCHAR(50),
                uniform_start_date DATE,
                uniform_end_date DATE,
                created_at DATETIME,
                deleted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_deleted_at (deleted_at)
            )
            """
            cursor.execute(sql)
            conn.commit()
            print("✅ deleted_members 테이블 생성 완료")
    except Exception as e:
        print(f"❌ deleted_members 테이블 생성 실패: {e}")
        conn.rollback()
    finally:
        conn.close()


def setup_auto_checkout_event():
    """3시간 자동 퇴장 이벤트 생성"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DROP EVENT IF EXISTS auto_checkout_after_3hours")
            sql = """
            CREATE EVENT auto_checkout_after_3hours
            ON SCHEDULE EVERY 30 MINUTE
            DO
            BEGIN
                UPDATE checkins
                SET checkout_time = NOW()
                WHERE checkout_time IS NULL
                AND TIMESTAMPDIFF(HOUR, checkin_time, NOW()) >= 3;
                UPDATE members m
                INNER JOIN checkins c ON m.member_id = c.member_id
                SET m.checkin_time = NULL, m.checkout_time = c.checkout_time
                WHERE c.checkout_time IS NOT NULL
                AND m.checkin_time IS NOT NULL
                AND TIMESTAMPDIFF(HOUR, m.checkin_time, NOW()) >= 3;
            END
            """
            cursor.execute(sql)
            conn.commit()
            print("✅ auto_checkout_after_3hours 이벤트 생성 완료 (is_active 유지)")
    except Exception as e:
        print(f"❌ auto_checkout_after_3hours 이벤트 생성 실패: {e}")
        conn.rollback()
    finally:
        conn.close()


def remove_member_delete_trigger():
    """기존 before_member_delete 트리거 제거 (자동 이동 방지)"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DROP TRIGGER IF EXISTS before_member_delete")
            conn.commit()
            print("✅ before_member_delete 트리거 제거 완료 (관리자 명시적 삭제만 허용)")
    except Exception as e:
        print(f"❌ before_member_delete 트리거 제거 실패: {e}")
        conn.rollback()
    finally:
        conn.close()


def setup_auto_delete_event():
    """30일 후 자동 영구 삭제 이벤트 생성 (deleted_members에서만)"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DROP EVENT IF EXISTS auto_delete_old_members")
            sql = """
            CREATE EVENT auto_delete_old_members
            ON SCHEDULE EVERY 1 DAY
            DO
            BEGIN
                DELETE FROM deleted_members
                WHERE TIMESTAMPDIFF(DAY, deleted_at, NOW()) >= 30;
            END
            """
            cursor.execute(sql)
            conn.commit()
            print("✅ auto_delete_old_members 이벤트 생성 완료 (30일 후 자동 영구 삭제)")
    except Exception as e:
        print(f"❌ auto_delete_old_members 이벤트 생성 실패: {e}")
        conn.rollback()
    finally:
        conn.close()


def remove_auto_delete_event():
    """기존 auto_delete_old_members 이벤트 제거 (자동 영구 삭제 방지)"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DROP EVENT IF EXISTS auto_delete_old_members")
            conn.commit()
            print("✅ auto_delete_old_members 이벤트 제거 완료 (관리자 수동 삭제만 허용)")
    except Exception as e:
        print(f"❌ auto_delete_old_members 이벤트 제거 실패: {e}")
        conn.rollback()
    finally:
        conn.close()


def enable_event_scheduler():
    """이벤트 스케줄러 활성화"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SET GLOBAL event_scheduler = ON")
            conn.commit()
            print("✅ 이벤트 스케줄러 활성화 완료")
    except Exception as e:
        print(f"❌ 이벤트 스케줄러 활성화 실패: {e}")
        conn.rollback()
    finally:
        conn.close()


def setup_all():
    print("=" * 50)
    print("자동 삭제 트리거 및 이벤트 설정 시작")
    print("=" * 50)
    setup_deleted_members_table()
    remove_member_delete_trigger()  # 트리거 제거 (관리자 명시적 삭제만 허용)
    setup_auto_checkout_event()
    setup_auto_delete_event()  # 30일 후 자동 영구 삭제 (deleted_members에서만)
    enable_event_scheduler()
    print("=" * 50)
    print("자동 삭제 트리거 및 이벤트 설정 완료")
    print("=" * 50)


if __name__ == "__main__":
    setup_all()
