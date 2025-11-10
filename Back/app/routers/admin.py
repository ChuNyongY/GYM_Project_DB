from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from ..database import get_db
from ..services.admin_service import AdminService
from ..schemas.admin import AdminCreate, AdminUpdate
from ..utils.security import oauth2_scheme

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.post("/login")
def admin_login(
    password: str,
    db = Depends(get_db)
) -> Dict:
    admin_service = AdminService(db)
    return admin_service.verify_admin(password)

@router.put("/change-password")
async def change_admin_password(
    update_data: AdminUpdate,
    db = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Dict:
    admin_service = AdminService(db)
    await admin_service.get_current_admin(token)
    
    return admin_service.change_password(
        update_data.current_password,
        update_data.new_password
    )