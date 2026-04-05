from __future__ import annotations

from app.shared.serialization import isoformat_or_none
from app.shared.serialization import number_to_float


def decimal_to_float(value):
    return number_to_float(value)


__all__ = ["decimal_to_float", "isoformat_or_none", "number_to_float"]
