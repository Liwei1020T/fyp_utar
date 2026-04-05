from __future__ import annotations

from app.entrypoints.api.dependencies import CurrentUser
from app.entrypoints.api.dependencies import get_booking_repository
from app.entrypoints.api.dependencies import get_catalog_repository
from app.entrypoints.api.dependencies import get_clock
from app.entrypoints.api.dependencies import get_current_admin
from app.entrypoints.api.dependencies import get_current_customer
from app.entrypoints.api.dependencies import get_current_user
from app.entrypoints.api.dependencies import get_db
from app.entrypoints.api.dependencies import get_password_hasher
from app.entrypoints.api.dependencies import get_password_reset_repository
from app.entrypoints.api.dependencies import get_profile_repository
from app.entrypoints.api.dependencies import get_rag_service
from app.entrypoints.api.dependencies import get_recommendation_engine
from app.entrypoints.api.dependencies import get_recommendation_log_repository
from app.entrypoints.api.dependencies import get_review_analysis_service
from app.entrypoints.api.dependencies import get_store_repository
from app.entrypoints.api.dependencies import get_token_service
from app.entrypoints.api.dependencies import get_user_repository
from app.entrypoints.api.dependencies import require_roles
from app.entrypoints.api.dependencies import security

__all__ = [
    "CurrentUser",
    "get_booking_repository",
    "get_catalog_repository",
    "get_clock",
    "get_current_admin",
    "get_current_customer",
    "get_current_user",
    "get_db",
    "get_password_hasher",
    "get_password_reset_repository",
    "get_profile_repository",
    "get_rag_service",
    "get_recommendation_engine",
    "get_recommendation_log_repository",
    "get_review_analysis_service",
    "get_store_repository",
    "get_token_service",
    "get_user_repository",
    "require_roles",
    "security",
]
