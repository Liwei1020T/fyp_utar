from __future__ import annotations

from app.adapters.persistence.sqlalchemy.models.booking import Booking
from app.adapters.persistence.sqlalchemy.models.booking import BookingStatusHistory
from app.adapters.persistence.sqlalchemy.models.booking import BookingUpdate
from app.adapters.persistence.sqlalchemy.models.password_reset_code import (
    PasswordResetCode,
)
from app.adapters.persistence.sqlalchemy.models.profile import Profile
from app.adapters.persistence.sqlalchemy.models.recommendation_log import (
    RecommendationLog,
)
from app.adapters.persistence.sqlalchemy.models.store_business_hours import (
    StoreBusinessHours,
)
from app.adapters.persistence.sqlalchemy.models.store_settings import StoreSettings
from app.adapters.persistence.sqlalchemy.models.string_catalog_item import Brand
from app.adapters.persistence.sqlalchemy.models.string_catalog_item import (
    InventoryMovement,
)
from app.adapters.persistence.sqlalchemy.models.string_catalog_item import (
    RecommendationFeatureDefinition,
)
from app.adapters.persistence.sqlalchemy.models.string_catalog_item import (
    RecommendationScoreCache,
)
from app.adapters.persistence.sqlalchemy.models.string_catalog_item import (
    StringCatalogItem,
)
from app.adapters.persistence.sqlalchemy.models.string_catalog_item import (
    StringCatalogMetric,
)
from app.adapters.persistence.sqlalchemy.models.string_catalog_item import (
    StringCatalogTag,
)
from app.adapters.persistence.sqlalchemy.models.string_catalog_item import (
    StringInventoryItem,
)
from app.adapters.persistence.sqlalchemy.models.string_catalog_item import (
    StringOfficialPerformance,
)
from app.adapters.persistence.sqlalchemy.models.string_catalog_item import (
    StringRecommendationMatrix,
)
from app.adapters.persistence.sqlalchemy.models.string_catalog_item import (
    UserPreferenceMatrix,
)
from app.adapters.persistence.sqlalchemy.models.user import User

__all__ = [
    "Brand",
    "Booking",
    "BookingStatusHistory",
    "BookingUpdate",
    "InventoryMovement",
    "PasswordResetCode",
    "Profile",
    "RecommendationFeatureDefinition",
    "RecommendationLog",
    "RecommendationScoreCache",
    "StoreBusinessHours",
    "StoreSettings",
    "StringCatalogItem",
    "StringCatalogMetric",
    "StringCatalogTag",
    "StringInventoryItem",
    "StringOfficialPerformance",
    "StringRecommendationMatrix",
    "User",
    "UserPreferenceMatrix",
]
