from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from stringsense_backend.db.session import get_db
from stringsense_backend.modules.admin import router as admin_router
from stringsense_backend.modules.auth import router as auth_router
from stringsense_backend.modules.bookings import router as bookings_router
from stringsense_backend.modules.health import health_payload
from stringsense_backend.modules.profile import router as profile_router
from stringsense_backend.modules.recommendations import router as recommendations_router
from stringsense_backend.modules.strings import router as strings_router


router = APIRouter()


@router.get("/health")
def api_health(db: Session = Depends(get_db)) -> dict[str, object]:
    return health_payload(db)


router.include_router(auth_router)
router.include_router(profile_router)
router.include_router(strings_router)
router.include_router(bookings_router)
router.include_router(recommendations_router)
router.include_router(admin_router)
