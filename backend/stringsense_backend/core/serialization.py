from __future__ import annotations

from datetime import datetime
from decimal import Decimal


def decimal_to_float(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)


def isoformat_or_none(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()
