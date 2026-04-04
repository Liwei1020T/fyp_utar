from datetime import date
from datetime import datetime
from datetime import timezone

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator

from app.core.constants import BookingStatus
from app.schemas.common import TensionValue
from app.schemas.common import TrimmedString


class BookingPayload(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    string_id: TrimmedString
    racket_brand: str | None = None
    racket_model: str | None = None
    requested_tension: TensionValue | None = None
    appointment_date: date | None = None
    appointment_slot: str | None = Field(default=None, max_length=30)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_appointment_date(self) -> "BookingPayload":
        if self.appointment_date is not None:
            today = datetime.now(timezone.utc).date()
            if self.appointment_date < today:
                raise ValueError("appointment_date cannot be in the past")
        return self


class BookingStatusPayload(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    status: BookingStatus
