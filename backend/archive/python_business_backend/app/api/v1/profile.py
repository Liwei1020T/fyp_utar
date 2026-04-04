from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_customer
from app.api.responses import success_response
from app.db.session import get_db
from app.schemas.profile import ProfilePayload
from app.services.profile_service import profile_service


router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me")
def get_my_profile(
    user: dict = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(
        message="Profile fetched successfully",
        data=profile_service.get(db, user["sub"]),
    )


@router.post("/me")
def create_my_profile(
    payload: ProfilePayload,
    user: dict = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> dict:
    data = profile_service.save(db, user["sub"], payload)
    return success_response(message="Profile saved successfully", data=data)


@router.put("/me")
def update_my_profile(
    payload: ProfilePayload,
    user: dict = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> dict:
    data = profile_service.save(db, user["sub"], payload)
    return success_response(message="Profile updated successfully", data=data)
