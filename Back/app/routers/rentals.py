from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any
from ..database import get_db
from ..services.rental_service import RentalService
from ..schemas.locker_rental import LockerRentalCreate, LockerRentalResponse
from ..schemas.uniform_rental import UniformRentalCreate, UniformRentalResponse
from ..utils.security import oauth2_scheme

router = APIRouter(prefix="/api/rentals", tags=["rentals"])

@router.post("/locker/{member_id}/extend")
async def extend_locker_rental(
    member_id: int,
    rental_type: str,
    db = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Dict:
    rental_service = RentalService(db)
    return rental_service.extend_locker_rental(member_id, rental_type)

@router.post("/uniform/{member_id}/extend")
async def extend_uniform_rental(
    member_id: int,
    rental_type: str,
    db = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Dict:
    rental_service = RentalService(db)
    return rental_service.extend_uniform_rental(member_id, rental_type)

@router.get("/lockers/available")
async def get_available_lockers(
    db = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Dict:
    rental_service = RentalService(db)
    return rental_service.get_available_lockers()