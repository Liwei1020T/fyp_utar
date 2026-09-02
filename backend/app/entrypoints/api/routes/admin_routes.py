from __future__ import annotations

from datetime import date
from datetime import datetime
from typing import Literal
from typing import cast
from zoneinfo import ZoneInfo

from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import Form
from fastapi import Query
from fastapi import UploadFile
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.catalog_seed import (
    approved_catalog_ids,
)
from app.adapters.persistence.sqlalchemy.catalog_seed import (
    merge_with_approved_defaults,
)
from app.adapters.persistence.sqlalchemy.models import Booking
from app.adapters.persistence.sqlalchemy.models import CheckInToken
from app.adapters.persistence.sqlalchemy.models import Profile
from app.adapters.persistence.sqlalchemy.models import RecommendationScoreCache
from app.adapters.persistence.sqlalchemy.models import RacketModelCatalog
from app.adapters.persistence.sqlalchemy.models import StringCatalogItem
from app.adapters.persistence.sqlalchemy.models import User
from app.adapters.persistence.sqlalchemy.session import get_db
from app.config.settings import get_settings
from app.dto.booking import BookingOut
from app.dto.booking import BookingSortField
from app.dto.booking import SortOrder
from app.dto.booking import UpdateBookingStatusPayload
from app.dto.booking import booking_to_dto
from app.dto.auth import AdminUserBookingOut
from app.dto.auth import AdminUserDetailOut
from app.dto.auth import AdminUserProfileOut
from app.dto.auth import AdminUserSummaryOut
from app.dto.auth import AdminUsersOverviewOut
from app.dto.catalog import AdminInventoryStringOut
from app.dto.catalog import InventoryUpdatePayload
from app.dto.catalog import OfficialPerformanceOut
from app.dto.catalog import RecommendationMatrixImportReportOut
from app.dto.catalog import RecommendationMatrixInspectionOut
from app.dto.catalog import StringOut
from app.dto.catalog import StringEditorUpdatePayload
from app.dto.catalog import inventory_string_to_dto
from app.dto.catalog import official_performance_to_dto
from app.dto.catalog import recommendation_matrix_import_report_to_dto
from app.dto.catalog import recommendation_matrix_inspection_to_dto
from app.dto.catalog import string_to_dto
from app.dto.common import page_to_dict
from app.dto.recommendation import recommendation_run_to_dict
from app.dto.racket_feedback import AdminRacketModelOut
from app.dto.racket_feedback import CreateRacketModelPayload
from app.dto.racket_feedback import UpdateRacketModelPayload
from app.dto.store import CheckInLookupOut
from app.dto.store import CheckInPayload
from app.dto.store import ServiceQueueItemOut
from app.dto.store import ServiceQueueLaneOut
from app.dto.store import ServiceQueueOut
from app.dto.store import SecureCheckInPayload
from app.dto.store import StoreBusinessHoursOut
from app.dto.store import StoreBusinessHoursPayload
from app.dto.store import StoreSettingsOut
from app.dto.store import StoreSettingsPayload
from app.dto.store import business_hours_to_dto
from app.dto.store import settings_to_dto
from app.domain.booking.policies import booking_order_code
from app.domain.recommendation.learning_signals import normalize_racket_model_key
from app.domain.recommendation.scoring import ALGORITHM_VERSION
from app.entrypoints.api.dependencies import CurrentUser
from app.entrypoints.api.dependencies import get_booking_repository
from app.entrypoints.api.dependencies import get_catalog_repository
from app.entrypoints.api.dependencies import get_clock
from app.entrypoints.api.dependencies import get_current_admin
from app.entrypoints.api.dependencies import get_recommendation_run_repository
from app.entrypoints.api.dependencies import get_store_repository
from app.shared.errors import BadRequestError
from app.shared.errors import ConflictError
from app.shared.errors import NotFoundError
from app.shared.transaction_effects import register_created_file
from app.shared.transaction_effects import register_removed_file
from app.shared.upload_storage import MAX_UPLOAD_BYTES
from app.shared.upload_storage import delete_booking_update_photo
from app.shared.upload_storage import delete_payment_qr
from app.shared.upload_storage import delete_string_catalog_image
from app.shared.upload_storage import save_booking_update_photo
from app.shared.upload_storage import save_payment_qr
from app.shared.upload_storage import save_string_catalog_image
from app.use_cases.booking.add_booking_update import AddBookingUpdateUseCase
from app.use_cases.booking.get_booking import GetBookingUseCase
from app.use_cases.booking.list_admin_bookings import ListAdminBookingsUseCase
from app.use_cases.booking.update_booking_status import UpdateBookingStatusUseCase
from app.use_cases.catalog.get_string import GetStringUseCase
from app.use_cases.catalog.get_official_performance import GetOfficialPerformanceUseCase
from app.use_cases.catalog.get_recommendation_matrix import (
    GetRecommendationMatrixUseCase,
)
from app.use_cases.catalog.import_recommendation_matrix import (
    ImportRecommendationMatrixUseCase,
)
from app.use_cases.catalog.list_inventory_strings import ListInventoryStringsUseCase
from app.use_cases.catalog.prepare_string_values import PrepareStringValuesUseCase
from app.use_cases.catalog.update_inventory_string import UpdateInventoryStringUseCase
from app.use_cases.catalog.update_string import UpdateStringUseCase
from app.use_cases.catalog.update_string_editor import UpdateStringEditorUseCase
from app.use_cases.recommendation.list_recommendation_runs import (
    ListRecommendationRunsUseCase,
)
from app.use_cases.recommendation.get_recommendation_run import (
    GetRecommendationRunUseCase,
)
from app.use_cases.store.confirm_checkin import ConfirmCheckInUseCase
from app.use_cases.store.get_business_hours import GetBusinessHoursUseCase
from app.use_cases.store.get_queue import GetQueueUseCase
from app.domain.store.policies import hash_check_in_token
from app.use_cases.store.get_store_settings import GetStoreSettingsUseCase
from app.use_cases.store.lookup_checkin import LookupCheckInUseCase
from app.use_cases.store.update_business_hours import UpdateBusinessHoursUseCase
from app.use_cases.store.update_store_settings import UpdateStoreSettingsUseCase


