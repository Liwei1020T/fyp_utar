from __future__ import annotations

from app.adapters.persistence.sqlalchemy.models.booking import Booking
from app.adapters.persistence.sqlalchemy.models.booking import BookingStatusHistory
from app.adapters.persistence.sqlalchemy.models.booking import BookingUpdate
from app.adapters.persistence.sqlalchemy.models.booking_conversation import (
    BookingConversation,
)
from app.adapters.persistence.sqlalchemy.models.support_conversation import (
    SupportConversation,
    SupportConversationMessage,
)
from app.adapters.persistence.sqlalchemy.models.commerce import Payment
from app.adapters.persistence.sqlalchemy.models.commerce import WalletTransaction
from app.adapters.persistence.sqlalchemy.models.notification import CheckInToken
from app.adapters.persistence.sqlalchemy.models.notification import NotificationDelivery
from app.adapters.persistence.sqlalchemy.models.notification import NotificationRead
from app.adapters.persistence.sqlalchemy.models.password_reset_code import (
    PasswordResetCode,
)
from app.adapters.persistence.sqlalchemy.models.profile import Profile
from app.adapters.persistence.sqlalchemy.models.racket_feedback import BookingFeedback
from app.adapters.persistence.sqlalchemy.models.racket_feedback import Racket
from app.adapters.persistence.sqlalchemy.models.racket_feedback import (
    RacketModelCatalog,
)
from app.adapters.persistence.sqlalchemy.models.recommendation_run import (
    RecommendationRun,
)
from app.adapters.persistence.sqlalchemy.models.recommendation_run import (
    RecommendationRunItem,
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
    "BookingConversation",
    "SupportConversation",
    "SupportConversationMessage",
    "BookingFeedback",
    "BookingStatusHistory",
    "BookingUpdate",
    "CheckInToken",
    "InventoryMovement",
    "NotificationDelivery",
    "NotificationRead",
    "PasswordResetCode",
    "Payment",
    "Profile",
    "Racket",
    "RacketModelCatalog",
    "RecommendationFeatureDefinition",
    "RecommendationRun",
    "RecommendationRunItem",
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
    "WalletTransaction",
]
