from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from zoneinfo import ZoneInfo

def parse_membership_type(membership_type: str) -> int:
    """
    회원권 종류 문자열을 개월 수로 변환
    예: '1개월' -> 1, 'PT(3개월)' -> 3, '1년' -> 12
    """
    # PT권 처리
    if membership_type.startswith('PT('):
        # 'PT(1개월)' -> '1개월'
        membership_type = membership_type[3:-1]
    
    # 개월수 추출
    if '개월' in membership_type:
        return int(membership_type.replace('개월', ''))
    elif '년' in membership_type:
        return int(membership_type.replace('년', '')) * 12
    else:
        raise ValueError(f"지원하지 않는 회원권 종류: {membership_type}")

def calculate_end_date(start_date: date, membership_type: str) -> date:
    """
    시작일로부터 회원권 종류에 따른 만료일을 계산
    membership_type: '1개월', '3개월', '6개월', '1년', 'PT(1개월)', 'PT(3개월)' 등
    """
    months = parse_membership_type(membership_type)
    return (start_date + relativedelta(months=months)) - relativedelta(days=1)

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