router = APIRouter(prefix="/admin", tags=["admin"])

BookingPhotoType = Literal["racket", "service_progress", "other"]


def _prepare_string_values() -> PrepareStringValuesUseCase:
    settings = get_settings()
    return PrepareStringValuesUseCase(
        approved_strings_path=settings.approved_strings_path,
        approved_catalog_ids=approved_catalog_ids(settings.approved_string_cohort_path),
        merge_defaults=merge_with_approved_defaults,
    )


def _validate_closed_dates_not_in_past(special_closed_dates: list[str]) -> None:
    today = datetime.now(ZoneInfo(get_settings().store_timezone)).date()
    if any(date.fromisoformat(value) < today for value in special_closed_dates):
        raise BadRequestError("Closed dates must be today or later")


async def read_upload_bytes_limited(
    photo: UploadFile,
    *,
    oversize_message: str,
) -> bytes:
    total_size = 0
    chunks: list[bytes] = []
    while True:
        chunk = await photo.read(512 * 1024)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > MAX_UPLOAD_BYTES:
            raise BadRequestError(oversize_message)
        chunks.append(chunk)
    return b"".join(chunks)


async def save_update_photo_upload(
    photo: UploadFile,
) -> tuple[str, str | None, str | None]:
    photo_content_type = photo.content_type
    photo_original_name = photo.filename
    photo_content = await read_upload_bytes_limited(
        photo,
        oversize_message="Uploaded photo must be 5 MB or smaller",
    )
    photo_path = save_booking_update_photo(
        content=photo_content,
        content_type=photo.content_type,
        original_name=photo.filename,
    )
    return photo_path, photo_original_name, photo_content_type


async def save_string_image_upload(photo: UploadFile) -> str:
    photo_content = await read_upload_bytes_limited(
        photo,
        oversize_message="Uploaded image must be 5 MB or smaller",
    )
    return save_string_catalog_image(
        content=photo_content,
        content_type=photo.content_type,
        original_name=photo.filename,
    )


