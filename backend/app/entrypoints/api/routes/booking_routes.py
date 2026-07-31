from __future__ import annotations

import secrets
from datetime import timedelta
from typing import Literal

from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import Form
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.models import CheckInToken
from app.adapters.persistence.sqlalchemy.session import get_db
from app.domain.auth.entities import UserRole
from app.domain.booking.enums import BookingStatus
from app.domain.store.policies import hash_check_in_token
from app.config.settings import get_settings
from app.dto.booking import BookingOut
from app.dto.booking import CancelBookingPayload
from app.dto.booking import CheckInTokenOut
from app.dto.booking import CreateBookingPayload
from app.dto.booking import booking_to_dto
from app.dto.common import page_to_dict
from app.entrypoints.api.dependencies import CurrentUser
from app.entrypoints.api.dependencies import get_booking_repository
from app.entrypoints.api.dependencies import get_catalog_repository
from app.entrypoints.api.dependencies import get_clock
from app.entrypoints.api.dependencies import get_current_customer
from app.entrypoints.api.dependencies import get_store_repository
from app.entrypoints.api.dependencies import get_transaction_manager
from app.shared.errors import BadRequestError
from app.shared.errors import NotFoundError
from app.shared.upload_storage import MAX_UPLOAD_BYTES
from app.shared.upload_storage import delete_booking_update_photo
from app.shared.upload_storage import save_booking_update_photo
from app.use_cases.booking.add_booking_update import AddBookingUpdateUseCase
from app.use_cases.booking.create_booking import CreateBookingUseCase
from app.use_cases.booking.get_booking import GetBookingUseCase
from app.use_cases.booking.list_my_bookings import ListMyBookingsUseCase
from app.use_cases.booking.update_booking_status import UpdateBookingStatusUseCase
from app.shared.errors import ConflictError


router = APIRouter(prefix="/bookings", tags=["bookings"])

BookingPhotoType = Literal["racket", "service_progress", "other"]


async def read_upload_bytes_limited(photo: UploadFile) -> bytes:
    total_size = 0
    chunks: list[bytes] = []
    while True:
        chunk = await photo.read(512 * 1024)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > MAX_UPLOAD_BYTES:
            raise BadRequestError("Uploaded photo must be 5 MB or smaller")
        chunks.append(chunk)
    return b"".join(chunks)


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
    store_repository=Depends(get_store_repository),
    clock=Depends(get_clock),
) -> BookingOut:
    booking = CreateBookingUseCase(
        booking_repository=booking_repository,
        catalog_repository=catalog_repository,
        store_repository=store_repository,
        clock=clock,
        store_timezone=get_settings().store_timezone,
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


@router.post("/{booking_id}/cancel", response_model=BookingOut)
def cancel_booking(
    booking_id: str,
    payload: CancelBookingPayload,
    current_user: CurrentUser = Depends(get_current_customer),
    booking_repository=Depends(get_booking_repository),
    transaction_manager=Depends(get_transaction_manager),
) -> BookingOut:
    booking = get_customer_owned_booking(
        booking_id=booking_id,
        current_user=current_user,
        booking_repository=booking_repository,
    )
    if booking.user_id != current_user.user_id:
        raise NotFoundError("Booking not found")
    updated = UpdateBookingStatusUseCase(
        booking_repository=booking_repository,
        transaction_manager=transaction_manager,
    ).execute(
        booking_id=booking.id,
        next_status=BookingStatus.CANCELLED.value,
        expected_completion_datetime=None,
        update_expected_completion_datetime=False,
        changed_by_user_id=current_user.user_id,
        note=payload.reason,
    )
    return booking_to_dto(updated, include_user=False, include_history=True)


@router.post("/{booking_id}/check-in-token", response_model=CheckInTokenOut)
def create_check_in_token(
    booking_id: str,
    current_user: CurrentUser = Depends(get_current_customer),
    booking_repository=Depends(get_booking_repository),
    clock=Depends(get_clock),
    db: Session = Depends(get_db),
) -> CheckInTokenOut:
    booking = booking_repository.get_by_id_for_update(booking_id)
    if booking is None or booking.user_id != current_user.user_id:
        raise NotFoundError("Booking not found")
    if booking.status != BookingStatus.AWAITING_DROPOFF.value:
        raise ConflictError("Check-in QR is only available before drop-off")

    now = clock.now()
    active_tokens = db.scalars(
        select(CheckInToken).where(
            CheckInToken.booking_id == booking.id,
            CheckInToken.used_at.is_(None),
            CheckInToken.revoked_at.is_(None),
        )
    ).all()
    for active_token in active_tokens:
        active_token.revoked_at = now

    raw_token = f"SSQR.{secrets.token_urlsafe(32)}"
    expires_at = now + timedelta(minutes=10)
    db.add(
        CheckInToken(
            booking_id=booking.id,
            token_hash=hash_check_in_token(raw_token),
            expires_at=expires_at,
        )
    )
    db.commit()
    return CheckInTokenOut(
        token=raw_token,
        expires_at=expires_at.isoformat(),
        status="active",
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
        photo_content = await read_upload_bytes_limited(photo)
        photo_path = save_booking_update_photo(
            content=photo_content,
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
