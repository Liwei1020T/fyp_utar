from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
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


@dataclass
class GetStoreAnalyticsUseCase:
    booking_repository: BookingRepository
    catalog_repository: CatalogRepository
    clock: Clock

    def execute_summary(self) -> AnalyticsSummary:
        bookings = self.booking_repository.list_all_for_analytics()
        strings = self.catalog_repository.list_inventory(
            brand=None,
            search=None,
            availability=None,
            limit=None,
            offset=0,
        ).items
        now = self.clock.now().replace(tzinfo=None)
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
                for item in strings:
                    if item.id == booking.string_id:
                        today_revenue += item.price_rm or 0.0
                        break

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
        return AnalyticsSummary(
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
                AnalyticsWorkloadEntry(label="Pending payment", value=0),
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
        counter: Counter[str] = Counter(booking.string_id for booking in active_bookings)
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

