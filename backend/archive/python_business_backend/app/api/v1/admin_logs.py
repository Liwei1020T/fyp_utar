from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_admin
from app.api.responses import paginated_success_response
from app.db.session import get_db
from app.services.recommendation_service import recommendation_service


router = APIRouter(prefix="/admin/recommendation-logs", tags=["admin-logs"])


@router.get("")
def list_recommendation_logs(
    phone_number: str | None = Query(default=None, max_length=30),
    algorithm_version: str | None = Query(default=None, max_length=50),
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict:
    items, total = recommendation_service.logs(
        db,
        phone_number=phone_number,
        algorithm_version=algorithm_version,
        limit=limit,
        offset=offset,
    )
    return paginated_success_response(
        message="Recommendation logs fetched successfully",
        data=items,
        total=total,
        limit=limit,
        offset=offset,
    )
