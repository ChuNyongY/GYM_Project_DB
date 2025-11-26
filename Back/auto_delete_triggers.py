#!/usr/bin/env python
"""
자동 삭제 트리거 및 이벤트 설정 스크립트
터미널에서 실행: python auto_delete_triggers.py
"""
import sys
import os

# 현재 파일의 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.auto_delete_triggers import setup_all

if __name__ == "__main__":
    try:
        setup_all()
        print("\n✅ 모든 자동 삭제 트리거 및 이벤트 설정이 완료되었습니다!")
        print("\n다음 명령어로 확인할 수 있습니다:")
        print("  - SHOW EVENTS;")
        print("  - SHOW TRIGGERS LIKE 'members';")
        print("  - SHOW TABLES LIKE 'deleted_members';")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 설정 중 오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
