from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator

from app.schemas.common import OptionalLongText
from app.schemas.common import PriceValue
from app.schemas.common import TrimmedString


class StringPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brand: TrimmedString
    model_name: TrimmedString
    price: PriceValue | None = None
    recommended_tension_min: int | None = Field(default=None, ge=18, le=35)
    recommended_tension_max: int | None = Field(default=None, ge=18, le=35)
    description: OptionalLongText | None = None

    @model_validator(mode="after")
    def validate_tension_range(self) -> "StringPayload":
        if (
            isinstance(self.recommended_tension_min, int)
            and isinstance(self.recommended_tension_max, int)
            and self.recommended_tension_max < self.recommended_tension_min
        ):
            raise ValueError(
                "recommended_tension_max must be greater than or equal to recommended_tension_min"
            )
        return self
