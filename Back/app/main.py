from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .routers import kiosk, admin, members, rentals, checkin, deleted_members
from .database import get_connection

# 설정 로드
settings = get_settings()

# 애플리케이션 생성
app = FastAPI(
    title="GYM Management System",
    description="헬스장 회원 관리 및 출입 시스템 API",
    version="1.0.0",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 구체적인 도메인 지정
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(kiosk.router, prefix=f"{settings.API_PREFIX}/kiosk", tags=["Kiosk"])
app.include_router(admin.router, prefix=f"{settings.API_PREFIX}/admin", tags=["Admin"])
app.include_router(members.router, prefix=f"{settings.API_PREFIX}/members", tags=["Members"])
app.include_router(rentals.router, prefix=f"{settings.API_PREFIX}/rentals", tags=["Rentals"])
app.include_router(checkin.router, prefix=f"{settings.API_PREFIX}/checkin", tags=["Check-in"])
app.include_router(deleted_members.router, prefix=f"{settings.API_PREFIX}/deleted-members", tags=["Deleted Members"])

# 상태 확인 엔드포인트
@app.get("/")
async def root():
    return {
        "status": "running",
        "message": "GYM Management System API",
        "version": "1.0.0"
    }