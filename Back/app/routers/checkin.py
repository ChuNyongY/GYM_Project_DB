from fastapi import APIRouter, Depends, Query
from typing import Dict, Optional, Any
from ..database import get_db
from ..services.member_service import MemberService
from ..services.checkin_service import CheckInService
from ..utils.security import oauth2_scheme

router = APIRouter(prefix="/api/checkin", tags=["checkin"])

@router.get("/today")
async def get_today_checkins(
    page: int = Query(1, gt=0),
    size: int = Query(50, gt=0),
    db = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Dict:
    checkin_service = CheckInService(db)
    checkins, total = checkin_service.get_today_checkins(page, size)

    return {
        "total": total,
        "page": page,
        "size": size,
        "checkins": checkins
    }

@router.put("/{checkin_id}/checkout")
async def process_checkout(
    checkin_id: int,
    db = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Dict:
    checkin_service = CheckInService(db)
    return checkin_service.process_checkout(checkin_id)

@router.get("/member/{member_id}")
async def get_member_checkins(
    member_id: int,
    year: int = Query(...),
    month: int = Query(...),
    db = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Dict:
    checkin_service = CheckInService(db)
    checkins = checkin_service.get_member_checkins(member_id, year, month)

    return {
        "member_id": member_id,
        "year": year,
        "month": month,
        "total_checkins": len(checkins),
        "checkins": checkins
    }