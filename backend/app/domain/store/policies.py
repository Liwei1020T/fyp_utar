from __future__ import annotations

from collections import Counter
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from datetime import timezone

from app.domain.booking.entities import BookingRecord
from app.domain.booking.enums import BookingStatus
from app.domain.store.entities import BookingSlot
from app.domain.store.entities import BusinessHoursDay


ACTIVE_QUEUE_STATUSES = (
    BookingStatus.AWAITING_DROPOFF.value,
    BookingStatus.IN_PROGRESS.value,
    BookingStatus.READY_FOR_COLLECTION.value,
)


def parse_hhmm(value: str) -> time:
    return time.fromisoformat(value)


def booking_check_in_reference(booking_id: str) -> str:
    return f"CHK-{booking_id[:8].upper()}"


def weekday_name(target_date: date) -> str:
    return target_date.strftime("%A")


def slot_label(slot_time: str) -> str:
    return datetime.strptime(slot_time, "%H:%M").strftime("%-I:%M %p")


def slot_busy_label(target_date: date, slot_time: str) -> str:
    return (
        f"{target_date.strftime('%a')} "
        f"{datetime.strptime(slot_time, '%H:%M').strftime('%-I %p')}"
    )


def normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def slots_for_date(
    *,
    target_date: date,
    day_config: BusinessHoursDay | None,
    special_closed_dates: list[str],
    bookings: list[BookingRecord],
) -> list[BookingSlot]:
    if day_config is None or not day_config.is_open:
        return []
    if target_date.isoformat() in special_closed_dates:
        return []

    open_time = parse_hhmm(day_config.open_time)
    close_time = parse_hhmm(day_config.close_time)
    break_start = parse_hhmm(day_config.break_start) if day_config.break_start else None
    break_end = parse_hhmm(day_config.break_end) if day_config.break_end else None
    capacity = day_config.max_bookings_per_slot
    duration = timedelta(minutes=day_config.slot_duration_minutes)
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
        if booking.status in {
            BookingStatus.CANCELLED.value,
            BookingStatus.REJECTED.value,
        }:
            continue
        drop_off = normalize_datetime(booking.drop_off_datetime)
        if drop_off is None or drop_off.date() != target_date:
            continue
        booked_counter[drop_off.strftime("%H:%M")] += 1

    items: list[BookingSlot] = []
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
            BookingSlot(
                id=f"slot-{target_date.isoformat()}-{slot_time}",
                date=target_date.isoformat(),
                time=slot_time,
                capacity=capacity,
                booked_count=booked_count,
                available_spots=max(0, capacity - booked_count),
                label=slot_label(slot_time),
                day_label=weekday_name(target_date),
            )
        )
        current += duration
    return items
