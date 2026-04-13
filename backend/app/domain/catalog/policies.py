from __future__ import annotations

from typing import Literal

from app.domain.catalog.entities import StringItem


InventoryAvailability = Literal["in_stock", "low_stock", "out_of_stock"]


def inventory_availability(item: StringItem) -> InventoryAvailability:
    if not item.is_active or item.stock_level <= 0:
        return "out_of_stock"
    if item.inventory and item.inventory.availability_status in {
        "in_stock",
        "low_stock",
        "out_of_stock",
    }:
        return item.inventory.availability_status  # type: ignore[return-value]
    if item.stock_level <= 5:
        return "low_stock"
    return "in_stock"
