from app.db.base import Base
from app.db.models import (  # noqa: F401
    AppUser,
    Booking,
    BookingStatusHistory,
    CustomerProfile,
    RecommendationLog,
    String,
)


def test_core_model_tables_are_registered():
    table_names = set(Base.metadata.tables.keys())

    assert table_names == {
        "app_users",
        "customer_profiles",
        "strings",
        "string_tags",
        "bookings",
        "booking_status_history",
        "recommendation_logs",
        "password_reset_codes",
    }
