from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from sqlalchemy.orm import Session

from stringsense_backend.api.dependencies import CurrentUser
from stringsense_backend.api.dependencies import get_current_admin
from stringsense_backend.core.errors import BadRequestError
from stringsense_backend.db.models import BookingStatusHistory
from stringsense_backend.db.models import StringCatalogItem
from stringsense_backend.db.session import get_db
from stringsense_backend.modules.bookings import BookingOut
from stringsense_backend.modules.bookings import BookingSortField
from stringsense_backend.modules.bookings import SortOrder
from stringsense_backend.modules.bookings import UpdateBookingStatusPayload
from stringsense_backend.modules.bookings import assert_booking_status_transition
from stringsense_backend.modules.bookings import get_booking_or_404
from stringsense_backend.modules.bookings import list_admin_bookings
from stringsense_backend.modules.bookings import serialize_booking
from stringsense_backend.modules.recommendations import recommendation_logs_page
from stringsense_backend.modules.strings import StringOut
from stringsense_backend.modules.strings import AdminInventoryStringOut
from stringsense_backend.modules.strings import InventoryUpdatePayload
from stringsense_backend.modules.strings import StringWritePayload
from stringsense_backend.modules.strings import build_string_values
from stringsense_backend.modules.strings import get_string_or_404
from stringsense_backend.modules.strings import list_inventory_strings
from stringsense_backend.modules.strings import list_strings
from stringsense_backend.modules.strings import serialize_inventory_string
from stringsense_backend.modules.strings import serialize_string


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/strings", response_model=dict)
def admin_list_strings(
    search: str | None = Query(default=None, max_length=100),
    brand: str | None = Query(default=None, max_length=100),
    is_active: bool | None = Query(default=None),
    sort_by: Literal[
        "brand",
        "model_name",
        "price_rm",
        "attack",
        "comfort",
        "control",
        "durability",
        "elasticity",
        "sound",
        "tension_retention",
        "value_for_money",
        "created_at",
        "updated_at",
    ] = Query(default="updated_at"),
    sort_order: Literal["asc", "desc"] = Query(default="desc"),
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return list_strings(
        db,
        is_active=is_active,
        brand=brand,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )


@router.post("/strings", response_model=StringOut)
def admin_create_string(
    payload: StringWritePayload,
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> StringOut:
    item = StringCatalogItem(**build_string_values(payload))
    db.add(item)
    db.commit()
    db.refresh(item)
    return serialize_string(item)


@router.put("/strings/{string_id}", response_model=StringOut)
def admin_update_string(
    string_id: str,
    payload: StringWritePayload,
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> StringOut:
    item = get_string_or_404(db, string_id, include_inactive=True)
    for field, value in build_string_values(payload).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return serialize_string(item)


@router.delete("/strings/{string_id}", response_model=StringOut)
def admin_deactivate_string(
    string_id: str,
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> StringOut:
    item = get_string_or_404(db, string_id, include_inactive=True)
    item.is_active = False
    db.commit()
    db.refresh(item)
    return serialize_string(item)


@router.get("/inventory/strings", response_model=dict)
def admin_inventory_strings(
    search: str | None = Query(default=None, max_length=100),
    brand: str | None = Query(default=None, max_length=100),
    availability: Literal["in_stock", "low_stock", "out_of_stock"] | None = Query(
        default=None
    ),
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return list_inventory_strings(
        db,
        brand=brand,
        search=search,
        availability=availability,
        limit=limit,
        offset=offset,
    )


@router.get("/inventory/strings/{string_id}", response_model=AdminInventoryStringOut)
def admin_inventory_string_detail(
    string_id: str,
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AdminInventoryStringOut:
    return serialize_inventory_string(
        get_string_or_404(db, string_id, include_inactive=True)
    )


@router.patch("/inventory/strings/{string_id}", response_model=AdminInventoryStringOut)
def admin_update_inventory_string(
    string_id: str,
    payload: InventoryUpdatePayload,
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AdminInventoryStringOut:
    if not payload.model_fields_set:
        raise BadRequestError("At least one inventory field must be provided")

    item = get_string_or_404(db, string_id, include_inactive=True)

    if "price_rm" in payload.model_fields_set:
        item.price_rm = payload.price_rm
    if "stock_level" in payload.model_fields_set:
        item.stock_level = payload.stock_level or 0
        item.is_active = item.stock_level > 0
    if "admin_note" in payload.model_fields_set:
        item.admin_note = payload.admin_note.strip() if payload.admin_note else None

    db.commit()
    db.refresh(item)
    return serialize_inventory_string(item)


@router.get("/bookings", response_model=dict)
def admin_bookings(
    status: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=100),
    sort_by: BookingSortField = Query(default="updated_at"),
    sort_order: SortOrder = Query(default="desc"),
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return list_admin_bookings(
        db,
        status=status,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )


@router.get("/bookings/{booking_id}", response_model=BookingOut)
def admin_get_booking(
    booking_id: str,
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> BookingOut:
    return serialize_booking(
        get_booking_or_404(db, booking_id),
        include_user=True,
        include_history=True,
    )


@router.patch("/bookings/{booking_id}/status", response_model=BookingOut)
def admin_update_booking_status(
    booking_id: str,
    payload: UpdateBookingStatusPayload,
    current_user: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> BookingOut:
    booking = get_booking_or_404(db, booking_id)
    assert_booking_status_transition(booking.status, payload.status)
    previous_status = booking.status
    booking.status = payload.status
    db.add(
        BookingStatusHistory(
            booking_id=booking.id,
            old_status=previous_status,
            new_status=payload.status,
            changed_by_user_id=current_user.user_id,
            note=payload.note.strip() if payload.note else None,
        )
    )
    db.commit()
    db.expire_all()
    return serialize_booking(
        get_booking_or_404(db, booking_id),
        include_user=True,
        include_history=True,
    )


@router.get("/recommendations/logs", response_model=dict)
def admin_recommendation_logs(
    phone_number: str | None = Query(default=None, max_length=30),
    algorithm_version: str | None = Query(default=None, max_length=80),
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return recommendation_logs_page(
        phone_number=phone_number,
        algorithm_version=algorithm_version,
        limit=limit,
        offset=offset,
        db=db,
    )
