from __future__ import annotations

from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator


SentimentTag = Literal[
    "crisp_feel",
    "good_communication",
    "fast_turnaround",
    "would_book_again",
]


class CreateRacketPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nickname: str = Field(min_length=1, max_length=80)
    brand: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    weight_class: str | None = Field(default=None, min_length=1, max_length=30)
    balance_point: str | None = Field(default=None, min_length=1, max_length=50)
    grip_size: str | None = Field(default=None, min_length=1, max_length=30)
    preferred_use: str | None = Field(default=None, min_length=1, max_length=120)
    notes: str | None = Field(default=None, min_length=1, max_length=1000)


class UpdateRacketPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nickname: str | None = Field(default=None, min_length=1, max_length=80)
    brand: str | None = Field(default=None, min_length=1, max_length=100)
    model: str | None = Field(default=None, min_length=1, max_length=100)
    weight_class: str | None = Field(default=None, min_length=1, max_length=30)
    balance_point: str | None = Field(default=None, min_length=1, max_length=50)
    grip_size: str | None = Field(default=None, min_length=1, max_length=30)
    preferred_use: str | None = Field(default=None, min_length=1, max_length=120)
    notes: str | None = Field(default=None, min_length=1, max_length=1000)

    @model_validator(mode="after")
    def validate_update(self) -> "UpdateRacketPayload":
        if not self.model_fields_set:
            raise ValueError("At least one racket field is required")
        for field_name in ("nickname", "brand", "model"):
            if (
                field_name in self.model_fields_set
                and getattr(self, field_name) is None
            ):
                raise ValueError(f"{field_name} cannot be null")
        return self


class RacketOut(BaseModel):
    id: str
    user_id: str
    nickname: str
    brand: str
    model: str
    weight_class: str | None
    balance_point: str | None
    grip_size: str | None
    preferred_use: str | None
    notes: str | None
    created_at: str
    updated_at: str


class CreateFeedbackPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    rating: int = Field(ge=1, le=5, strict=True)
    string_feedback: str | None = Field(
        default=None,
        min_length=1,
        max_length=2000,
    )
    service_feedback: str | None = Field(
        default=None,
        min_length=1,
        max_length=2000,
    )
    sentiment_tags: list[SentimentTag] = Field(default_factory=list, max_length=4)

    @model_validator(mode="after")
    def validate_feedback(self) -> "CreateFeedbackPayload":
        if not (self.string_feedback or self.service_feedback or self.sentiment_tags):
            raise ValueError("Add feedback text or at least one sentiment tag")
        if len(self.sentiment_tags) != len(set(self.sentiment_tags)):
            raise ValueError("sentiment_tags must be unique")
        return self


class FeedbackOut(BaseModel):
    id: str
    booking_id: str
    user_id: str
    rating: int
    string_feedback: str | None
    service_feedback: str | None
    sentiment_tags: list[SentimentTag]
    created_at: str
    updated_at: str


class RacketServiceHistoryOut(BaseModel):
    booking_id: str
    string_id: str
    string_name: str
    requested_tension: float | None
    serviced_at: str
    feedback: FeedbackOut | None


class RacketDetailOut(RacketOut):
    service_history: list[RacketServiceHistoryOut]
