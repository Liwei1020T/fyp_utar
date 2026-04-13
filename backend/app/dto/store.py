from __future__ import annotations

from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator

from app.domain.store.entities import AnalyticsSummary
from app.domain.store.entities import BookingSlot
from app.domain.store.entities import PopularString
from app.domain.store.entities import StoreBusinessHoursRecord
from app.domain.store.entities import StoreSettingsRecord
from app.shared.constants import STORE_ID


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
        if self.open_time >= self.close_time:
            raise ValueError("open_time must be earlier than close_time")
        if self.break_start and self.break_end and self.break_start >= self.break_end:
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
    booking: dict[str, object]


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
    booking: dict[str, object]


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
    trending_string_ids: list[str] = Field(default_factory=list, max_length=5)

    @model_validator(mode="after")
    def validate_trending_string_ids(self) -> "StoreSettingsPayload":
        normalized = [
            value.strip() for value in self.trending_string_ids if value.strip()
        ]
        if len(set(normalized)) != len(normalized):
            raise ValueError("trending_string_ids must not contain duplicates")
        self.trending_string_ids = normalized
        return self


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


def business_hours_to_dto(hours: StoreBusinessHoursRecord) -> StoreBusinessHoursOut:
    return StoreBusinessHoursOut(
        id=hours.id,
        days=[
            BusinessHoursDayPayload.model_validate(day.__dict__) for day in hours.days
        ],
        special_closed_dates=hours.special_closed_dates,
        updated_at=hours.updated_at,
    )


def settings_to_dto(settings: StoreSettingsRecord) -> StoreSettingsOut:
    return StoreSettingsOut(
        id=settings.id,
        store_name=settings.store_name,
        store_contact=settings.store_contact,
        support_text=settings.support_text,
        payment_notes=settings.payment_notes,
        booking_notes=settings.booking_notes,
        store_policy_text=settings.store_policy_text,
        address=settings.address,
        trending_string_ids=settings.trending_string_ids,
        updated_at=settings.updated_at,
    )


def slot_to_dto(slot: BookingSlot) -> BookingSlotOut:
    return BookingSlotOut(**slot.__dict__)


def analytics_summary_to_dto(summary: AnalyticsSummary) -> AnalyticsSummaryOut:
    return AnalyticsSummaryOut(
        weekly_bookings=summary.weekly_bookings,
        pending_payment_count=summary.pending_payment_count,
        awaiting_dropoff_count=summary.awaiting_dropoff_count,
        in_progress_count=summary.in_progress_count,
        ready_for_collection_count=summary.ready_for_collection_count,
        completed_today=summary.completed_today,
        low_stock_count=summary.low_stock_count,
        unread_chats=summary.unread_chats,
        today_revenue=summary.today_revenue,
        busy_slots=summary.busy_slots,
        popular_string_ids=summary.popular_string_ids,
        workload_mix=[
            AnalyticsWorkloadEntryOut(label=item.label, value=item.value)
            for item in summary.workload_mix
        ],
    )


def popular_string_to_dto(item: PopularString) -> PopularStringOut:
    return PopularStringOut(**item.__dict__)