def inventory_update_values(payload: InventoryUpdatePayload) -> dict[str, object]:
    values: dict[str, object] = {}
    numeric_fields = (
        "price_rm",
        "stock_level",
        "current_stock",
        "reserved_stock",
        "reorder_level",
        "reorder_quantity",
        "cost_price",
        "selling_price",
    )
    optional_fields = (
        "pricing_mode",
        "availability_status",
        "movement_type",
        "reference_type",
        "reference_id",
    )
    for field in numeric_fields:
        if field in payload.model_fields_set:
            values[field] = getattr(payload, field)
    for field in optional_fields:
        if field in payload.model_fields_set:
            values[field] = getattr(payload, field)
    if "is_active" in payload.model_fields_set:
        values["is_active"] = bool(payload.is_active)
    if "admin_note" in payload.model_fields_set:
        values["admin_note"] = (
            payload.admin_note.strip() if payload.admin_note else None
        )
    return values


def racket_model_to_dto(model: RacketModelCatalog) -> AdminRacketModelOut:
    return AdminRacketModelOut(
        id=model.id,
        key=model.model_key,
        brand=model.brand,
        model=model.model,
        is_active=model.is_active,
        created_at=model.created_at.isoformat(),
        updated_at=model.updated_at.isoformat(),
    )


@router.post("/strings/{string_id}/image", response_model=StringOut)
async def admin_upload_string_image(
    string_id: str,
    photo: UploadFile = File(...),
    _: CurrentUser = Depends(get_current_admin),
    catalog_repository=Depends(get_catalog_repository),
    db: Session = Depends(get_db, scope="function"),
) -> StringOut:
    existing = GetStringUseCase(catalog_repository=catalog_repository).execute(
        string_id=string_id,
        include_inactive=True,
    )
    image_path = await save_string_image_upload(photo)
    register_created_file(db, image_path, delete_string_catalog_image)
    previous_image_path = existing.image_url
    item = UpdateStringUseCase(catalog_repository=catalog_repository).execute(
        string_id=string_id,
        values={"catalog": {"image_url": image_path}},
    )

    if previous_image_path:
        register_removed_file(db, previous_image_path, delete_string_catalog_image)
    return string_to_dto(item)


@router.delete("/strings/{string_id}/image", response_model=StringOut)
def admin_delete_string_image(
    string_id: str,
    _: CurrentUser = Depends(get_current_admin),
    catalog_repository=Depends(get_catalog_repository),
    db: Session = Depends(get_db, scope="function"),
) -> StringOut:
    existing = GetStringUseCase(catalog_repository=catalog_repository).execute(
        string_id=string_id,
        include_inactive=True,
    )
    item = UpdateStringUseCase(catalog_repository=catalog_repository).execute(
        string_id=string_id,
        values={"catalog": {"image_url": None}},
    )
    if existing.image_url:
        register_removed_file(db, existing.image_url, delete_string_catalog_image)
    return string_to_dto(item)


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
    catalog_repository=Depends(get_catalog_repository),
) -> dict[str, object]:
    page = ListInventoryStringsUseCase(catalog_repository=catalog_repository).execute(
        brand=brand,
        search=search,
        availability=availability,
        limit=limit,
        offset=offset,
    )
    return page_to_dict(page, lambda item: inventory_string_to_dto(item).model_dump())


@router.get("/racket-models", response_model=list[AdminRacketModelOut])
def admin_racket_models(
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db, scope="function"),
) -> list[AdminRacketModelOut]:
    models = (
        db.execute(
            select(RacketModelCatalog).order_by(
                RacketModelCatalog.is_active.desc(),
                RacketModelCatalog.brand.asc(),
                RacketModelCatalog.model.asc(),
            )
        )
        .scalars()
        .all()
    )
    return [racket_model_to_dto(model) for model in models]


