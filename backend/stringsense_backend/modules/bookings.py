from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from stringsense_backend.api.dependencies import CurrentUser
from stringsense_backend.api.dependencies import get_current_customer
from stringsense_backend.core.domain import BOOKING_STATUS_TRANSITIONS
from stringsense_backend.core.domain import BookingStatus
from stringsense_backend.core.domain import UserRole
from stringsense_backend.core.errors import ConflictError
from stringsense_backend.core.errors import NotFoundError
from stringsense_backend.core.http import page_response
from stringsense_backend.core.serialization import decimal_to_float
from stringsense_backend.core.serialization import isoformat_or_none
from stringsense_backend.db.models import Booking
from stringsense_backend.db.models import BookingStatusHistory
from stringsense_backend.db.models import StringCatalogItem
from stringsense_backend.db.models import User
from stringsense_backend.db.session import get_db


router = APIRouter(prefix="/bookings", tags=["bookings"])

BookingSortField = Literal["created_at", "updated_at", "status", "drop_off_datetime"]
SortOrder = Literal["asc", "desc"]


class CreateBookingPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    string_id: str
    racket_brand: str | None = None
    racket_model: str | None = None
    requested_tension: float | None = Field(default=None, ge=16, le=35)
    drop_off_datetime: datetime | None = None
    notes: str | None = None


class UpdateBookingStatusPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(
        pattern="^(awaiting_dropoff|in_progress|ready_for_collection|completed|cancelled|rejected)$"
    )
    note: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_terminal_note(self) -> "UpdateBookingStatusPayload":
        if self.status in {
            BookingStatus.CANCELLED.value,
            BookingStatus.REJECTED.value,
        } and not (self.note and self.note.strip()):
            raise ValueError("note is required when cancelling or rejecting a booking")
        return self


class BookingStatusHistoryOut(BaseModel):
    old_status: str | None
    new_status: str
    changed_by_user_id: str | None
    changed_by_phone_number: str | None
    note: str | None
    changed_at: str | None


class BookingOut(BaseModel):
    id: str
    user_id: str
    string_id: str
    string_name: str
    customer_phone_number: str | None = None
    customer_username: str | None = None
    racket_brand: str | None = None
    racket_model: str | None = None
    requested_tension: float | None = None
    drop_off_datetime: str | None = None
    notes: str | None = None
    status: str
    created_at: str | None = None
    updated_at: str | None = None
    latest_admin_note: str | None = None
    status_history: list[BookingStatusHistoryOut] | None = None


def serialize_booking(
    booking: Booking, *, include_user: bool, include_history: bool
) -> BookingOut:
    latest_admin_note = next(
        (
            entry.note
            for entry in reversed(booking.status_history)
            if entry.note and entry.note.strip()
        ),
        None,
    )
    return BookingOut(
        id=booking.id,
        user_id=booking.user_id,
        string_id=booking.string_id,
        string_name=f"{booking.string_item.brand} {booking.string_item.model_name}",
        customer_phone_number=booking.user.phone_number if include_user else None,
        customer_username=booking.user.username if include_user else None,
        racket_brand=booking.racket_brand,
        racket_model=booking.racket_model,
        requested_tension=decimal_to_float(booking.requested_tension),
        drop_off_datetime=isoformat_or_none(booking.drop_off_datetime),
        notes=booking.notes,
        status=booking.status,
        created_at=isoformat_or_none(booking.created_at),
        updated_at=isoformat_or_none(booking.updated_at),
        latest_admin_note=latest_admin_note,
        status_history=[
            BookingStatusHistoryOut(
                old_status=entry.old_status,
                new_status=entry.new_status,
                changed_by_user_id=entry.changed_by_user_id,
                changed_by_phone_number=entry.changed_by.phone_number
                if entry.changed_by
                else None,
                note=entry.note,
                changed_at=isoformat_or_none(entry.changed_at),
            )
            for entry in booking.status_history
        ]
        if include_history
        else None,
    )


def get_booking_or_404(db: Session, booking_id: str) -> Booking:
    booking = (
        db.execute(
            select(Booking)
            .where(Booking.id == booking_id)
            .options(
                joinedload(Booking.string_item),
                joinedload(Booking.user),
                joinedload(Booking.status_history).joinedload(
                    BookingStatusHistory.changed_by
                ),
            )
        )
        .unique()
        .scalar_one_or_none()
    )
    if booking is None:
        raise NotFoundError("Booking not found")
    return booking


