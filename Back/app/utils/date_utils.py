from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from zoneinfo import ZoneInfo

def calculate_end_date(start_date: date, duration_months: int) -> date:
    """
    시작일로부터 지정된 개월 수 후의 만료일을 계산
    """
    return (start_date + relativedelta(months=duration_months)) - relativedelta(days=1)

def days_until_expiry(end_date: date) -> int:
    """
    오늘부터 만료일까지 남은 일수 계산
    음수: 이미 만료됨
    양수: 남은 일수
    """
    return (end_date - date.today()).days

def is_expiring_soon(end_date: date, warning_days: int = 7) -> bool:
    """
    만료 임박 여부 체크 (기본값: 7일)
    """
    days_left = days_until_expiry(end_date)
    return 0 <= days_left <= warning_days

def format_datetime_kst(dt: datetime) -> str:
    """
    datetime을 KST 기준으로 포맷팅
    """
    kst = dt.astimezone(ZoneInfo("Asia/Seoul"))
    return kst.strftime("%Y-%m-%d %H:%M:%S")