@router.post("/racket-models", response_model=AdminRacketModelOut)
def admin_create_racket_model(
    payload: CreateRacketModelPayload,
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db, scope="function"),
) -> AdminRacketModelOut:
    model_key = normalize_racket_model_key(payload.brand, payload.model)
    if model_key is None:
        raise BadRequestError("Brand and model must contain letters or numbers")
    existing = db.execute(
        select(RacketModelCatalog).where(
            RacketModelCatalog.model_key == model_key,
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise ConflictError("Racket model already exists")
    model = RacketModelCatalog(
        model_key=model_key,
        brand=payload.brand,
        model=payload.model,
        is_active=True,
    )
    db.add(model)
    db.flush()
    db.refresh(model)
    return racket_model_to_dto(model)


@router.patch("/racket-models/{racket_model_id}", response_model=AdminRacketModelOut)
def admin_update_racket_model(
    racket_model_id: str,
    payload: UpdateRacketModelPayload,
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db, scope="function"),
) -> AdminRacketModelOut:
    model = db.get(RacketModelCatalog, racket_model_id)
    if model is None:
        raise NotFoundError("Racket model not found")
    model.is_active = payload.is_active
    db.flush()
    db.refresh(model)
    return racket_model_to_dto(model)


@router.get("/users/overview", response_model=AdminUsersOverviewOut)
def admin_users_overview(
    limit: int = Query(default=100, ge=1, le=100),
    search: str | None = Query(default=None, max_length=100),
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db, scope="function"),
) -> AdminUsersOverviewOut:
    total_users = db.scalar(select(func.count(User.id))) or 0
    active_users = (
        db.scalar(select(func.count(User.id)).where(User.is_active.is_(True))) or 0
    )
    player_count = (
        db.scalar(select(func.count(User.id)).where(User.role == "customer")) or 0
    )
    admin_count = (
        db.scalar(select(func.count(User.id)).where(User.role == "admin")) or 0
    )
    user_query = select(
        User.id,
        User.username,
        User.role,
        User.is_active,
        User.created_at,
    )
    normalized_search = search.strip() if search else ""
    if normalized_search:
        escaped_search = normalized_search.replace("\\", "\\\\")
        escaped_search = escaped_search.replace("%", "\\%").replace("_", "\\_")
        user_query = user_query.where(
            User.username.ilike(f"%{escaped_search}%", escape="\\")
        )
    rows = db.execute(
        user_query.order_by(User.created_at.desc(), User.id.desc()).limit(limit)
    ).all()
    return AdminUsersOverviewOut(
        total_users=total_users,
        active_users=active_users,
        player_count=player_count,
        admin_count=admin_count,
        users=[
            AdminUserSummaryOut(
                id=row.id,
                username=row.username,
                role=row.role,
                is_active=row.is_active,
                created_at=row.created_at.isoformat() if row.created_at else None,
            )
            for row in rows
        ],
    )


@router.get("/users/{user_id}", response_model=AdminUserDetailOut)
def admin_user_detail(
    user_id: str,
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db, scope="function"),
) -> AdminUserDetailOut:
    user = db.execute(
        select(
            User.id,
            User.username,
            User.phone_number,
            User.role,
            User.is_active,
            User.created_at,
        ).where(User.id == user_id)
    ).one_or_none()
    if user is None:
        raise NotFoundError("User not found")

    profile = db.execute(
        select(
            Profile.skill_level,
            Profile.playing_style,
            Profile.preferred_tension,
            Profile.frequency_per_week,
            Profile.preferred_feel,
            Profile.preferred_gauge,
            Profile.recent_goal,
        ).where(Profile.user_id == user.id)
    ).one_or_none()
    profile_dto = (
        AdminUserProfileOut(
            skill_level=profile.skill_level,
            playing_style=profile.playing_style,
            preferred_tension=(
                float(profile.preferred_tension)
                if profile.preferred_tension is not None
                else None
            ),
            frequency_per_week=profile.frequency_per_week,
            preferred_feel=profile.preferred_feel,
            preferred_gauge=profile.preferred_gauge,
            recent_goal=profile.recent_goal,
        )
        if profile is not None
        else None
    )

    booking_rows = db.execute(
        select(
            Booking.id,
            Booking.string_id,
            StringCatalogItem.display_name,
            Booking.racket_model,
            Booking.requested_tension,
            Booking.status,
            Booking.drop_off_datetime,
            Booking.created_at,
        )
        .outerjoin(
            StringCatalogItem,
            StringCatalogItem.catalog_id == Booking.string_id,
        )
        .where(Booking.user_id == user.id)
        .order_by(Booking.created_at.desc(), Booking.id.desc())
        .limit(5)
    ).all()

    return AdminUserDetailOut(
        id=user.id,
        username=user.username,
        phone_number=user.phone_number,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else None,
        profile=profile_dto,
        recent_orders=[
            AdminUserBookingOut(
                id=row.id,
                order_code=booking_order_code(row.id),
                string_name=row.display_name or f"Archived string ({row.string_id})",
                racket_model=row.racket_model,
                requested_tension=(
                    float(row.requested_tension)
                    if row.requested_tension is not None
                    else None
                ),
                status=row.status,
                drop_off_datetime=(
                    row.drop_off_datetime.isoformat() if row.drop_off_datetime else None
                ),
                created_at=row.created_at.isoformat() if row.created_at else None,
            )
            for row in booking_rows
        ],
    )


