# 🏋️ 헬스장 관리 시스템 (GYM Management System)

> 헬스장 회원 관리, 출입 체크, 관리자 대시보드를 제공하는 Full-Stack 웹 애플리케이션

## 📑 목차

- [프로젝트 개요](#-프로젝트-개요)
- [주요 기능](#-주요-기능)
- [기술 스택](#-기술-스택)
- [프로젝트 구조](#-프로젝트-구조)
- [화면 흐름도](#-화면-흐름도)
  - [회원용 키오스크 화면](#1-회원용-키오스크-화면-userapptsx)
  - [관리자 화면](#2-관리자-화면-adminapptsx)
- [설치 및 실행](#-설치-및-실행)
  - [백엔드 설정](#1-백엔드-설정)
  - [프론트엔드 설정](#2-프론트엔드-설정)
- [API 엔드포인트](#-api-엔드포인트)
- [트러블슈팅](#-트러블슈팅)
- [배포 가이드](#-배포-가이드)

---

## 🎯 프로젝트 개요

이 프로젝트는 헬스장의 효율적인 운영을 위한 종합 관리 시스템입니다.

### 핵심 가치
- **회원 자가 출입 체크**: 전화번호 뒷자리 4자리만으로 빠른 출입 확인
- **관리자 대시보드**: 회원 정보 관리, 출입 기록 조회, 회원권 관리
- **실시간 데이터**: 즉각적인 출입 기록 저장 및 조회
- **사용자 친화적 UI**: 터치스크린 키오스크 최적화 인터페이스

---

## ✨ 주요 기능

### 회원용 키오스크 (UserApp)
- ✅ 전화번호 뒷자리 4자리로 간편 출입 체크
- ✅ 실시간 출입 확인 메시지
- ✅ 회원권 만료 상태 자동 확인
- ✅ 터치스크린 최적화 숫자 키패드

### 관리자 대시보드 (AdminApp)
- 🔐 관리자 로그인 (비밀번호 인증)
- 👥 회원 목록 조회 (페이지네이션, 검색, 필터)
- ➕ 회원 추가/수정/삭제
- 🎫 회원권 관리 (3개월, 6개월, 1년)
- 📊 회원별 출입 기록 조회
- 🔍 회원 상태 필터링 (전체/활성/곧 만료)

---

## 🛠 기술 스택

### Frontend
- **Framework**: React 18.2 + TypeScript
- **Build Tool**: Vite 5.0
- **Routing**: React Router DOM 6.20
- **Styling**: TailwindCSS 3.4
- **HTTP Client**: Axios 1.6

### Backend
- **Framework**: FastAPI 0.120
- **Language**: Python 3.13
- **Database**: MySQL (via PyMySQL)
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt
- **Server**: Uvicorn (ASGI)

### Database
- **RDBMS**: MySQL
- **ORM**: Raw SQL (via PyMySQL cursor)

---

## 📂 프로젝트 구조

```
GYM_Project_DB/
├── Front/                          # 프론트엔드 (React + Vite)
│   ├── public/                     # 정적 자산
│   ├── src/
│   │   ├── assets/                 # 이미지, 폰트 등
│   │   ├── components/             # 재사용 컴포넌트
│   │   │   └── NumericKeypad.tsx   # 숫자 키패드 컴포넌트
│   │   ├── pages/                  # 페이지 컴포넌트
│   │   │   ├── UserApp.tsx         # 회원용 키오스크 화면
│   │   │   └── AdminApp.tsx        # 관리자 대시보드
│   │   ├── services/               # API 서비스 레이어
│   │   │   ├── api.ts              # 기본 Axios 설정
│   │   │   ├── kioskService.ts     # 키오스크 API
│   │   │   └── adminService.ts     # 관리자 API
│   │   ├── types/                  # TypeScript 타입 정의
│   │   │   └── api.types.ts
│   │   ├── App.tsx                 # 라우팅 설정
│   │   ├── main.tsx                # 엔트리 포인트
│   │   └── index.css               # 글로벌 스타일
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── Back/                           # 백엔드 (FastAPI)
│   ├── app/
│   │   ├── routers/                # API 라우터
│   │   │   ├── admin.py            # 관리자 API
│   │   │   ├── checkin.py          # 출입 체크 API
│   │   │   ├── kiosk.py            # 키오스크 API
│   │   │   ├── members.py          # 회원 API
│   │   │   └── rentals.py          # 대여 API
│   │   ├── services/               # 비즈니스 로직
│   │   │   ├── admin_service.py    # 관리자 서비스
│   │   │   ├── checkin_service.py  # 출입 서비스
│   │   │   ├── member_service.py   # 회원 서비스
│   │   │   └── rental_service.py   # 대여 서비스
│   │   ├── repositories/           # 데이터 접근 레이어
│   │   │   ├── admin_repository.py
│   │   │   ├── checkin_repository.py
│   │   │   ├── member_repository.py
│   │   │   ├── locker_repository.py
│   │   │   └── uniform_repository.py
│   │   ├── schemas/                # Pydantic 스키마
│   │   │   ├── admin.py
│   │   │   ├── member.py
│   │   │   ├── checkin_log.py
│   │   │   └── ...
│   │   ├── utils/                  # 유틸리티
│   │   │   ├── security.py         # JWT, 비밀번호 해싱
│   │   │   ├── validators.py       # 유효성 검사
│   │   │   └── date_utils.py       # 날짜 처리
│   │   ├── config.py               # 환경 설정
│   │   ├── database.py             # DB 연결
│   │   └── main.py                 # FastAPI 앱 진입점
│   ├── requirements.txt            # Python 의존성
│   └── .env                        # 환경 변수 (생성 필요)
│
└── README.md                       # 이 문서
```

---

## 🔄 화면 흐름도

### 1. 회원용 키오스크 화면 (`UserApp.tsx`)

```
┌─────────────────────────────────────────────────────┐
│  [회원용 키오스크 화면] (/kiosk)                     │
├─────────────────────────────────────────────────────┤
│                                                       │
│  좌측 (60%)                    │  우측 (40%)         │
│  ┌─────────────────────┐       │  ┌─────────────┐   │
│  │ FITNESS CENTER      │       │  │ 공지사항     │   │
│  │ 💪                  │       │  ├─────────────┤   │
│  │                     │       │  │ 출입체크     │   │
│  │ [이미지/브랜딩]      │       │  │ 전화번호 뒷 │   │
│  │                     │       │  │ 4자리 입력   │   │
│  │                     │       │  ├─────────────┤   │
│  │ 현재시간: 14:32     │       │  │ [숫자키패드] │   │
│  │ 2025년 11월 10일    │       │  │  1  2  3    │   │
│  └─────────────────────┘       │  │  4  5  6    │   │
│                                │  │  7  8  9    │   │
│                                │  │     0       │   │
│                                │  │  [←] [확인] │   │
│                                │  └─────────────┘   │
└─────────────────────────────────────────────────────┘

[사용자 시나리오]

1. 회원이 전화번호 뒷자리 4자리 입력 (예: 5678)
   ↓
2. [확인] 버튼 클릭
   ↓
3. API 호출: POST /api/checkin
   - Request: { "phone_last_four": "5678" }
   ↓
4. 백엔드 처리:
   - 전화번호 뒷자리로 회원 검색
   - 회원권 만료 여부 확인
   - 출입 기록 DB 저장
   ↓
5. 응답 처리:
   
   [성공 시]
   ┌─────────────────────────────────┐
   │   ✅                             │
   │ 출입이 확인되었습니다!            │
   │                                  │
   │ 홍길동님                          │
   │ 입장 시간: 14:32                 │
   └─────────────────────────────────┘
   → 3초 후 자동으로 초기화
   
   [실패 시 - 회원 없음]
   ┌─────────────────────────────────┐
   │   ❌                             │
   │ 등록된 회원을 찾을 수 없습니다.   │
   │ 프론트 데스크에 문의하세요.       │
   └─────────────────────────────────┘
   
   [실패 시 - 회원권 만료]
   ┌─────────────────────────────────┐
   │   ❌                             │
   │ 홍길동님, 회원권이 만료되었습니다.│
   │ 프론트 데스크에서 갱신해주세요.   │
   └─────────────────────────────────┘
```

### 2. 관리자 화면 (`AdminApp.tsx`)

```
┌─────────────────────────────────────────────────────────────┐
│  [관리자 로그인] (/admin)                                    │
├─────────────────────────────────────────────────────────────┤
│                  ┌─────────────────────┐                     │
│                  │  관리자 로그인       │                     │
│                  ├─────────────────────┤                     │
│                  │  비밀번호:          │                     │
│                  │  [●●●●●●●●]        │                     │
│                  │  [입장하기]         │                     │
│                  └─────────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
                           ↓ (로그인 성공)
                           
┌─────────────────────────────────────────────────────────────┐
│  [관리자 대시보드] (/admin)                                  │
├─────────────────────────────────────────────────────────────┤
│  헬스장 관리 시스템                      [로그아웃]          │
│  총 150명의 회원                                             │
├─────────────────────────────────────────────────────────────┤
│  [검색창: 이름 또는 전화번호]  [검색]                        │
│  [전체] [활성] [곧 만료]                                     │
├─────────────────────────────────────────────────────────────┤
│  회원번호 │ 이름   │ 전화번호      │ 회원권 │ 시작일   │...  │
│  ─────────┼────────┼───────────────┼────────┼──────────┤    │
│     1     │ 홍길동 │ 010-1234-5678 │ 3개월  │2025.01.01│... │
│     2     │ 김철수 │ 010-9876-5432 │ 6개월  │2025.01.05│... │
│     3     │ 이영희 │ 010-5555-1234 │ 1년    │2024.12.01│... │
│                                                              │
│  [이전] 1 / 8 [다음]                                         │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ (회원 행 클릭)
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                           │  [회원 상세 정보 Drawer]         │
│  [메인 테이블]             │  ────────────────────────       │
│                           │  👤 홍길동님                     │
│  (좌측 60%)               │  회원번호: 1번                   │
│                           │  ────────────────────────       │
│                           │  📋 기본 정보                    │
│                           │  - 이름: 홍길동                  │
│                           │  - 전화번호: 010-1234-5678      │
│                           │  - 상태: [활성]                 │
│                           │  - 등록일: 2024년 11월 1일      │
│                           │                                  │
│                           │  🎫 회원권 정보                  │
│                           │  - 회원권: 3개월                │
│                           │  - 시작일: 2025년 1월 1일       │
│                           │  - 종료일: 2025년 4월 1일       │
│                           │                                  │
│                           │  📈 최근 출입 기록               │
│                           │  1. 11월 10일 14:32 출입        │
│                           │  2. 11월 9일  09:15 출입        │
│                           │  3. 11월 7일  18:20 출입        │
│                           │                                  │
│                           │  [수정] [닫기]        [삭제]    │
└─────────────────────────────────────────────────────────────┘

[관리자 시나리오]

1. 회원 목록 조회
   - GET /api/admin/members?page=1&size=20
   - 검색: GET /api/admin/members?search=홍길동
   - 필터: GET /api/admin/members?status=active

2. 회원 추가 (우측 하단 [+] 버튼)
   ↓
   [새 회원 추가 Drawer 열림]
   - 이름 입력
   - 전화번호 입력 (자동 포맷팅: 010-1234-5678)
   - 회원권 선택 (3개월/6개월/1년)
   - 시작일 선택 → 종료일 자동 계산
   ↓
   - POST /api/admin/members
   - Request: { name, phone_number, membership_type, ... }
   ↓
   - 성공 시: 목록 새로고침

3. 회원 정보 수정
   - [수정] 버튼 클릭 → 편집 모드 전환
   - 정보 수정
   - [저장] → PUT /api/admin/members/{member_id}

4. 회원 삭제
   - [삭제] 버튼 클릭
   - 확인 다이얼로그
   - DELETE /api/admin/members/{member_id}

5. 출입 기록 조회
   - Drawer에서 자동으로 로드
   - GET /api/admin/members/{member_id}/checkins
```

---

## 🚀 설치 및 실행

### 사전 준비
- **Node.js** 18+ (프론트엔드)
- **Python** 3.9+ (백엔드)
- **MySQL** 5.7+ (데이터베이스)
- **Git** (선택사항)

---

### 1. 백엔드 설정

#### 1.1. 가상환경 생성 및 활성화

```powershell
# Back 폴더로 이동
cd Back

# 가상환경 생성 (Windows PowerShell)
python -m venv .venv

# 가상환경 활성화
.\.venv\Scripts\Activate.ps1

# (Linux/Mac의 경우)
# source .venv/bin/activate
```

#### 1.2. 의존성 설치

```powershell
pip install -r requirements.txt
```

#### 1.3. 환경 변수 설정

**`.env` 파일 생성** (`Back/.env`)

```env
# Database 설정
DB_HOST=localhost
DB_PORT=3306
DB_USER=gym_admin
DB_PASSWORD=your_database_password_here
DB_NAME=gym_management

# JWT 설정 (아래 명령으로 안전한 키 생성)
# python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your_generated_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 관리자 설정
DEFAULT_ADMIN_PASSWORD=1234

# 애플리케이션 설정
DEBUG=True
API_PREFIX=/api
```

**SECRET_KEY 생성 방법:**
```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
# 출력된 값을 SECRET_KEY에 복사
```

#### 1.4. MySQL 데이터베이스 생성

```sql
-- MySQL에 접속하여 실행
CREATE DATABASE gym_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 사용자 생성 (선택사항)
CREATE USER 'gym_admin'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON gym_management.* TO 'gym_admin'@'localhost';
FLUSH PRIVILEGES;
```

**테이블 스키마 예시** (프로젝트에 맞게 조정):
```sql
USE gym_management;

-- 회원 테이블
CREATE TABLE members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    membership_type VARCHAR(50),
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 출입 기록 테이블
CREATE TABLE checkins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE
);

-- 관리자 테이블 (선택사항)
CREATE TABLE admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 1.5. 백엔드 서버 실행

```powershell
# Back 폴더에서 실행
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**서버 실행 확인:**
- API 문서: http://localhost:8000/api/docs
- 상태 확인: http://localhost:8000/

---

### 2. 프론트엔드 설정

#### 2.1. 의존성 설치

```powershell
# Front 폴더로 이동
cd Front

# npm 패키지 설치
npm install
```

#### 2.2. 환경 변수 설정

**`.env` 파일 생성** (`Front/.env`)

```env
# 백엔드 API URL
VITE_API_BASE_URL=http://localhost:8000/api
```

#### 2.3. 프론트엔드 개발 서버 실행

```powershell
# Front 폴더에서 실행
npm run dev
```

**서버 실행 확인:**
- 키오스크: http://localhost:5173/kiosk
- 관리자: http://localhost:5173/admin

#### 2.4. 프로덕션 빌드 (배포용)

```powershell
npm run build

# 빌드 결과 미리보기
npm run preview
```

---

## 📡 API 엔드포인트

### 키오스크 API (인증 불필요)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/checkin` | 전화번호 뒷자리로 출입 체크 |

**요청 예시:**
```json
POST /api/checkin
{
  "phone_last_four": "5678"
}
```

**응답 예시 (성공):**
```json
{
  "status": "success",
  "message": "홍길동님 환영합니다! 😊",
  "member": {
    "id": 1,
    "name": "홍길동"
  }
}
```

**응답 예시 (실패):**
```json
{
  "detail": "등록된 회원을 찾을 수 없습니다. 프론트 데스크에 문의하세요."
}
```

### 관리자 API (JWT 인증 필요)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/admin/login` | 관리자 로그인 |
| GET | `/api/admin/members` | 회원 목록 조회 (페이지네이션, 검색, 필터) |
| POST | `/api/admin/members` | 회원 추가 |
| PUT | `/api/admin/members/{id}` | 회원 정보 수정 |
| DELETE | `/api/admin/members/{id}` | 회원 삭제 |
| GET | `/api/admin/members/{id}/checkins` | 회원 출입 기록 조회 |

**로그인 요청:**
```json
POST /api/admin/login
{
  "password": "1234"
}
```

**로그인 응답:**
```json
{
  "status": "success",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "message": "로그인 성공"
}
```

**회원 목록 조회:**
```
GET /api/admin/members?page=1&size=20&search=홍길동&status=active
Authorization: Bearer {token}
```

**회원 추가:**
```json
POST /api/admin/members
Authorization: Bearer {token}
{
  "name": "홍길동",
  "phone_number": "010-1234-5678",
  "membership_type": "3개월",
  "membership_start_date": "2025-01-01",
  "membership_end_date": "2025-04-01"
}
```

---

## 🔧 트러블슈팅

### 1. 백엔드 실행 실패

#### 에러: `ValidationError: DB_PASSWORD Field required`

**원인**: `.env` 파일이 없거나 필수 환경 변수가 누락됨

**해결 방법:**
```powershell
# Back/.env 파일 생성 및 필수 값 입력
# - DB_PASSWORD: MySQL 비밀번호
# - SECRET_KEY: JWT 시크릿 키 (랜덤 생성)

# SECRET_KEY 생성
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 에러: `Can't connect to MySQL server`

**원인**: MySQL 서버가 실행 중이지 않거나 연결 정보가 잘못됨

**해결 방법:**
1. MySQL 서버 실행 확인
   ```powershell
   # Windows: MySQL 서비스 확인
   Get-Service -Name MySQL*
   ```

2. `.env` 파일의 DB 설정 확인
   - `DB_HOST`: localhost
   - `DB_PORT`: 3306 (기본값)
   - `DB_USER`: 사용자명
   - `DB_PASSWORD`: 비밀번호
   - `DB_NAME`: gym_management

3. 데이터베이스 생성 확인
   ```sql
   SHOW DATABASES LIKE 'gym_management';
   ```

#### 에러: `ModuleNotFoundError: No module named 'XXX'`

**원인**: Python 패키지가 설치되지 않음

**해결 방법:**
```powershell
# 가상환경 활성화 확인
.\.venv\Scripts\Activate.ps1

# 의존성 재설치
pip install -r requirements.txt
```

---

### 2. 프론트엔드 실행 실패

#### 에러: `'react' 모듈 또는 해당 형식 선언을 찾을 수 없습니다` (TS2307)

**원인**: `node_modules`가 설치되지 않았거나 TypeScript 설정 문제

**해결 방법:**
```powershell
# 1. node_modules 삭제 후 재설치
rm -r node_modules
rm package-lock.json
npm install

# 2. TypeScript 서버 재시작 (VS Code)
# Ctrl+Shift+P → "TypeScript: Restart TS Server"

# 3. 여전히 에러 시 tsconfig.json 확인
# types 항목에 "react", "react-dom" 추가
```

#### 에러: `VITE_API_BASE_URL is not defined`

**원인**: `.env` 파일이 없거나 환경 변수가 누락됨

**해결 방법:**
```powershell
# Front/.env 파일 생성
echo "VITE_API_BASE_URL=http://localhost:8000/api" > .env

# 개발 서버 재시작
npm run dev
```

#### 에러: `Network Error` 또는 CORS 에러

**원인**: 백엔드 서버가 실행 중이지 않거나 CORS 설정 문제

**해결 방법:**
1. 백엔드 서버 실행 확인
   ```powershell
   # 백엔드가 8000 포트에서 실행 중인지 확인
   curl http://localhost:8000/
   ```

2. CORS 설정 확인 (`Back/app/main.py`)
   - `allow_origins=["*"]` 설정 확인
   - 프로덕션 환경에서는 구체적인 도메인 지정 권장

3. `.env`의 API URL 확인
   - `VITE_API_BASE_URL=http://localhost:8000/api`

---

### 3. 데이터베이스 문제

#### 에러: `Table 'gym_management.members' doesn't exist`

**원인**: 데이터베이스 테이블이 생성되지 않음

**해결 방법:**
```sql
-- MySQL에 접속하여 테이블 생성 스크립트 실행
-- (위의 "MySQL 데이터베이스 생성" 섹션 참조)
```

#### 에러: `Access denied for user 'gym_admin'@'localhost'`

**원인**: MySQL 사용자 권한 문제

**해결 방법:**
```sql
-- MySQL root 계정으로 접속하여 실행
GRANT ALL PRIVILEGES ON gym_management.* TO 'gym_admin'@'localhost';
FLUSH PRIVILEGES;
```

---

### 4. 실행 흐름 확인

#### 전체 시스템이 정상 동작하는지 확인하는 방법:

1. **백엔드 상태 확인**
   ```powershell
   # Back 폴더에서
   curl http://localhost:8000/
   # 응답: {"status": "running", ...}
   ```

2. **API 문서 확인**
   - 브라우저에서 http://localhost:8000/api/docs 접속
   - Swagger UI에서 API 테스트 가능

3. **프론트엔드 접속**
   - 키오스크: http://localhost:5173/kiosk
   - 관리자: http://localhost:5173/admin

4. **End-to-End 테스트**
   - 키오스크에서 전화번호 뒷자리 입력 → 출입 체크
   - 관리자 페이지 로그인 → 회원 목록 확인

---

## 🌐 배포 가이드

### 프론트엔드 배포 (Vercel/Netlify)

```powershell
# 프로덕션 빌드
cd Front
npm run build

# dist 폴더가 생성됨 → 정적 호스팅 서비스에 업로드
```

**환경 변수 설정** (Vercel/Netlify 대시보드):
- `VITE_API_BASE_URL`: `https://your-backend-api.com/api`

### 백엔드 배포 (AWS/Heroku/Railway)

```powershell
# requirements.txt 확인
pip freeze > requirements.txt

# .env 파일은 배포 환경에서 환경 변수로 설정
# (소스코드에 포함하지 말 것)
```

**환경 변수 설정** (배포 플랫폼):
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `SECRET_KEY`
- `DEFAULT_ADMIN_PASSWORD`

**Uvicorn 실행 명령**:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---