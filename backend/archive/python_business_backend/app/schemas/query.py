from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class PaginationParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int | None = Field(default=None, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


class PublicStringSortField(StrEnum):
    BRAND = "brand"
    MODEL_NAME = "model_name"
    PRICE = "price"
    RATING = "rating"
    POPULARITY_SIGNAL = "popularity_signal"


class AdminStringSortField(StrEnum):
    BRAND = "brand"
    MODEL_NAME = "model_name"
    PRICE = "price"
    RATING = "rating"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    POPULARITY_SIGNAL = "popularity_signal"


class AdminBookingSortField(StrEnum):
    CREATED_AT = "created_at"
    APPOINTMENT_DATE = "appointment_date"
    STATUS = "status"
    UPDATED_AT = "updated_at"