@router.get("/inventory/strings/{string_id}", response_model=AdminInventoryStringOut)
def admin_inventory_string_detail(
    string_id: str,
    _: CurrentUser = Depends(get_current_admin),
    catalog_repository=Depends(get_catalog_repository),
) -> AdminInventoryStringOut:
    item = GetStringUseCase(catalog_repository=catalog_repository).execute(
        string_id=string_id,
        include_inactive=True,
    )
    return inventory_string_to_dto(item)


@router.patch("/inventory/strings/{string_id}", response_model=AdminInventoryStringOut)
def admin_update_inventory_string(
    string_id: str,
    payload: InventoryUpdatePayload,
    _: CurrentUser = Depends(get_current_admin),
    catalog_repository=Depends(get_catalog_repository),
) -> AdminInventoryStringOut:
    item = UpdateInventoryStringUseCase(catalog_repository=catalog_repository).execute(
        string_id=string_id,
        values=inventory_update_values(payload),
    )
    return inventory_string_to_dto(item)


@router.put(
    "/inventory/strings/{string_id}/editor",
    response_model=AdminInventoryStringOut,
)
def admin_update_string_editor(
    string_id: str,
    payload: StringEditorUpdatePayload,
    _: CurrentUser = Depends(get_current_admin),
    catalog_repository=Depends(get_catalog_repository),
) -> AdminInventoryStringOut:
    catalog_values: dict[str, object] = {}
    if payload.catalog is not None:
        _prepare_string_values().execute(
            brand=payload.catalog.brand,
            model_name=payload.catalog.model_name,
            overrides={},
        )
        catalog_values = payload.catalog.model_dump(
            exclude_none=True,
            exclude={"brand", "price_rm"},
        )

    inventory_values = (
        inventory_update_values(payload.inventory)
        if payload.inventory is not None
        else {}
    )
    official_performance_values = (
        payload.official_performance.model_dump(exclude_none=True)
        if payload.official_performance is not None
        else {}
    )
    item = UpdateStringEditorUseCase(catalog_repository=catalog_repository).execute(
        string_id=string_id,
        catalog_values=catalog_values,
        inventory_values=inventory_values,
        official_performance_values=official_performance_values,
    )
    return inventory_string_to_dto(item)


@router.get(
    "/strings/{string_id}/official-performance",
    response_model=OfficialPerformanceOut,
)
def admin_get_official_performance(
    string_id: str,
    _: CurrentUser = Depends(get_current_admin),
    catalog_repository=Depends(get_catalog_repository),
) -> OfficialPerformanceOut:
    item = GetOfficialPerformanceUseCase(catalog_repository=catalog_repository).execute(
        string_id=string_id
    )
    return official_performance_to_dto(item)


@router.get(
    "/strings/{string_id}/recommendation-matrix",
    response_model=RecommendationMatrixInspectionOut,
)
def admin_get_recommendation_matrix(
    string_id: str,
    _: CurrentUser = Depends(get_current_admin),
    catalog_repository=Depends(get_catalog_repository),
) -> RecommendationMatrixInspectionOut:
    item = GetRecommendationMatrixUseCase(
        catalog_repository=catalog_repository
    ).execute(string_id=string_id)
    return recommendation_matrix_inspection_to_dto(item)


@router.post(
    "/recommendation-matrix/import",
    response_model=RecommendationMatrixImportReportOut,
)
def admin_import_recommendation_matrix(
    _: CurrentUser = Depends(get_current_admin),
    catalog_repository=Depends(get_catalog_repository),
) -> RecommendationMatrixImportReportOut:
    report = ImportRecommendationMatrixUseCase(
        catalog_repository=catalog_repository,
        matrix_path=get_settings().recommendation_matrix_path,
    ).execute()
    return recommendation_matrix_import_report_to_dto(report)


@router.get("/bookings", response_model=dict)
def admin_bookings(
    status: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=100),
    sort_by: BookingSortField = Query(default="updated_at"),
    sort_order: SortOrder = Query(default="desc"),
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: CurrentUser = Depends(get_current_admin),
    booking_repository=Depends(get_booking_repository),
) -> dict[str, object]:
    page = ListAdminBookingsUseCase(booking_repository=booking_repository).execute(
        status=status,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )
    return page_to_dict(
        page,
        lambda item: booking_to_dto(
            item, include_user=True, include_history=True
        ).model_dump(),
    )


