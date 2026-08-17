from __future__ import annotations

from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


ConversationState = Literal[
    "waiting_admin",
    "admin_joined",
    "resolved",
    "closed",
]


class SendConversationMessagePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    body: str = Field(min_length=1, max_length=2000)


class BookingConversationMessageOut(BaseModel):
    id: str
    author_user_id: str
    author_role: str
    body: str
    created_at: str | None


class BookingConversationOut(BaseModel):
    id: str
    booking_id: str | None
    player_id: str
    state: ConversationState
    support_requested_at: str
    player_last_read_at: str | None
    admin_last_read_at: str | None
    created_at: str | None
    updated_at: str | None
    messages: list[BookingConversationMessageOut]
