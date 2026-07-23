from __future__ import annotations

from datetime import datetime
from datetime import timezone
from decimal import Decimal


def number_to_float(value: Decimal | float | None) -> float | None:
    if value is None:
        return None
    return float(value)


def isoformat_or_none(value: datetime | None) -> str | None:
    if value is None:
        return None
    normalized = (
        value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    )
    return normalized.isoformat()
