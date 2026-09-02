from __future__ import annotations

from datetime import datetime
from typing import Annotated
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import StringConstraints


DEFAULT_NOTIFICATION_PREFERENCES = {
    "booking": True,
    "payment": True,
    "service": True,
    "chat": True,
    "recommendation": True,
    "system": True,
}

NotificationCategory = Literal[
    "booking",
    "payment",
    "service",
    "chat",
    "recommendation",
    "system",
]
NotificationEventId = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=160,
        pattern=r"^[a-z][a-z-]*:[A-Za-z0-9:_-]+$",
    ),
]


class NotificationPreferencesPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    booking: bool = True
    payment: bool = True
    service: bool = True
    chat: bool = True
    recommendation: bool = True
    system: bool = True


class NotificationOut(BaseModel):
    id: str
    user_id: str
    category: NotificationCategory
    title: str
    body: str
    created_at: datetime
    read: bool = False
    route: str


class MarkNotificationsReadPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_ids: list[NotificationEventId] = Field(min_length=1, max_length=100)


class MarkNotificationsReadOut(BaseModel):
    marked_count: int
    marked_read_ids: list[str]


class AdminNotificationOut(BaseModel):
    id: str
    user_id: str
    customer_username: str
    customer_phone_number: str
    category: NotificationCategory
    title: str
    body: str
    route: str | None
    status: str
    provider_message: str | None
    attempts: int
    created_at: datetime
    last_attempt_at: datetime | None


class SendNotificationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    user_id: str = Field(min_length=36, max_length=36)
    category: NotificationCategory
    title: str = Field(min_length=1, max_length=160)
    body: str = Field(min_length=1, max_length=2000)
    route: str | None = Field(default=None, min_length=1, max_length=255)


def notification_preferences_to_dto(
    values: dict[str, bool],
) -> NotificationPreferencesPayload:
    return NotificationPreferencesPayload(
        **{**DEFAULT_NOTIFICATION_PREFERENCES, **values}
    )
