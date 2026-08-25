from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.booking.entities import BookingRecord


@dataclass(frozen=True)
class BusinessHoursDay:
    day: str
    is_open: bool
    open_time: str
    close_time: str
    break_start: str | None
    break_end: str | None
    slot_duration_minutes: int
    max_bookings_per_slot: int


@dataclass(frozen=True)
class StoreBusinessHoursRecord:
    id: str
    days: list[BusinessHoursDay]
    special_closed_dates: list[str]
    updated_at: str | None


@dataclass(frozen=True)
class StoreSettingsRecord:
    id: str
    store_name: str
    store_contact: str
    support_text: str
    payment_notes: str
    payment_qr_path: str | None
    booking_notes: str
    store_policy_text: str
    address: str
    trending_string_ids: list[str]
    notification_settings: dict[str, object]
    updated_at: str | None


@dataclass(frozen=True)
class BookingSlot:
    id: str
    date: str
    time: str
    capacity: int
    booked_count: int
    available_spots: int
    label: str
    day_label: str


@dataclass(frozen=True)
class BookedSlot:
    drop_off_datetime: datetime
    status: str


@dataclass(frozen=True)
class CheckInLookup:
    matched_by: str
    booking: BookingRecord


@dataclass(frozen=True)
class ServiceQueueItem:
    queue_position: int
    booking: BookingRecord


@dataclass(frozen=True)
class ServiceQueueLane:
    status: str
    title: str
    items: list[ServiceQueueItem]


@dataclass(frozen=True)
class ServiceQueue:
    generated_at: str
    lanes: list[ServiceQueueLane]


@dataclass(frozen=True)
class AnalyticsWorkloadEntry:
    label: str
    value: int


@dataclass(frozen=True)
class AnalyticsSummary:
    weekly_bookings: int
    today_bookings: int
    pending_payment_count: int
    awaiting_dropoff_count: int
    in_progress_count: int
    ready_for_collection_count: int
    completed_today: int
    low_stock_count: int
    unread_chats: int
    today_revenue: float
    repeat_customer_count: int
    pending_feedback_count: int
    average_feedback_score: float | None
    average_completion_hours: float | None
    tension_distribution: dict[str, int]
    busy_slots: list[str]
    popular_string_ids: list[str]
    workload_mix: list[AnalyticsWorkloadEntry]


@dataclass(frozen=True)
class PopularString:
    string_id: str
    brand: str
    model_name: str
    booking_count: int