def assert_booking_status_transition(current_status: str, next_status: str) -> None:
    current = BookingStatus(current_status)
    requested = BookingStatus(next_status)
    if requested not in BOOKING_STATUS_TRANSITIONS[current]:
        raise ConflictError("Invalid booking status transition")


def list_admin_bookings(
    db: Session,
    *,
    status: str | None,
    search: str | None,
    sort_by: BookingSortField,
    sort_order: SortOrder,
    limit: int | None,
    offset: int,
) -> dict[str, object]:
    query = select(Booking).options(
        joinedload(Booking.string_item),
        joinedload(Booking.user),
        joinedload(Booking.status_history).joinedload(BookingStatusHistory.changed_by),
    )
    count_query = select(func.count()).select_from(Booking)

    if status:
        query = query.where(Booking.status == status)
        count_query = count_query.where(Booking.status == status)

    if search:
        term = f"%{search.strip()}%"
        query = query.join(Booking.string_item).join(Booking.user)
        count_query = count_query.join(Booking.string_item).join(Booking.user)
        condition = or_(
            Booking.racket_brand.ilike(term),
            Booking.racket_model.ilike(term),
            StringCatalogItem.brand.ilike(term),
            StringCatalogItem.model_name.ilike(term),
            User.phone_number.ilike(term),
            User.username.ilike(term),
        )
        query = query.where(condition)
        count_query = count_query.where(condition)

    total = db.execute(count_query).scalar_one()
    sort_column = {
        "created_at": Booking.created_at,
        "updated_at": Booking.updated_at,
        "status": Booking.status,
        "drop_off_datetime": Booking.drop_off_datetime,
    }[sort_by]
    if sort_order == "desc":
        query = query.order_by(sort_column.desc(), Booking.created_at.desc())
    else:
        query = query.order_by(sort_column.asc(), Booking.created_at.desc())

    if limit is not None:
        query = query.limit(limit).offset(offset)

    items = db.execute(query).unique().scalars().all()
    return page_response(
        items=[
            serialize_booking(
                item, include_user=True, include_history=True
            ).model_dump()
            for item in items
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=BookingOut)
def create_booking(
    payload: CreateBookingPayload,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> BookingOut:
    string_item = db.execute(
        select(StringCatalogItem).where(StringCatalogItem.id == payload.string_id)
    ).scalar_one_or_none()
    if string_item is None or not string_item.is_active:
        raise NotFoundError("String not found")

    booking = Booking(
        user_id=current_user.user_id,
        string_id=payload.string_id,
        racket_brand=payload.racket_brand,
        racket_model=payload.racket_model,
        requested_tension=payload.requested_tension,
        drop_off_datetime=payload.drop_off_datetime,
        notes=payload.notes,
        status=BookingStatus.AWAITING_DROPOFF.value,
    )
    db.add(booking)
    db.flush()
    db.add(
        BookingStatusHistory(
            booking_id=booking.id,
            old_status=None,
            new_status=BookingStatus.AWAITING_DROPOFF.value,
            changed_by_user_id=current_user.user_id,
        )
    )
    db.commit()
    booking = get_booking_or_404(db, booking.id)
    return serialize_booking(booking, include_user=False, include_history=True)


@router.get("", response_model=dict)
def list_my_bookings(
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    items = (
        db.execute(
            select(Booking)
            .where(Booking.user_id == current_user.user_id)
            .options(
                joinedload(Booking.string_item),
                joinedload(Booking.status_history).joinedload(
                    BookingStatusHistory.changed_by
                ),
                joinedload(Booking.user),
            )
            .order_by(Booking.created_at.desc())
        )
        .unique()
        .scalars()
        .all()
    )
    return page_response(
        items=[
            serialize_booking(
                item, include_user=False, include_history=True
            ).model_dump()
            for item in items
        ],
        total=len(items),
        limit=None,
        offset=0,
    )


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(
    booking_id: str,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> BookingOut:
    booking = get_booking_or_404(db, booking_id)
    if (
        current_user.role == UserRole.CUSTOMER.value
        and booking.user_id != current_user.user_id
    ):
        raise NotFoundError("Booking not found")
    return serialize_booking(
        booking,
        include_user=current_user.role != UserRole.CUSTOMER.value,
        include_history=True,
    )