@router.get("/bookings/{booking_id}", response_model=BookingOut)
def admin_get_booking(
    booking_id: str,
    _: CurrentUser = Depends(get_current_admin),
    booking_repository=Depends(get_booking_repository),
) -> BookingOut:
    booking = GetBookingUseCase(booking_repository=booking_repository).execute(
        booking_id
    )
    return booking_to_dto(booking, include_user=True, include_history=True)


@router.patch("/bookings/{booking_id}/status", response_model=BookingOut)
def admin_update_booking_status(
    booking_id: str,
    payload: UpdateBookingStatusPayload,
    current_user: CurrentUser = Depends(get_current_admin),
    booking_repository=Depends(get_booking_repository),
    db: Session = Depends(get_db, scope="function"),
) -> BookingOut:
    booking = UpdateBookingStatusUseCase(
        booking_repository=booking_repository,
    ).execute(
        booking_id=booking_id,
        next_status=payload.status,
        expected_completion_datetime=payload.expected_completion_datetime,
        update_expected_completion_datetime=(
            "expected_completion_datetime" in payload.model_fields_set
        ),
        changed_by_user_id=current_user.user_id,
        note=payload.note,
    )
    if payload.status == "completed":
        db.execute(
            delete(RecommendationScoreCache).where(
                RecommendationScoreCache.algorithm_version == ALGORITHM_VERSION
            )
        )
    return booking_to_dto(booking, include_user=True, include_history=True)


@router.post("/bookings/{booking_id}/updates", response_model=BookingOut)
async def admin_add_booking_update(
    booking_id: str,
    comment: str | None = Form(default=None),
    photo: UploadFile | None = File(default=None),
    photo_type: BookingPhotoType = Form(default="other"),
    current_user: CurrentUser = Depends(get_current_admin),
    booking_repository=Depends(get_booking_repository),
    db: Session = Depends(get_db, scope="function"),
) -> BookingOut:
    GetBookingUseCase(booking_repository=booking_repository).execute(booking_id)
    photo_path = None
    photo_original_name = None
    photo_content_type = None
    if photo is not None:
        (
            photo_path,
            photo_original_name,
            photo_content_type,
        ) = await save_update_photo_upload(photo)
        register_created_file(db, photo_path, delete_booking_update_photo)

    booking = AddBookingUpdateUseCase(booking_repository=booking_repository).execute(
        booking_id=booking_id,
        author_user_id=current_user.user_id,
        author_role=current_user.role,
        comment=comment,
        photo_path=photo_path,
        photo_original_name=photo_original_name,
        photo_content_type=photo_content_type,
        photo_type=photo_type if photo_path else None,
    )
    return booking_to_dto(booking, include_user=True, include_history=True)


@router.post("/bookings/{booking_id}/photos", response_model=BookingOut)
async def admin_upload_booking_photo(
    booking_id: str,
    photo: UploadFile = File(...),
    comment: str | None = Form(default=None),
    photo_type: BookingPhotoType = Form(default="racket"),
    current_user: CurrentUser = Depends(get_current_admin),
    booking_repository=Depends(get_booking_repository),
    db: Session = Depends(get_db, scope="function"),
) -> BookingOut:
    GetBookingUseCase(booking_repository=booking_repository).execute(booking_id)
    (
        photo_path,
        photo_original_name,
        photo_content_type,
    ) = await save_update_photo_upload(photo)
    register_created_file(db, photo_path, delete_booking_update_photo)
    booking = AddBookingUpdateUseCase(booking_repository=booking_repository).execute(
        booking_id=booking_id,
        author_user_id=current_user.user_id,
        author_role=current_user.role,
        comment=comment,
        photo_path=photo_path,
        photo_original_name=photo_original_name,
        photo_content_type=photo_content_type,
        photo_type=photo_type,
    )
    return booking_to_dto(booking, include_user=True, include_history=True)


