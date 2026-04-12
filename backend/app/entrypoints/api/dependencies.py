from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_booking_repository import (
    SqlAlchemyBookingRepository,
)
from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_catalog_repository import (
    SqlAlchemyCatalogRepository,
)
from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_password_reset_repository import (
    SqlAlchemyPasswordResetRepository,
)
from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_profile_repository import (
    SqlAlchemyProfileRepository,
)
from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_recommendation_log_repository import (
    SqlAlchemyRecommendationLogRepository,
)
from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_recommendation_repository import (
    SqlAlchemyRecommendationRepository,
)
from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_store_repository import (
    SqlAlchemyStoreRepository,
)
from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from app.adapters.persistence.sqlalchemy.session import get_db
from app.adapters.services.ai.rag_adapter import RagAdapter
from app.adapters.services.ai.recommendation_engine_adapter import (
    RecommendationEngineAdapter,
)
from app.adapters.services.ai.review_analysis_adapter import ReviewAnalysisAdapter
from app.adapters.services.security.jwt_token_service import JwtTokenService
from app.adapters.services.security.pbkdf2_password_hasher import (
    Pbkdf2PasswordHasher,
)
from app.adapters.services.system_clock import SystemClock
from app.domain.auth.entities import UserRole
from app.shared.errors import ForbiddenError
from app.shared.errors import UnauthorizedError


class CurrentUser(BaseModel):
    sub: str
    user_id: str
    phone_number: str
    role: str


security = HTTPBearer(auto_error=False)

_password_hasher = Pbkdf2PasswordHasher()
_token_service = JwtTokenService()
_clock = SystemClock()
_recommendation_engine = RecommendationEngineAdapter()
_review_analysis_service = ReviewAnalysisAdapter()
_rag_service = RagAdapter()


def get_password_hasher() -> Pbkdf2PasswordHasher:
    return _password_hasher


def get_token_service() -> JwtTokenService:
    return _token_service


def get_clock() -> SystemClock:
    return _clock


def get_recommendation_engine() -> RecommendationEngineAdapter:
    return _recommendation_engine


def get_review_analysis_service() -> ReviewAnalysisAdapter:
    return _review_analysis_service


def get_rag_service() -> RagAdapter:
    return _rag_service


def get_user_repository(db: Session = Depends(get_db)) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(db)


def get_password_reset_repository(
    db: Session = Depends(get_db),
) -> SqlAlchemyPasswordResetRepository:
    return SqlAlchemyPasswordResetRepository(db)


def get_profile_repository(
    db: Session = Depends(get_db),
) -> SqlAlchemyProfileRepository:
    return SqlAlchemyProfileRepository(db)


def get_catalog_repository(
    db: Session = Depends(get_db),
) -> SqlAlchemyCatalogRepository:
    return SqlAlchemyCatalogRepository(db)


def get_booking_repository(
    db: Session = Depends(get_db),
) -> SqlAlchemyBookingRepository:
    return SqlAlchemyBookingRepository(db)


def get_store_repository(db: Session = Depends(get_db)) -> SqlAlchemyStoreRepository:
    return SqlAlchemyStoreRepository(db)


def get_recommendation_log_repository(
    db: Session = Depends(get_db),
) -> SqlAlchemyRecommendationLogRepository:
    return SqlAlchemyRecommendationLogRepository(db)


def get_recommendation_repository(
    db: Session = Depends(get_db),
) -> SqlAlchemyRecommendationRepository:
    return SqlAlchemyRecommendationRepository(db)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    token_service: JwtTokenService = Depends(get_token_service),
) -> CurrentUser:
    if credentials is None:
        raise UnauthorizedError("Missing bearer token")
    payload = token_service.verify_access_token(credentials.credentials)
    if payload is None:
        raise UnauthorizedError("Invalid access token")
    return CurrentUser(**payload.__dict__)


def require_roles(user: CurrentUser, *roles: UserRole) -> CurrentUser:
    allowed = {role.value for role in roles}
    if user.role not in allowed:
        raise ForbiddenError("Insufficient permissions for this resource")
    return user


def get_current_customer(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return require_roles(user, UserRole.CUSTOMER, UserRole.ADMIN)


def get_current_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return require_roles(user, UserRole.ADMIN)
