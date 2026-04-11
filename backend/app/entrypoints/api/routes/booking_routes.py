from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import Form
from fastapi import UploadFile

from app.domain.auth.entities import UserRole
from app.dto.booking import BookingOut
from app.dto.booking import CreateBookingPayload
from app.dto.booking import booking_to_dto
from app.dto.common import page_to_dict
from app.entrypoints.api.dependencies import CurrentUser
from app.entrypoints.api.dependencies import get_booking_repository
from app.entrypoints.api.dependencies import get_catalog_repository
from app.entrypoints.api.dependencies import get_current_customer
from app.shared.errors import NotFoundError
from app.shared.upload_storage import delete_booking_update_photo
from app.shared.upload_storage import save_booking_update_photo
from app.use_cases.booking.add_booking_update import AddBookingUpdateUseCase
from app.use_cases.booking.create_booking import CreateBookingUseCase
from app.use_cases.booking.get_booking import GetBookingUseCase
from app.use_cases.booking.list_my_bookings import ListMyBookingsUseCase


router = APIRouter(prefix="/bookings", tags=["bookings"])

BookingPhotoType = Literal["racket", "service_progress", "other"]


def get_customer_owned_booking(
    *,
    booking_id: str,
    current_user: CurrentUser,
    booking_repository,
):
    booking = GetBookingUseCase(booking_repository=booking_repository).execute(
        booking_id
    )
    if (
        current_user.role == UserRole.CUSTOMER.value
        and booking.user_id != current_user.user_id
    ):
        raise NotFoundError("Booking not found")
    return booking


@router.post("", response_model=BookingOut)
def create_booking(
    payload: CreateBookingPayload,
    current_user: CurrentUser = Depends(get_current_customer),
    booking_repository=Depends(get_booking_repository),
    catalog_repository=Depends(get_catalog_repository),
) -> BookingOut:
    booking = CreateBookingUseCase(
        booking_repository=booking_repository,
        catalog_repository=catalog_repository,
    ).execute(user_id=current_user.user_id, **payload.model_dump())
    return booking_to_dto(booking, include_user=False, include_history=True)


@router.get("", response_model=dict)
def list_my_bookings(
    current_user: CurrentUser = Depends(get_current_customer),
    booking_repository=Depends(get_booking_repository),
) -> dict[str, object]:
    page = ListMyBookingsUseCase(booking_repository=booking_repository).execute(
        current_user.user_id
    )
    return page_to_dict(
        page,
        lambda item: booking_to_dto(
            item,
            include_user=False,
            include_history=True,
        ).model_dump(),
    )


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(
    booking_id: str,
    current_user: CurrentUser = Depends(get_current_customer),
    booking_repository=Depends(get_booking_repository),
) -> BookingOut:
    booking = get_customer_owned_booking(
        booking_id=booking_id,
        current_user=current_user,
        booking_repository=booking_repository,
    )
    return booking_to_dto(
        booking,
        include_user=current_user.role != UserRole.CUSTOMER.value,
        include_history=True,
    )


@router.post("/{booking_id}/updates", response_model=BookingOut)
async def add_booking_update(
    booking_id: str,
    comment: str | None = Form(default=None),
    photo: UploadFile | None = File(default=None),
    photo_type: BookingPhotoType = Form(default="other"),
    current_user: CurrentUser = Depends(get_current_customer),
    booking_repository=Depends(get_booking_repository),
) -> BookingOut:
    get_customer_owned_booking(
        booking_id=booking_id,
        current_user=current_user,
        booking_repository=booking_repository,
    )
    photo_path = None
    photo_original_name = None
    photo_content_type = None
    if photo is not None:
        photo_content_type = photo.content_type
        photo_original_name = photo.filename
        photo_path = save_booking_update_photo(
            content=await photo.read(),
            content_type=photo.content_type,
            original_name=photo.filename,
        )

    try:
        booking = AddBookingUpdateUseCase(
            booking_repository=booking_repository
        ).execute(
            booking_id=booking_id,
            author_user_id=current_user.user_id,
            author_role=current_user.role,
            comment=comment,
            photo_path=photo_path,
            photo_original_name=photo_original_name,
            photo_content_type=photo_content_type,
            photo_type=photo_type if photo_path else None,
        )
    except Exception:
        delete_booking_update_photo(photo_path)
        raise
    return booking_to_dto(booking, include_user=False, include_history=True)
