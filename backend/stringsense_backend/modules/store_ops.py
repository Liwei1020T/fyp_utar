from __future__ import annotations

from collections import Counter
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from datetime import timezone
from typing import Literal

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from stringsense_backend.api.dependencies import CurrentUser
from stringsense_backend.api.dependencies import get_current_admin
from stringsense_backend.api.dependencies import get_current_customer
from stringsense_backend.core.domain import BookingStatus
from stringsense_backend.core.errors import ConflictError
from stringsense_backend.core.errors import NotFoundError
from stringsense_backend.core.http import page_response
from stringsense_backend.core.serialization import decimal_to_float
from stringsense_backend.core.serialization import isoformat_or_none
from stringsense_backend.db.models import Booking
from stringsense_backend.db.models import BookingStatusHistory
from stringsense_backend.db.models import StoreBusinessHours
from stringsense_backend.db.models import StoreSettings
from stringsense_backend.db.models import StringCatalogItem
from stringsense_backend.db.session import get_db
from stringsense_backend.modules.bookings import BookingOut
from stringsense_backend.modules.bookings import assert_booking_status_transition
from stringsense_backend.modules.bookings import get_booking_or_404
from stringsense_backend.modules.bookings import serialize_booking
from stringsense_backend.modules.strings import inventory_availability


admin_router = APIRouter(prefix="/admin", tags=["admin"])
public_router = APIRouter(tags=["store"])

STORE_ID = "main"
ACTIVE_QUEUE_STATUSES = (
    BookingStatus.AWAITING_DROPOFF.value,
    BookingStatus.IN_PROGRESS.value,
    BookingStatus.READY_FOR_COLLECTION.value,
)


class BusinessHoursDayPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    day: Literal[
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    is_open: bool
    open_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    close_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    break_start: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    break_end: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    slot_duration_minutes: int = Field(ge=15, le=180)
    max_bookings_per_slot: int = Field(ge=1, le=20)

    @model_validator(mode="after")
    def validate_day_window(self) -> "BusinessHoursDayPayload":
        open_time = parse_hhmm(self.open_time)
        close_time = parse_hhmm(self.close_time)
        if open_time >= close_time:
            raise ValueError("open_time must be earlier than close_time")
        if self.break_start and self.break_end:
            break_start = parse_hhmm(self.break_start)
            break_end = parse_hhmm(self.break_end)
            if break_start >= break_end:
                raise ValueError("break_start must be earlier than break_end")
        return self


class StoreBusinessHoursPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    days: list[BusinessHoursDayPayload]
    special_closed_dates: list[str]

    @model_validator(mode="after")
    def validate_unique_days(self) -> "StoreBusinessHoursPayload":
        if len({day.day for day in self.days}) != len(self.days):
            raise ValueError("Each weekday may only appear once")
        return self


class StoreBusinessHoursOut(StoreBusinessHoursPayload):
    id: str = STORE_ID
    updated_at: str | None = None


class BookingSlotOut(BaseModel):
    id: str
    date: str
    time: str
    capacity: int
    booked_count: int
    available_spots: int
    label: str
    day_label: str


class CheckInLookupOut(BaseModel):
    matched_by: Literal["booking_id", "check_in_reference"]
    booking: BookingOut


class CheckInPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    booking_id: str | None = None
    reference: str | None = None
    note: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_lookup_input(self) -> "CheckInPayload":
        if bool(self.booking_id) == bool(self.reference):
            raise ValueError("Provide exactly one of booking_id or reference")
        return self


class ServiceQueueItemOut(BaseModel):
    queue_position: int
    booking: BookingOut


class ServiceQueueLaneOut(BaseModel):
    status: str
    title: str
    items: list[ServiceQueueItemOut]


class ServiceQueueOut(BaseModel):
    generated_at: str
    lanes: list[ServiceQueueLaneOut]


class StoreSettingsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    store_name: str = Field(min_length=1, max_length=120)
    store_contact: str = Field(min_length=1, max_length=120)
    support_text: str = Field(min_length=1, max_length=2000)
    payment_notes: str = Field(min_length=1, max_length=2000)
    booking_notes: str = Field(min_length=1, max_length=2000)
    store_policy_text: str = Field(min_length=1, max_length=2000)
    address: str = Field(min_length=1, max_length=500)


class StoreSettingsOut(StoreSettingsPayload):
    id: str = STORE_ID
    updated_at: str | None = None


class AnalyticsWorkloadEntryOut(BaseModel):
    label: str
    value: int


class AnalyticsSummaryOut(BaseModel):
    weekly_bookings: int
    pending_payment_count: int
    awaiting_dropoff_count: int
    in_progress_count: int
    ready_for_collection_count: int
    completed_today: int
    low_stock_count: int
    unread_chats: int
    today_revenue: float
    busy_slots: list[str]
    popular_string_ids: list[str]
    workload_mix: list[AnalyticsWorkloadEntryOut]


class PopularStringOut(BaseModel):
    string_id: str
    brand: str
    model_name: str
    booking_count: int


def parse_hhmm(value: str) -> time:
    return time.fromisoformat(value)


def booking_check_in_reference(booking: Booking) -> str:
    return f"CHK-{booking.id[:8].upper()}"


def weekday_name(target_date: date) -> str:
    return target_date.strftime("%A")


def slot_label(slot_time: str) -> str:
    return datetime.strptime(slot_time, "%H:%M").strftime("%-I:%M %p")


def slot_busy_label(target_date: date, slot_time: str) -> str:
    return f"{target_date.strftime('%a')} {datetime.strptime(slot_time, '%H:%M').strftime('%-I %p')}"


def normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def get_store_business_hours(db: Session) -> StoreBusinessHours:
    hours = db.get(StoreBusinessHours, STORE_ID)
    if hours is None:
        raise NotFoundError("Store business hours not found")
    return hours


def get_store_settings(db: Session) -> StoreSettings:
    settings = db.get(StoreSettings, STORE_ID)
    if settings is None:
        raise NotFoundError("Store settings not found")
    return settings


def serialize_store_business_hours(hours: StoreBusinessHours) -> StoreBusinessHoursOut:
    return StoreBusinessHoursOut(
        id=hours.id,
        days=hours.days_json,
        special_closed_dates=hours.special_closed_dates,
        updated_at=isoformat_or_none(hours.updated_at),
    )


def serialize_store_settings(settings: StoreSettings) -> StoreSettingsOut:
    return StoreSettingsOut(
        id=settings.id,
        store_name=settings.store_name,
        store_contact=settings.store_contact,
        support_text=settings.support_text,
        payment_notes=settings.payment_notes,
        booking_notes=settings.booking_notes,
        store_policy_text=settings.store_policy_text,
        address=settings.address,
        updated_at=isoformat_or_none(settings.updated_at),
    )


def bookings_for_slot_generation(db: Session) -> list[Booking]:
    return (
        db.execute(
            select(Booking).where(
                Booking.drop_off_datetime.is_not(None),
                Booking.status.not_in(
                    [BookingStatus.CANCELLED.value, BookingStatus.REJECTED.value]
                ),
            )
        )
        .scalars()
        .all()
    )


def slots_for_date(
    *,
    target_date: date,
    hours: StoreBusinessHours,
    bookings: list[Booking],
) -> list[BookingSlotOut]:
    day_name = weekday_name(target_date)
    day_config = next(
        (day for day in hours.days_json if day.get("day") == day_name),
        None,
    )
    if day_config is None or not day_config.get("is_open", False):
        return []
    if target_date.isoformat() in hours.special_closed_dates:
        return []

    open_time = parse_hhmm(str(day_config["open_time"]))
    close_time = parse_hhmm(str(day_config["close_time"]))
    break_start = (
        parse_hhmm(str(day_config["break_start"]))
        if day_config.get("break_start")
        else None
    )
    break_end = (
        parse_hhmm(str(day_config["break_end"]))
        if day_config.get("break_end")
        else None
    )
    capacity = int(day_config["max_bookings_per_slot"])
    duration = timedelta(minutes=int(day_config["slot_duration_minutes"]))
    current = datetime.combine(target_date, open_time)
    closing = datetime.combine(target_date, close_time)
    break_start_dt = (
        datetime.combine(target_date, break_start) if break_start is not None else None
    )
    break_end_dt = (
        datetime.combine(target_date, break_end) if break_end is not None else None
    )

    booked_counter: Counter[str] = Counter()
    for booking in bookings:
        drop_off = normalize_datetime(booking.drop_off_datetime)
        if drop_off is None or drop_off.date() != target_date:
            continue
        booked_counter[drop_off.strftime("%H:%M")] += 1

    items: list[BookingSlotOut] = []
    while current + duration <= closing:
        slot_end = current + duration
        if (
            break_start_dt is not None
            and break_end_dt is not None
            and current < break_end_dt
            and slot_end > break_start_dt
        ):
            current += duration
            continue

        slot_time = current.strftime("%H:%M")
        booked_count = booked_counter[slot_time]
        items.append(
            BookingSlotOut(
                id=f"slot-{target_date.isoformat()}-{slot_time}",
                date=target_date.isoformat(),
                time=slot_time,
                capacity=capacity,
                booked_count=booked_count,
                available_spots=max(0, capacity - booked_count),
                label=slot_label(slot_time),
                day_label=day_name,
            )
        )
        current += duration

    return items


def resolve_lookup_booking(
    *,
    db: Session,
    booking_id: str | None,
    reference: str | None,
) -> tuple[Literal["booking_id", "check_in_reference"], Booking]:
    if booking_id:
        return "booking_id", get_booking_or_404(db, booking_id)

    assert reference is not None
    normalized_reference = reference.strip().upper()
    bookings = (
        db.execute(
            select(Booking).options(
                joinedload(Booking.string_item),
                joinedload(Booking.user),
                joinedload(Booking.status_history).joinedload(
                    BookingStatusHistory.changed_by
                ),
            )
        )
        .unique()
        .scalars()
        .all()
    )
    for booking in bookings:
        if (
            booking.id.upper() == normalized_reference
            or booking_check_in_reference(booking) == normalized_reference
        ):
            return "check_in_reference", booking
    raise NotFoundError("Booking not found")


def active_queue_bookings(db: Session) -> list[Booking]:
    return (
        db.execute(
            select(Booking)
            .where(Booking.status.in_(ACTIVE_QUEUE_STATUSES))
            .options(
                joinedload(Booking.string_item),
                joinedload(Booking.user),
                joinedload(Booking.status_history).joinedload(
                    BookingStatusHistory.changed_by
                ),
            )
            .order_by(Booking.drop_off_datetime.asc(), Booking.created_at.asc())
        )
        .unique()
        .scalars()
        .all()
    )


def build_service_queue(db: Session) -> ServiceQueueOut:
    bookings = active_queue_bookings(db)
    lanes: list[ServiceQueueLaneOut] = []
    for status, title in (
        (BookingStatus.AWAITING_DROPOFF.value, "Awaiting drop-off"),
        (BookingStatus.IN_PROGRESS.value, "In progress"),
        (BookingStatus.READY_FOR_COLLECTION.value, "Ready for collection"),
    ):
        lane_bookings = [booking for booking in bookings if booking.status == status]
        lanes.append(
            ServiceQueueLaneOut(
                status=status,
                title=title,
                items=[
                    ServiceQueueItemOut(
                        queue_position=index + 1,
                        booking=serialize_booking(
                            booking,
                            include_user=True,
                            include_history=True,
                        ),
                    )
                    for index, booking in enumerate(lane_bookings)
                ],
            )
        )
    return ServiceQueueOut(
        generated_at=datetime.now(timezone.utc).isoformat(),
        lanes=lanes,
    )


def analytics_summary(db: Session) -> AnalyticsSummaryOut:
    bookings = (
        db.execute(select(Booking).options(joinedload(Booking.string_item)))
        .unique()
        .scalars()
        .all()
    )
    strings = db.execute(select(StringCatalogItem)).scalars().all()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    week_ago = now - timedelta(days=7)
    today = now.date()

    weekly_bookings = 0
    awaiting_dropoff_count = 0
    in_progress_count = 0
    ready_for_collection_count = 0
    completed_today = 0
    today_revenue = 0.0
    slot_counter: Counter[str] = Counter()
    string_counter: Counter[str] = Counter()

    for booking in bookings:
        created_at = normalize_datetime(booking.created_at)
        updated_at = normalize_datetime(booking.updated_at)
        if created_at is not None and created_at >= week_ago:
            weekly_bookings += 1

        if booking.status == BookingStatus.AWAITING_DROPOFF.value:
            awaiting_dropoff_count += 1
        elif booking.status == BookingStatus.IN_PROGRESS.value:
            in_progress_count += 1
        elif booking.status == BookingStatus.READY_FOR_COLLECTION.value:
            ready_for_collection_count += 1
        elif (
            booking.status == BookingStatus.COMPLETED.value
            and updated_at is not None
            and updated_at.date() == today
        ):
            completed_today += 1
            today_revenue += decimal_to_float(booking.string_item.price_rm) or 0.0

        if booking.status not in {
            BookingStatus.CANCELLED.value,
            BookingStatus.REJECTED.value,
        }:
            string_counter[booking.string_id] += 1
            drop_off = normalize_datetime(booking.drop_off_datetime)
            if drop_off is not None:
                slot_counter[
                    slot_busy_label(drop_off.date(), drop_off.strftime("%H:%M"))
                ] += 1

    low_stock_count = sum(
        1 for item in strings if inventory_availability(item) == "low_stock"
    )
    popular_string_ids = [string_id for string_id, _ in string_counter.most_common(3)]

    return AnalyticsSummaryOut(
        weekly_bookings=weekly_bookings,
        pending_payment_count=0,
        awaiting_dropoff_count=awaiting_dropoff_count,
        in_progress_count=in_progress_count,
        ready_for_collection_count=ready_for_collection_count,
        completed_today=completed_today,
        low_stock_count=low_stock_count,
        unread_chats=0,
        today_revenue=round(today_revenue, 2),
        busy_slots=[label for label, _ in slot_counter.most_common(3)],
        popular_string_ids=popular_string_ids,
        workload_mix=[
            AnalyticsWorkloadEntryOut(label="Pending payment", value=0),
            AnalyticsWorkloadEntryOut(
                label="Awaiting drop-off",
                value=awaiting_dropoff_count,
            ),
            AnalyticsWorkloadEntryOut(label="In progress", value=in_progress_count),
            AnalyticsWorkloadEntryOut(
                label="Ready for collection",
                value=ready_for_collection_count,
            ),
            AnalyticsWorkloadEntryOut(
                label="Completed today",
                value=completed_today,
            ),
        ],
    )


def popular_strings(db: Session, limit: int) -> list[PopularStringOut]:
    bookings = (
        db.execute(
            select(Booking)
            .options(joinedload(Booking.string_item))
            .where(
                Booking.status.not_in(
                    [BookingStatus.CANCELLED.value, BookingStatus.REJECTED.value]
                )
            )
        )
        .unique()
        .scalars()
        .all()
    )
    counter: Counter[str] = Counter()
    string_by_id: dict[str, StringCatalogItem] = {}
    for booking in bookings:
        counter[booking.string_id] += 1
        string_by_id[booking.string_id] = booking.string_item

    items: list[PopularStringOut] = []
    for string_id, count in counter.most_common(limit):
        string_item = string_by_id[string_id]
        items.append(
            PopularStringOut(
                string_id=string_id,
                brand=string_item.brand,
                model_name=string_item.model_name,
                booking_count=count,
            )
        )
    return items


@admin_router.get("/business-hours", response_model=StoreBusinessHoursOut)
def admin_get_business_hours(
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> StoreBusinessHoursOut:
    return serialize_store_business_hours(get_store_business_hours(db))


@admin_router.put("/business-hours", response_model=StoreBusinessHoursOut)
def admin_update_business_hours(
    payload: StoreBusinessHoursPayload,
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> StoreBusinessHoursOut:
    hours = get_store_business_hours(db)
    hours.days_json = [day.model_dump() for day in payload.days]
    hours.special_closed_dates = payload.special_closed_dates
    db.commit()
    db.refresh(hours)
    return serialize_store_business_hours(hours)


def list_slots(
    *,
    date_value: date | None,
    date_from: date | None,
    days: int,
    db: Session,
) -> dict[str, object]:
    hours = get_store_business_hours(db)
    bookings = bookings_for_slot_generation(db)
    if date_value is not None:
        items = slots_for_date(target_date=date_value, hours=hours, bookings=bookings)
        return page_response(
            items=[item.model_dump() for item in items],
            total=len(items),
            limit=None,
            offset=0,
        )

    start_date = date_from or datetime.now(timezone.utc).date()
    items: list[BookingSlotOut] = []
    for offset in range(days):
        items.extend(
            slots_for_date(
                target_date=start_date + timedelta(days=offset),
                hours=hours,
                bookings=bookings,
            )
        )
    return page_response(
        items=[item.model_dump() for item in items],
        total=len(items),
        limit=None,
        offset=0,
    )


@admin_router.get("/slots", response_model=dict)
def admin_list_slots(
    date_value: date | None = Query(default=None, alias="date"),
    date_from: date | None = Query(default=None),
    days: int = Query(default=7, ge=1, le=31),
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return list_slots(
        date_value=date_value,
        date_from=date_from,
        days=days,
        db=db,
    )


@public_router.get("/slots", response_model=dict)
def public_list_slots(
    date_value: date | None = Query(default=None, alias="date"),
    date_from: date | None = Query(default=None),
    days: int = Query(default=7, ge=1, le=31),
    _: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return list_slots(
        date_value=date_value,
        date_from=date_from,
        days=days,
        db=db,
    )


@admin_router.get("/check-in/lookup", response_model=CheckInLookupOut)
def admin_lookup_check_in(
    reference: str = Query(min_length=1, max_length=120),
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> CheckInLookupOut:
    matched_by, booking = resolve_lookup_booking(
        db=db,
        booking_id=None,
        reference=reference,
    )
    return CheckInLookupOut(
        matched_by=matched_by,
        booking=serialize_booking(booking, include_user=True, include_history=True),
    )


@admin_router.post("/check-in", response_model=BookingOut)
def admin_check_in_booking(
    payload: CheckInPayload,
    current_user: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> BookingOut:
    _, booking = resolve_lookup_booking(
        db=db,
        booking_id=payload.booking_id,
        reference=payload.reference,
    )
    if booking.status != BookingStatus.AWAITING_DROPOFF.value:
        raise ConflictError("Only awaiting drop-off bookings can be checked in")

    next_status = BookingStatus.IN_PROGRESS.value
    assert_booking_status_transition(booking.status, next_status)
    previous_status = booking.status
    booking.status = next_status
    db.add(
        BookingStatusHistory(
            booking_id=booking.id,
            old_status=previous_status,
            new_status=next_status,
            changed_by_user_id=current_user.user_id,
            note=(payload.note or "Checked in at the service counter.").strip(),
        )
    )
    db.commit()
    db.expire_all()
    return serialize_booking(
        get_booking_or_404(db, booking.id),
        include_user=True,
        include_history=True,
    )


@admin_router.get("/service-queue", response_model=ServiceQueueOut)
def admin_service_queue(
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> ServiceQueueOut:
    return build_service_queue(db)


@admin_router.get("/store-settings", response_model=StoreSettingsOut)
def admin_get_store_settings(
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> StoreSettingsOut:
    return serialize_store_settings(get_store_settings(db))


@admin_router.put("/store-settings", response_model=StoreSettingsOut)
def admin_update_store_settings(
    payload: StoreSettingsPayload,
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> StoreSettingsOut:
    settings = get_store_settings(db)
    for field, value in payload.model_dump().items():
        setattr(settings, field, value)
    db.commit()
    db.refresh(settings)
    return serialize_store_settings(settings)


@admin_router.get("/analytics/summary", response_model=AnalyticsSummaryOut)
def admin_analytics_summary(
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AnalyticsSummaryOut:
    return analytics_summary(db)


@admin_router.get("/analytics/popular-strings", response_model=list[PopularStringOut])
def admin_popular_strings(
    limit: int = Query(default=5, ge=1, le=20),
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[PopularStringOut]:
    return popular_strings(db, limit)
