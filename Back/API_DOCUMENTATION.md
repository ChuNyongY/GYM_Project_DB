# GYM Project API Documentation

이 문서는 프론트엔드 개발자가 로컬 개발 및 통합 테스트를 빠르게 시작할 수 있도록 최소한의 엔드포인트 설명과 샘플 요청/응답을 제공합니다.

기본 정보
- 베이스 URL: /api
- 인증: 관리자 토큰 기반 (OAuth2 Bearer). `/api/admin/login`로 토큰을 발급받아 Authorization: Bearer <token> 헤더 사용.
- 모든 엔드포인트는 JSON을 주고받습니다.

----------------

## Members

### 1) 회원 생성
- 경로: POST /api/members/
- 바디: MemberCreate 스키마 (JSON)
  - 예: { "name": "홍길동", "phone_number": "01012345678", "membership_type_id": 1, "membership_start_date": "2025-11-01" }
- 응답: 생성된 회원 정보 (dict)
  - 예: { "member_id": 123, "name": "홍길동", "phone_number": "01012345678", "membership_end_date": "2026-11-01", ... }

### 2) 회원 목록 조회
- 경로: GET /api/members/
- 쿼리 파라미터: page (기본 1), size (기본 20), search, status (active|inactive|expiring_soon)
- 응답 예:
  {
    "total": 345,
    "page": 1,
    "size": 20,
    "members": [ { "member_id": 1, "name": "...", "phone_number": "..." }, ... ]
  }

### 3) 회원 상세 조회
- 경로: GET /api/members/{member_id}
- 응답: 회원 객체 (dict)

### 4) 회원 수정
- 경로: PUT /api/members/{member_id}
- 바디: MemberUpdate 스키마
- 응답: 수정된 회원 객체

### 5) 회원 연장/기타
- 경로: POST /api/members/{member_id}/extend-membership
- 파라미터: membership_type_id
- 응답: 연장 결과

----------------

## Checkin (출입)

### 1) 키오스크 검색 (전화 뒷자리)
- 경로: POST /api/kiosk/search-by-phone
- 바디/Form: { "last_four_digits": "1234" }
- 응답 예:
  {
    "status": "success",
    "count": 1,
    "members": [ { "member_id": 12, "name": "A", "phone_number": "010..." } ]
  }

### 2) 키오스크 체크인
- 경로: POST /api/kiosk/checkin/{member_id}
- 응답: 체크인 결과 (checkin_time 포함)

### 3) 당일 출입 목록
- 경로: GET /api/checkin/today?page=1&size=50
- 응답 예:
  {
    "total": 100,
    "page": 1,
    "size": 50,
    "checkins": [ { "checkin_id": 1, "member_id": 12, "checkin_time": "2025-11-05T09:00:00" }, ... ]
  }

### 4) 체크아웃 처리
- 경로: PUT /api/checkin/{checkin_id}/checkout
- 응답: 체크아웃 결과 (checkout_time, duration_minutes 등)

### 5) 회원별 출입 기록 조회
- 경로: GET /api/checkin/member/{member_id}?year=2025&month=11
- 응답: 기록 배열

----------------

## Rentals (락커 / 회원복)

### 1) 락커 연장
- 경로: POST /api/rentals/locker/{member_id}/extend?rental_type=3개월
- 인증 필요
- 응답: 연장 결과 및 이전/새 만료일

### 2) 회원복 연장
- 경로: POST /api/rentals/uniform/{member_id}/extend?rental_type=3개월
- 인증 필요

### 3) 사용 가능한 락커 조회
- 경로: GET /api/rentals/lockers/available
- 응답 예: { "available_lockers": [1,2,3,...], "total_available": 50, "total_lockers": 100 }

----------------

## Admin

### 1) 관리자 로그인
- 경로: POST /api/admin/login
- 폼/바디: { "password": "..." }
- 응답: { "status": "success", "token": "<jwt>" }

### 2) 관리자 비밀번호 변경
- 경로: PUT /api/admin/change-password
- 인증: Bearer 토큰 필요
- 바디: { "current_password": "...", "new_password": "..." }
- 응답: 변경 결과

----------------

## 인증(토큰)
- 토큰 발급: POST /api/admin/login
- 요청에 Authorization 헤더 추가: `Authorization: Bearer <token>`

----------------

## 참고
- FastAPI의 자동 생성된 OpenAPI 스펙: `/openapi.json`
- Swagger UI: `/docs` (개발 환경에서 사용)

문서가 더 자세히 필요하면 (예: 각 스키마 필드 타입, 에러 코드, 예외 응답 구조) 알려주세요. 빠르게 추가하겠습니다.