@router.get("/recommendations/runs", response_model=dict)
def admin_recommendation_runs(
    phone_number: str | None = Query(default=None, max_length=30),
    algorithm_version: str | None = Query(default=None, max_length=80),
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: CurrentUser = Depends(get_current_admin),
    recommendation_run_repository=Depends(get_recommendation_run_repository),
) -> dict[str, object]:
    page = ListRecommendationRunsUseCase(
        recommendation_run_repository=recommendation_run_repository
    ).execute(
        phone_number=phone_number,
        algorithm_version=algorithm_version,
        limit=limit,
        offset=offset,
    )
    return page_to_dict(page, recommendation_run_to_dict)


@router.get("/recommendations/runs/{run_id}", response_model=dict)
def admin_recommendation_run_detail(
    run_id: str,
    _: CurrentUser = Depends(get_current_admin),
    recommendation_run_repository=Depends(get_recommendation_run_repository),
) -> dict[str, object]:
    run = GetRecommendationRunUseCase(
        recommendation_run_repository=recommendation_run_repository
    ).execute(run_id)
    return recommendation_run_to_dict(run)


@router.get("/business-hours", response_model=StoreBusinessHoursOut)
def admin_get_business_hours(
    _: CurrentUser = Depends(get_current_admin),
    store_repository=Depends(get_store_repository),
) -> StoreBusinessHoursOut:
    hours = GetBusinessHoursUseCase(store_repository=store_repository).execute()
    return business_hours_to_dto(hours)


@router.put("/business-hours", response_model=StoreBusinessHoursOut)
def admin_update_business_hours(
    payload: StoreBusinessHoursPayload,
    _: CurrentUser = Depends(get_current_admin),
    store_repository=Depends(get_store_repository),
) -> StoreBusinessHoursOut:
    _validate_closed_dates_not_in_past(payload.special_closed_dates)
    hours = UpdateBusinessHoursUseCase(store_repository=store_repository).execute(
        days=[day.model_dump() for day in payload.days],
        special_closed_dates=payload.special_closed_dates,
    )
    return business_hours_to_dto(hours)


@router.get("/check-in/lookup", response_model=CheckInLookupOut)
def admin_lookup_check_in(
    reference: str = Query(min_length=1, max_length=120),
    _: CurrentUser = Depends(get_current_admin),
    booking_repository=Depends(get_booking_repository),
) -> CheckInLookupOut:
    lookup = LookupCheckInUseCase(booking_repository=booking_repository).execute(
        booking_id=None,
        reference=reference,
    )
    return CheckInLookupOut(
        matched_by=cast(Literal["booking_id", "check_in_reference"], lookup.matched_by),
        booking=booking_to_dto(
            lookup.booking,
            include_user=True,
            include_history=True,
        ).model_dump(),
    )


@router.post("/check-in", response_model=BookingOut)
def admin_check_in_booking(
    payload: CheckInPayload,
    current_user: CurrentUser = Depends(get_current_admin),
    booking_repository=Depends(get_booking_repository),
) -> BookingOut:
    lookup_use_case = LookupCheckInUseCase(booking_repository=booking_repository)
    booking = ConfirmCheckInUseCase(
        booking_repository=booking_repository,
        lookup_check_in_use_case=lookup_use_case,
    ).execute(
        booking_id=payload.booking_id,
        reference=payload.reference,
        admin_user_id=current_user.user_id,
        note=payload.note,
    )
    return booking_to_dto(booking, include_user=True, include_history=True)


def _active_check_in_token(
    db: Session,
    *,
    raw_token: str,
    now,
    lock: bool,
) -> CheckInToken:
    query = select(CheckInToken).where(
        CheckInToken.token_hash == hash_check_in_token(raw_token),
        CheckInToken.used_at.is_(None),
        CheckInToken.revoked_at.is_(None),
        CheckInToken.expires_at > now,
    )
    if lock:
        query = query.with_for_update()
    token = db.scalar(query)
    if token is None:
        raise BadRequestError("QR token is invalid, expired, or already used")
    return token


@router.post("/check-in/lookup", response_model=CheckInLookupOut)
def admin_lookup_secure_check_in(
    payload: SecureCheckInPayload,
    _: CurrentUser = Depends(get_current_admin),
    booking_repository=Depends(get_booking_repository),
    clock=Depends(get_clock),
    db: Session = Depends(get_db, scope="function"),
) -> CheckInLookupOut:
    token = _active_check_in_token(
        db,
        raw_token=payload.token,
        now=clock.now(),
        lock=False,
    )
    booking = GetBookingUseCase(booking_repository=booking_repository).execute(
        token.booking_id
    )
    return CheckInLookupOut(
        matched_by="qr_token",
        booking=booking_to_dto(
            booking,
            include_user=True,
            include_history=True,
        ).model_dump(),
    )


