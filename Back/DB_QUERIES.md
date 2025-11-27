**개요**
- **목적**: 코드베이스에서 SQL의 `JOIN`, `서브쿼리(subquery)`, 그리고 CRUD 관련 트리거/이벤트의 사용 위치와 이유를 한 눈에 보기 쉽게 정리합니다.

**파일 목록 및 사용 이유**
  - **서브쿼리**: 회원 목록 조회(`get_members`)에서 각 회원의 최근 입장/퇴장 시간을 가져오기 위해 다음과 같은 서브쿼리를 사용합니다.
    - 이유: `checkins` 테이블에서 각 회원의 "최신" 입장/퇴장 시간만 필요하므로, 복잡한 GROUP BY나 윈도우 함수 대신 간단한 서브쿼리로 최신 행을 조회해 성능과 가독성 균형을 맞춥니다.
    - 사용 예: `(SELECT checkin_time FROM checkins WHERE member_id = m.member_id ORDER BY checkin_time DESC LIMIT 1) as last_checkin_time`
  - **서브쿼리(체크인 상태 필터)**: `checkin_status` 필터에서 현재 입장 중인지 여부를 판단하는 서브쿼리를 사용.
    - 이유: 한 회원에 대해 최신 체크인 행의 `checkout_time` 존재 여부로 입장 상태를 판단하기 위함.
  - **JOIN**: `get_today_checkins`는 `checkins`와 `members`를 `JOIN`하여 입장 기록에 회원 정보를 합쳐 반환.
    - 이유: 프론트에 표시할 때 회원의 `name`, `phone_number` 등 회원정보가 필요하므로 조인 사용.
  - **CRUD (INSERT/UPDATE)**: `create_member`, `update_member`, `delete_member` 등에서 직접 `INSERT`/`UPDATE`/`DELETE` 쿼리를 실행.
    - 이유: 관리자 기능에서 members 테이블의 생성/수정/삭제를 직접 제어해야 하기 때문.

## **데이터 모델링 개념 정리 (추가)**

**1. 논리적 모델링(Logical Modeling)**
- 정의: 비즈니스 요구사항을 기반으로 개념적 모델(개체/관계)을 구체적인 논리 구조로 설계하는 단계입니다. DBMS 종류에 구애받지 않고 "어떤 테이블이 필요한지", "각 테이블에 어떤 컬럼이 들어가는지", "테이블 간 관계(PK/FK)는 무엇인지" 등을 결정합니다.
- 논리 모델링에서 결정하는 것들:
  - 엔티티(테이블) 정의
  - 속성(컬럼) 정의
  - 기본키(PK) 설정
  - 관계(1:1, 1:N, N:M) 정의
  - 도메인(속성의 허용값 범위) 정의
  - 기본적인 제약조건(NOT NULL, UNIQUE 등) 설정

**2. 물리적 모델링(Physical Modeling)**
- 정의: 논리 모델을 실제 사용할 DBMS(MySQL, MariaDB, Oracle 등)에 맞게 최적화하고 구현 가능한 구조로 변환하는 단계입니다.
- 주요 결정 사항 예시:
  - 컬럼 타입 선택(VARCHAR 길이, DATE vs DATETIME 등)
  - 인덱스 설계(어떤 컬럼에 인덱스를 걸지, 복합 인덱스 순서)
  - PK/FK 구현 방식(예: `AUTO_INCREMENT` 사용 여부)
  - 파티셔닝, 테이블 엔진, 문자셋 등 DBMS-specific 설정
  - 성능을 위해 정규화를 일부 풀어 반정규화 적용 여부

**3. PK 적절성 (Primary Key Appropriateness)**
- PK 선택 기준:
  - 유일성(Unique): 각 행을 유일하게 식별해야 합니다.
  - 비NULL성: NULL을 허용하면 안 됩니다.
  - 불변성: 가능하면 값이 바뀌지 않는 컬럼을 사용해야 합니다.
  - 최소성: 불필요하게 많은 컬럼을 포함하지 않는 것이 좋습니다.
- 권장: 시스템 생성 surrogate key(`id`, `AUTO_INCREMENT`)를 기본 PK로 사용하고, 비즈니스 속성(이메일, 주민번호)은 별도의 UNIQUE 제약으로 관리.

