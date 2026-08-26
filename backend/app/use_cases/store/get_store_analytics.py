from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta

from app.domain.booking.enums import BookingStatus
from app.domain.catalog.policies import inventory_availability
from app.domain.store.entities import AnalyticsSummary
from app.domain.store.entities import AnalyticsWorkloadEntry
from app.domain.store.entities import PopularString
from app.domain.store.policies import normalize_datetime
from app.domain.store.policies import slot_busy_label
from app.ports.repositories.booking_repository import BookingRepository
from app.ports.repositories.catalog_repository import CatalogRepository
from app.ports.services.clock import Clock


@dataclass(frozen=True)
class AnalyticsPayment:
    status: str
    payment_type: str
    amount: float
    updated_at: datetime


@dataclass(frozen=True)
class AnalyticsFeedback:
    booking_id: str
    rating: int


@dataclass
class GetStoreAnalyticsUseCase:
    booking_repository: BookingRepository
    catalog_repository: CatalogRepository
    clock: Clock

    def execute_summary(
        self,
        *,
        payments: list[AnalyticsPayment],
        feedback: list[AnalyticsFeedback],
        unread_chats: int,
        store_timezone: str,
        period_days: int = 7,
    ) -> AnalyticsSummary:
        bookings = self.booking_repository.list_all_for_analytics()
        strings = self.catalog_repository.list_inventory(
            brand=None,
            search=None,
            availability=None,
            limit=None,
            offset=0,
        ).items
        now = normalize_datetime(self.clock.now(), store_timezone)
        assert now is not None
        week_ago = now - timedelta(days=7)
        period_start = now - timedelta(days=period_days)
        previous_period_start = period_start - timedelta(days=period_days)
        today = now.date()

        weekly_bookings = 0
        today_bookings = 0
        awaiting_dropoff_count = 0
        in_progress_count = 0
        ready_for_collection_count = 0
        completed_today = 0
        pending_payment_count = 0
        today_revenue = 0.0
        period_bookings = 0
        previous_period_bookings = 0
        period_revenue = 0.0
        previous_period_revenue = 0.0
        slot_counter: Counter[str] = Counter()
        string_counter: Counter[str] = Counter()
        customer_completed_counter: Counter[str] = Counter()
        tension_counter: Counter[str] = Counter()
        completion_hours: list[float] = []

        for payment in payments:
            paid_at = normalize_datetime(payment.updated_at, store_timezone)
            if payment.status == "pending":
                pending_payment_count += 1
            elif payment.status == "paid" and payment.payment_type == "booking_payment":
                if paid_at is not None and paid_at.date() == today:
                    today_revenue += payment.amount
                if paid_at is not None and period_start <= paid_at <= now:
                    period_revenue += payment.amount
                elif (
                    paid_at is not None
                    and previous_period_start <= paid_at < period_start
                ):
                    previous_period_revenue += payment.amount

        for booking in bookings:
            created_at = normalize_datetime(booking.created_at, store_timezone)
            updated_at = normalize_datetime(booking.updated_at, store_timezone)
            if created_at is not None and created_at >= week_ago:
                weekly_bookings += 1
            if created_at is not None and period_start <= created_at <= now:
                period_bookings += 1
            elif (
                created_at is not None
                and previous_period_start <= created_at < period_start
            ):
                previous_period_bookings += 1

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

            if booking.status not in {
                BookingStatus.CANCELLED.value,
                BookingStatus.REJECTED.value,
            }:
                string_counter[booking.string_id] += 1
                drop_off = normalize_datetime(
                    booking.drop_off_datetime,
                    store_timezone,
                )
                if drop_off is not None:
                    if drop_off.date() == today:
                        today_bookings += 1
                    slot_counter[
                        slot_busy_label(drop_off.date(), drop_off.strftime("%H:%M"))
                    ] += 1
                if booking.requested_tension is not None:
                    tension_counter[f"{booking.requested_tension:g} lbs"] += 1

            if booking.status == BookingStatus.COMPLETED.value:
                customer_completed_counter[booking.user_id] += 1
                completed_at = normalize_datetime(
                    booking.collection_datetime or booking.updated_at,
                    store_timezone,
                )
                if created_at is not None and completed_at is not None:
                    completion_hours.append(
                        max(0, (completed_at - created_at).total_seconds() / 3600)
                    )

        low_stock_count = sum(
            1 for item in strings if inventory_availability(item) == "low_stock"
        )
        popular_string_ids = [
            string_id for string_id, _ in string_counter.most_common(3)
        ]
        feedback_booking_ids = {item.booking_id for item in feedback}
        completed_booking_ids = {
            booking.id
            for booking in bookings
            if booking.status == BookingStatus.COMPLETED.value
        }
        return AnalyticsSummary(
            weekly_bookings=weekly_bookings,
            today_bookings=today_bookings,
            pending_payment_count=pending_payment_count,
            awaiting_dropoff_count=awaiting_dropoff_count,
            in_progress_count=in_progress_count,
            ready_for_collection_count=ready_for_collection_count,
            completed_today=completed_today,
            low_stock_count=low_stock_count,
            unread_chats=unread_chats,
            today_revenue=round(today_revenue, 2),
            period_days=period_days,
            period_bookings=period_bookings,
            previous_period_bookings=previous_period_bookings,
            period_revenue=round(period_revenue, 2),
            previous_period_revenue=round(previous_period_revenue, 2),
            repeat_customer_count=sum(
                1 for count in customer_completed_counter.values() if count >= 2
            ),
            pending_feedback_count=len(completed_booking_ids - feedback_booking_ids),
            average_feedback_score=(
                round(sum(item.rating for item in feedback) / len(feedback), 2)
                if feedback
                else None
            ),
            average_completion_hours=(
                round(sum(completion_hours) / len(completion_hours), 1)
                if completion_hours
                else None
            ),
            tension_distribution=dict(tension_counter.most_common()),
            busy_slots=[label for label, _ in slot_counter.most_common(3)],
            popular_string_ids=popular_string_ids,
            workload_mix=[
                AnalyticsWorkloadEntry(
                    label="Pending payment",
                    value=pending_payment_count,
                ),
                AnalyticsWorkloadEntry(
                    label="Awaiting drop-off",
                    value=awaiting_dropoff_count,
                ),
                AnalyticsWorkloadEntry(label="In progress", value=in_progress_count),
                AnalyticsWorkloadEntry(
                    label="Ready for collection",
                    value=ready_for_collection_count,
                ),
                AnalyticsWorkloadEntry(label="Completed today", value=completed_today),
            ],
        )

    def execute_popular_strings(self, *, limit: int) -> list[PopularString]:
        bookings = self.booking_repository.list_all_for_analytics()
        active_bookings = [
            booking
            for booking in bookings
            if booking.status
            not in {BookingStatus.CANCELLED.value, BookingStatus.REJECTED.value}
        ]
        counter: Counter[str] = Counter(
            booking.string_id for booking in active_bookings
        )
        catalog = {
            item.id: item
            for item in self.catalog_repository.list_inventory(
                brand=None,
                search=None,
                availability=None,
                limit=None,
                offset=0,
            ).items
        }
        items: list[PopularString] = []
        for string_id, count in counter.most_common(limit):
            string_item = catalog[string_id]
            items.append(
                PopularString(
                    string_id=string_id,
                    brand=string_item.brand,
                    model_name=string_item.model_name,
                    booking_count=count,
                )
            )
        return items