@router.post("/check-in/confirm", response_model=BookingOut)
def admin_confirm_secure_check_in(
    payload: SecureCheckInPayload,
    current_user: CurrentUser = Depends(get_current_admin),
    booking_repository=Depends(get_booking_repository),
    clock=Depends(get_clock),
    db: Session = Depends(get_db, scope="function"),
) -> BookingOut:
    now = clock.now()
    token = _active_check_in_token(
        db,
        raw_token=payload.token,
        now=now,
        lock=True,
    )
    token.used_at = now
    booking = ConfirmCheckInUseCase(
        booking_repository=booking_repository,
        lookup_check_in_use_case=LookupCheckInUseCase(
            booking_repository=booking_repository
        ),
    ).execute(
        booking_id=token.booking_id,
        reference=None,
        admin_user_id=current_user.user_id,
        note=payload.note,
    )
    return booking_to_dto(booking, include_user=True, include_history=True)


@router.get("/service-queue", response_model=ServiceQueueOut)
def admin_service_queue(
    _: CurrentUser = Depends(get_current_admin),
    booking_repository=Depends(get_booking_repository),
) -> ServiceQueueOut:
    queue = GetQueueUseCase(booking_repository=booking_repository).execute()
    return ServiceQueueOut(
        generated_at=queue.generated_at,
        lanes=[
            ServiceQueueLaneOut(
                status=lane.status,
                title=lane.title,
                items=[
                    ServiceQueueItemOut(
                        queue_position=item.queue_position,
                        booking=booking_to_dto(
                            item.booking,
                            include_user=True,
                            include_history=True,
                        ).model_dump(),
                    )
                    for item in lane.items
                ],
            )
            for lane in queue.lanes
        ],
    )


@router.get("/store-settings", response_model=StoreSettingsOut)
def admin_get_store_settings(
    _: CurrentUser = Depends(get_current_admin),
    store_repository=Depends(get_store_repository),
) -> StoreSettingsOut:
    settings = GetStoreSettingsUseCase(store_repository=store_repository).execute()
    return settings_to_dto(settings)


@router.put("/store-settings", response_model=StoreSettingsOut)
def admin_update_store_settings(
    payload: StoreSettingsPayload,
    _: CurrentUser = Depends(get_current_admin),
    store_repository=Depends(get_store_repository),
) -> StoreSettingsOut:
    settings = UpdateStoreSettingsUseCase(store_repository=store_repository).execute(
        payload.model_dump()
    )
    return settings_to_dto(settings)


@router.post("/store-settings/payment-qr", response_model=StoreSettingsOut)
async def admin_upload_payment_qr(
    photo: UploadFile = File(...),
    _: CurrentUser = Depends(get_current_admin),
    store_repository=Depends(get_store_repository),
    db: Session = Depends(get_db, scope="function"),
) -> StoreSettingsOut:
    existing = GetStoreSettingsUseCase(store_repository=store_repository).execute()
    content = await read_upload_bytes_limited(
        photo,
        oversize_message="Payment QR must be 5 MB or smaller",
    )
    image_path = save_payment_qr(
        content=content,
        content_type=photo.content_type,
        original_name=photo.filename,
    )
    register_created_file(db, image_path, delete_payment_qr)
    settings = UpdateStoreSettingsUseCase(store_repository=store_repository).execute(
        {"payment_qr_path": image_path}
    )
    if existing.payment_qr_path:
        register_removed_file(db, existing.payment_qr_path, delete_payment_qr)
    return settings_to_dto(settings)


@router.delete("/store-settings/payment-qr", response_model=StoreSettingsOut)
def admin_delete_payment_qr(
    _: CurrentUser = Depends(get_current_admin),
    store_repository=Depends(get_store_repository),
    db: Session = Depends(get_db, scope="function"),
) -> StoreSettingsOut:
    existing = GetStoreSettingsUseCase(store_repository=store_repository).execute()
    settings = UpdateStoreSettingsUseCase(store_repository=store_repository).execute(
        {"payment_qr_path": None}
    )
    if existing.payment_qr_path:
        register_removed_file(db, existing.payment_qr_path, delete_payment_qr)
    return settings_to_dto(settings)