**4. 데이터 타입(Data Type) 적절성**
- 각 컬럼에 대해 저장할 값의 범위와 연산을 고려해 타입을 선택합니다.
  - 예: `name` -> `VARCHAR(20)`, `age` -> `INT`, `gender` -> `CHAR(1)`, `created_at` -> `DATETIME`
- 피해야 할 실수 예시:
  - 날짜를 `VARCHAR`로 저장
  - 숫자를 `TEXT`/`VARCHAR`로 저장
  - 불필요하게 큰 `VARCHAR(5000)` 사용

**5. 도메인(Domain)**
- 정의: 컬럼이 가질 수 있는 값의 허용 범위(값의 타입과 목록 또는 범위).
- 예시:
  - `gender`: ('M','F')
  - `membership_type`: ('PT(1개월)', 'PT(3개월)', '1개월', '3개월', ...)
  - `age`: 0 ~ 150
  - `status`: ('활성','만료','곧 만료')

**6. 제약조건(Constraints)**
- 정의: DB가 데이터 무결성을 보장하기 위해 강제하는 규칙들.
- 주요 제약조건:
  - `NOT NULL`: 반드시 값이 있어야 함
  - `UNIQUE`: 값이 중복되면 안 됨 (예: 전화번호, 이메일 — 단 실제 변경 가능성 고려)
  - `PRIMARY KEY`: 유일성과 비NULL을 보장
  - `FOREIGN KEY`: 참조 무결성(참조 대상의 존재 보장)
  - `CHECK` (DB 지원 시): 값의 범위/형식 제한
  - `DEFAULT`: 기본값 설정

**권장 적용 예시 (현재 레포 적용 관점)**
- `members.member_id` : `PRIMARY KEY`, `AUTO_INCREMENT` (surrogate PK 권장)
- `members.phone_number` : `UNIQUE` (단, 전화번호 변경 워크플로가 있다면 nullable 포함 정책 검토)
- `checkins.member_id` : `FOREIGN KEY` -> `members.member_id` (참조 무결성)
- `deleted_members.deleted_at` : 인덱스(`idx_deleted_at`)로 삭제된 레코드의 만료(30일 후 삭제) 쿼리 성능 개선

---
추가로 원하시면 아래 항목도 문서에 포함해 드립니다:
- 각 테이블에 권장 인덱스와 이유(쿼리 패턴 기반)
- 서브쿼리 대신 윈도우 함수(사용 가능한 DBMS에서)로 성능 개선 제안
- 현재 스키마에 맞춘 ERD(간단한 ASCII 또는 PlantUML)

원하시는 추가 항목을 알려주시면 반영하겠습니다.
- **`Back/app/repositories/checkin_repository.py`**:
  - **JOIN**: `get_today_checkins`, per-checkin `CREATE EVENT` 등의 UPDATE 구문에서 `checkins`와 `members`를 `JOIN`하여 동기화 작업 수행.
    - 이유: 체크인 이벤트가 발생했을 때 `members` 테이블의 `checkin_time`/`checkout_time`을 업데이트해야 하므로 JOIN으로 관련 회원을 참조.
  - **이벤트 생성 (per-checkin Event)**: `create_checkin`에서 각 체크인 행에 대해 MySQL `EVENT`를 만들어 3시간 후 자동 퇴장 처리를 예약.
    - 이유: 사용자가 체크아웃을 하지 않았을 경우 자동으로 퇴장(checkout_time 설정) 및 `members` 동기화를 수행해야 하기 때문. DB 레벨 스케줄러를 이용하면 앱 프로세스가 죽어도 보장됨.

- **`Back/app/repositories/member_repository.py`**:
  - **JOIN 사용 예(간접)**: 회원 조회 및 당일 출입 목록 등에서 조인을 통해 회원과 체크인 정보를 결합(파일 내 `get_today_checkins` 등).
  - **CRUD**: `create_member`, `update_member`, `soft_delete_member` 등에서 `INSERT`, `UPDATE`, `ON DUPLICATE KEY UPDATE`를 사용.
    - 이유: 회원의 생성/수정/소프트 삭제(활성화 플래그 변경 및 `deleted_members` 테이블로 복사)를 처리해야 하고, 기존 데이터 유지 및 복원을 지원하기 위함.
  - **서브쿼리/조건조합**: 페이징/검색/필터링 로직에서 동적 WHERE 절과 CASE 문을 사용하여 정렬/상태 판단을 수행.

