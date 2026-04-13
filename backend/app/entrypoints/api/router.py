from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.session import check_database_connection
from app.adapters.persistence.sqlalchemy.session import get_db
from app.entrypoints.api.routes.admin_routes import router as admin_router
from app.entrypoints.api.routes.auth_routes import router as auth_router
from app.entrypoints.api.routes.booking_routes import router as booking_router
from app.entrypoints.api.routes.catalog_routes import router as catalog_router
from app.entrypoints.api.routes.media_routes import router as media_router
from app.entrypoints.api.routes.profile_routes import router as profile_router
from app.entrypoints.api.routes.recommendation_routes import (
    router as recommendation_router,
)
from app.entrypoints.api.routes.store_routes import router as store_router


router = APIRouter()


@router.get("/health")
def api_health(db: Session = Depends(get_db)) -> dict[str, object]:
    check_database_connection(db)
    return {"status": "ok", "service": "backend"}


router.include_router(auth_router)
router.include_router(profile_router)
router.include_router(catalog_router)
router.include_router(media_router)
router.include_router(booking_router)
router.include_router(recommendation_router)
router.include_router(admin_router)
router.include_router(store_router)
