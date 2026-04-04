import json

from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import Query
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_admin
from app.api.responses import paginated_success_response
from app.api.responses import success_response
from app.core.exceptions import BadRequestError
from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.schemas.query import AdminStringSortField
from app.schemas.query import SortOrder
from app.schemas.string import StringPayload
from app.services.string_import_service import import_strings_rows
from app.services.string_import_service import parse_import_rows
from app.services.string_service import string_service


router = APIRouter(prefix="/admin/strings", tags=["admin-strings"])


@router.get("")
def list_strings(
    search: str | None = Query(default=None, max_length=100),
    brand: str | None = Query(default=None, max_length=100),
    is_active: bool | None = Query(default=None),
    sort_by: AdminStringSortField = Query(default=AdminStringSortField.UPDATED_AT),
    sort_order: SortOrder = Query(default=SortOrder.DESC),
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict:
    items, total = string_service.list_all(
        db,
        search=search,
        brand=brand,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )
    return paginated_success_response(
        message="Admin strings fetched successfully",
        data=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("")
def create_string(
    payload: StringPayload,
    user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict:
    item = string_service.create(db, payload)
    return success_response(message="String created successfully", data=item)


@router.post("/import")
async def import_strings(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict:
    if not file.filename:
        raise BadRequestError("Import file must include a filename")

    try:
        rows = parse_import_rows(
            filename=file.filename,
            content=await file.read(),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise BadRequestError("Invalid import file") from exc

    summary = import_strings_rows(db, rows)
    db.commit()
    return success_response(message="Strings imported successfully", data=summary)


@router.put("/{string_id}")
def update_string(
    string_id: str,
    payload: StringPayload,
    user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict:
    item = string_service.update(db, string_id, payload)
    if item is None:
        raise NotFoundError("String not found")

    return success_response(message="String updated successfully", data=item)


@router.delete("/{string_id}")
def delete_string(
    string_id: str,
    user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict:
    item = string_service.deactivate(db, string_id)
    if item is None:
        raise NotFoundError("String not found")

    return success_response(message="String deactivated successfully", data=item)
