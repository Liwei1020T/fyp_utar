from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from datetime import timezone

from app.domain.booking.enums import BookingStatus
from app.domain.store.entities import ServiceQueue
from app.domain.store.entities import ServiceQueueItem
from app.domain.store.entities import ServiceQueueLane
from app.ports.repositories.booking_repository import BookingRepository


@dataclass
class GetQueueUseCase:
    booking_repository: BookingRepository

    def execute(self) -> ServiceQueue:
        bookings = self.booking_repository.list_active_queue()
        lanes: list[ServiceQueueLane] = []
        for status, title in (
            (BookingStatus.AWAITING_DROPOFF.value, "Awaiting drop-off"),
            (BookingStatus.IN_PROGRESS.value, "In progress"),
            (BookingStatus.READY_FOR_COLLECTION.value, "Ready for collection"),
        ):
            lane_bookings = [booking for booking in bookings if booking.status == status]
            lanes.append(
                ServiceQueueLane(
                    status=status,
                    title=title,
                    items=[
                        ServiceQueueItem(queue_position=index + 1, booking=booking)
                        for index, booking in enumerate(lane_bookings)
                    ],
                )
            )
        return ServiceQueue(
            generated_at=datetime.now(timezone.utc).isoformat(),
            lanes=lanes,
        )

