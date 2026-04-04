from __future__ import annotations

import re
from decimal import Decimal
from typing import Annotated, Any

from pydantic import AfterValidator
from pydantic import BaseModel
from pydantic import BeforeValidator
from pydantic import ConfigDict
from pydantic import Field
from pydantic import StringConstraints
from pydantic import model_validator

from app.core.constants import MAX_BUDGET
from app.core.constants import MAX_PASSWORD_LENGTH
from app.core.constants import MAX_PRICE
from app.core.constants import MAX_TENSION
from app.core.constants import MIN_PASSWORD_LENGTH
from app.core.constants import MIN_TENSION


def _clean_text(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    return value


def normalize_phone_number(value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError("Phone number must be a string")

    raw = re.sub(r"[\s()-]+", "", value.strip())
    if raw.startswith("+"):
        normalized = f"+{re.sub(r'[^0-9]', '', raw[1:])}"
    else:
        normalized = re.sub(r"[^0-9]", "", raw)

    if not re.fullmatch(r"(?:\+?[0-9]{9,15})", normalized):
        raise ValueError("Phone number must contain 9 to 15 digits")
    return normalized


def validate_password_strength(value: str) -> str:
    if not any(character.isalpha() for character in value):
        raise ValueError("Password must contain at least one letter")
    if not any(character.isdigit() for character in value):
        raise ValueError("Password must contain at least one digit")
    return value


TrimmedString = Annotated[
    str,
    BeforeValidator(_clean_text),
    StringConstraints(strip_whitespace=True, min_length=1),
]
PhoneNumber = Annotated[str, BeforeValidator(normalize_phone_number)]
PasswordString = Annotated[
    str,
    StringConstraints(
        min_length=MIN_PASSWORD_LENGTH,
        max_length=MAX_PASSWORD_LENGTH,
    ),
    AfterValidator(validate_password_strength),
]
OptionalShortText = Annotated[
    str,
    BeforeValidator(_clean_text),
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]
OptionalLongText = Annotated[
    str,
    BeforeValidator(_clean_text),
    StringConstraints(strip_whitespace=True, min_length=1, max_length=1000),
]
PriorityValue = Annotated[int, Field(ge=1, le=5)]
BudgetValue = Annotated[Decimal, Field(ge=0, le=MAX_BUDGET)]
PriceValue = Annotated[Decimal, Field(ge=0, le=MAX_PRICE)]
TensionValue = Annotated[Decimal, Field(ge=MIN_TENSION, le=MAX_TENSION)]


class BudgetRangeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min: BudgetValue | None = None
    max: BudgetValue | None = None

    @model_validator(mode="after")
    def validate_range(self) -> "BudgetRangeInput":
        if (
            isinstance(self.min, Decimal)
            and isinstance(self.max, Decimal)
            and self.max < self.min
        ):
            raise ValueError("budget.max must be greater than or equal to budget.min")
        return self
