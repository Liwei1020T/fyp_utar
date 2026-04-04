from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.health import health_payload
from app.api.v1.admin_bookings import router as admin_bookings_router
from app.api.v1.admin_logs import router as admin_logs_router
from app.api.v1.admin_strings import router as admin_strings_router
from app.api.v1.auth import router as auth_router
from app.db.session import get_db

from app.api.v1.bookings import router as bookings_router
from app.api.v1.profile import router as profile_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.strings import router as strings_router


router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    return health_payload(db)


router.include_router(profile_router)
router.include_router(auth_router)
router.include_router(strings_router)
router.include_router(admin_strings_router)
router.include_router(admin_logs_router)
router.include_router(bookings_router)
router.include_router(admin_bookings_router)
router.include_router(recommendations_router)