- **`Back/app/repositories/deleted_member_repository.py`**:
  - **CRUD(복원/영구삭제)**:
    - `restore_member`: `deleted_members`에서 데이터를 읽어 `members`로 복원(`INSERT ... ON DUPLICATE KEY UPDATE`) 후 `deleted_members`에서 삭제.
    - `permanent_delete_member` / `permanent_delete_all`: `deleted_members`와 `members` 양쪽에서 `DELETE` 실행.
    - 이유: 소프트 삭제(관리자 실수로부터 복구 가능)를 지원하고, 일정 기간 후 영구 삭제를 통해 보관 정책을 구현하기 위함.

- **`Back/app/auto_delete_triggers.py`** (및 `Back/auto_delete_triggers.py`의 실행 래퍼):
  - **트리거(Triggers)**:
    - `before_checkin_insert_immediate`: `checkins`에 INSERT될 때, 이미 3시간 이상 지난 체크인이면 `NEW.checkout_time`을 즉시 설정.
    - `after_checkin_insert_immediate`: INSERT 후 `members` 테이블의 `checkin_time`/`checkout_time`을 동기화(필요 시).
    - `remove_member_delete_trigger`: 기본적으로 자동으로 members 삭제 시 즉시 이동시키는 기존 트리거를 제거하여 "관리자 명시적 삭제만" 허용.
    - 이유: DB 레벨에서 데이터 정합성과 자동화(오래된 체크인 자동 퇴장, 삭제 정책)를 보장하고 앱 단에서 놓칠 수 있는 시나리오를 예방.
  - **EVENT(스케줄러)**:
    - `setup_auto_checkout_event`: 초기 실행 시 기존 3시간 이상 경과한 체크인을 즉시 정리하는 UPDATE (JOIN 사용).
    - `setup_auto_delete_event`: `deleted_members`에서 `deleted_at` 기준으로 30일 후 자동 영구 삭제하는 이벤트 생성.
    - 이유: 주기적/예약된 정리 작업을 DB에서 직접 실행하게 하여 앱에 의존하지 않는 일관된 유지보수를 수행.

**요약: 언제 무엇을 왜 사용했나**
- **JOIN**: `checkins`와 `members`는 관계형으로 자주 함께 조회되어야 하므로 조인을 사용하여 한 쿼리로 회원정보와 체크인정보를 결합합니다. (예: 당일 출입 목록, 자동 퇴장 업데이트)
- **서브쿼리**: 회원 목록에서 "각 회원의 최신 체크인/체크아웃" 같이 한 행에 대해 다른 테이블의 최신값을 가져올 때 사용합니다. 이는 복잡한 그룹화나 윈도우 함수 대신 간결하게 최신값을 얻을 수 있어 구현과 정렬에 편리합니다.
- **CRUD + 트리거/이벤트**: 회원의 소프트 삭제/복원 로직과 자동 정리(오래된 체크인 자동 퇴장, 30일 후 영구 삭제)를 DB 레벨 트리거/이벤트로 처리하여 데이터 정합성과 자동화를 보장합니다. 또한 앱 권한 문제로 이벤트/트리거 생성이 실패할 수 있으므로 예외를 기록하고 앱 레벨에서 보완하는 코드를 같이 둡니다.

**참고 파일 경로 (핵심)**
- `Back/app/services/admin_service.py`  — 서브쿼리(최근 체크인), 관리자 CRUD
- `Back/app/repositories/checkin_repository.py` — JOIN(회원정보 결합), per-checkin EVENT 생성
- `Back/app/repositories/member_repository.py` — members 테이블 CRUD, 페이징/필터링
- `Back/app/repositories/deleted_member_repository.py` — deleted_members 기반 복원/영구삭제 로직
- `Back/app/auto_delete_triggers.py` & `Back/auto_delete_triggers.py` — 트리거/이벤트 생성 및 초기 정리 스크립트

---
추가로 원하시면:
- 각 쿼리 코드 라인 참조 및 설명(라인 번호 포함) 추가
- 성능 관점(인덱스 권장, 서브쿼리→윈도우함수 전환)에서 개선안 제시
- DB 권한(이벤트, 트리거) 요구사항 문서화

원하시는 추가 옵션을 알려주세요.