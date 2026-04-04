from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_admin
from app.api.responses import paginated_success_response
from app.api.responses import success_response
from app.core.constants import BookingStatus
from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.schemas.query import AdminBookingSortField
from app.schemas.query import SortOrder
from app.schemas.booking import BookingStatusPayload
from app.services.booking_service import booking_service


router = APIRouter(prefix="/admin/bookings", tags=["admin-bookings"])


@router.get("")
def list_bookings(
    status: BookingStatus | None = Query(default=None),
    search: str | None = Query(default=None, max_length=100),
    sort_by: AdminBookingSortField = Query(default=AdminBookingSortField.CREATED_AT),
    sort_order: SortOrder = Query(default=SortOrder.DESC),
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict:
    items, total = booking_service.list_all(
        db,
        status=status,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )
    return paginated_success_response(
        message="Admin bookings fetched successfully",
        data=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{booking_id}")
def get_booking_detail(
    booking_id: str,
    user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict:
    booking = booking_service.get_by_id(db, booking_id)
    if booking is None:
        raise NotFoundError("Booking not found")

    return success_response(
        message="Admin booking fetched successfully",
        data=booking,
    )


@router.patch("/{booking_id}/status")
def update_booking_status(
    booking_id: str,
    payload: BookingStatusPayload,
    user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict:
    booking = booking_service.update_status(
        db,
        booking_id,
        payload.status,
        changed_by_user_id=user["sub"],
    )
    if booking is None:
        raise NotFoundError("Booking not found")

    return success_response(message="Booking updated successfully", data=booking)
