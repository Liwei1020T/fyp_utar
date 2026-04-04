from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user
from app.api.responses import paginated_success_response
from app.api.responses import success_response
from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.schemas.query import PublicStringSortField
from app.schemas.query import SortOrder
from app.services.string_service import string_service


router = APIRouter(prefix="/strings", tags=["strings"])


@router.get("")
def list_strings(
    search: str | None = Query(default=None, max_length=100),
    brand: str | None = Query(default=None, max_length=100),
    sort_by: PublicStringSortField = Query(default=PublicStringSortField.BRAND),
    sort_order: SortOrder = Query(default=SortOrder.ASC),
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    items, total = string_service.list_active(
        db,
        search=search,
        brand=brand,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )
    return paginated_success_response(
        message="Strings fetched successfully",
        data=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{string_id}")
def get_string_detail(
    string_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    item = string_service.get(db, string_id)
    if item is None:
        raise NotFoundError("String not found")

    return success_response(message="String fetched successfully", data=item)
