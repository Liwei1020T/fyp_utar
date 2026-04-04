from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_customer
from app.api.deps.auth import get_current_user
from app.api.responses import success_response
from app.core.constants import UserRole
from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.schemas.booking import BookingPayload
from app.services.booking_service import booking_service


router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("")
def create_booking(
    payload: BookingPayload,
    user: dict = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> dict:
    booking = booking_service.create(
        db,
        customer_user_id=user["sub"],
        payload=payload.model_dump(exclude_none=True),
    )
    return success_response(message="Booking created successfully", data=booking)


@router.get("/me")
def get_my_bookings(
    user: dict = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(
        message="Bookings fetched successfully",
        data=booking_service.list_for_customer(db, user["sub"]),
    )


@router.get("/{booking_id}")
def get_booking_detail(
    booking_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if user.get("role") == UserRole.ADMIN.value:
        booking = booking_service.get_by_id(db, booking_id)
    else:
        booking = booking_service.get_for_customer(db, booking_id, user["sub"])

    if booking is None:
        raise NotFoundError("Booking not found")

    return success_response(message="Booking fetched successfully", data=booking)
