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
            # Remove any existing recurring auto-checkout event to avoid
            # mass-updating records on schedule. We will perform a one-time
            # immediate cleanup for existing overdue checkins below, and
            # rely on per-checkin EVENTS (created at checkin time) for
            # future automatic checkouts at the exact checkin_time + 3 hours.
            cursor.execute("DROP EVENT IF EXISTS auto_checkout_after_3hours")

            # Immediate one-time cleanup: mark existing checkins older than
            # 180 minutes (3 hours) as checked out now. This makes the
            # behavior deterministic: any pre-existing rows that are >3h
            # will be updated once when the setup script runs.
            cleanup_sql = """
            UPDATE checkins c
            JOIN members m ON m.member_id = c.member_id
            SET c.checkout_time = NOW(),
                m.checkin_time = NULL,
                m.checkout_time = NOW()
            WHERE c.checkout_time IS NULL
              AND TIMESTAMPDIFF(MINUTE, c.checkin_time, NOW()) >= 180;
            """
            cursor.execute(cleanup_sql)
            conn.commit()
            print("✅ 기존 3시간 초과 체크인에 대한 즉시 정리 완료")
            print("⚠️ 반복 이벤트는 생성하지 않습니다. 앞으로는 per-checkin EVENT가 사용됩니다.")
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


def setup_checkin_insert_trigger():
    """INSERT 시 이미 3시간 이상 지난 체크인은 즉시 체크아웃 처리하는 트리거 생성"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # We need two triggers: a BEFORE INSERT to set NEW.checkout_time
            # when the inserted checkin is already older than 180 minutes,
            # and an AFTER INSERT to sync the members table. Updating the
            # checkins table in an AFTER trigger that was invoked by an
            # INSERT on the same table is not allowed, so use BEFORE to set
            # the NEW value.
            cursor.execute("DROP TRIGGER IF EXISTS before_checkin_insert_immediate")
            cursor.execute("DROP TRIGGER IF EXISTS after_checkin_insert_immediate")

            before_sql = """
            CREATE TRIGGER before_checkin_insert_immediate
            BEFORE INSERT ON checkins
            FOR EACH ROW
            BEGIN
                IF NEW.checkout_time IS NULL AND TIMESTAMPDIFF(MINUTE, NEW.checkin_time, NOW()) >= 180 THEN
                    SET NEW.checkout_time = NOW();
                END IF;
            END
            """
            cursor.execute(before_sql)

            after_sql = """
            CREATE TRIGGER after_checkin_insert_immediate
            AFTER INSERT ON checkins
            FOR EACH ROW
            BEGIN
                IF NEW.checkout_time IS NOT NULL AND TIMESTAMPDIFF(MINUTE, NEW.checkin_time, NOW()) >= 180 THEN
                    UPDATE members SET checkin_time = NULL, checkout_time = NOW() WHERE member_id = NEW.member_id;
                END IF;
            END
            """
            cursor.execute(after_sql)
            conn.commit()
            print("✅ before/after checkin insert 트리거 생성 완료 (과거 체크인 즉시 퇴장 처리)")
    except Exception as e:
        print(f"❌ after_checkin_insert_immediate 트리거 생성 실패: {e}")
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
            # Enable the event scheduler. Changing GLOBAL time_zone requires
            # elevated privileges and can fail; avoid attempting it here to
            # prevent unexpected permission errors. If global time_zone must
            # be changed, do so manually with the DB admin/root account.
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
    # Create INSERT trigger that immediately checks out past checkins
    setup_checkin_insert_trigger()
    setup_auto_delete_event()  # 30일 후 자동 영구 삭제 (deleted_members에서만)
    enable_event_scheduler()
    print("=" * 50)
    print("자동 삭제 트리거 및 이벤트 설정 완료")
    print("=" * 50)


if __name__ == "__main__":
    setup_all()
