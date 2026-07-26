from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy import inspect
from sqlalchemy import text

from app.config.settings import get_settings


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def make_alembic_config(database_url: str) -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_catalog_normalization_migration_preserves_existing_booking(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "catalog-migration.sqlite"
    database_url = f"sqlite+pysqlite:///{db_path}"

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("AUTO_CREATE_SCHEMA", "false")
    get_settings.cache_clear()

    config = make_alembic_config(database_url)
    command.upgrade(config, "20260411_0007")

    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO users (
                    id, username, phone_number, password_hash, role, auth_provider
                ) VALUES (
                    'user-1', 'legacy-user', '+60123334444', 'hashed', 'customer', 'local'
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO string_catalog_items (
                    id, brand, model_name, normalized_name, price_rm,
                    attack, comfort, control, durability, elasticity, sound,
                    string_movement, tension_retention, value_for_money,
                    beginner_fit_score, stability_score, all_round_score,
                    source_item_id, source_url, stock_level, admin_note,
                    is_active
                ) VALUES (
                    'legacy-bg80-id', 'Yonex', 'BG80', 'yonex bg80', 45,
                    0.90, 0.50, 0.70, 0.60, 0.80, 0.70,
                    0.40, 0.60, 0.50,
                    0.40, 0.60, 0.70,
                    '715', 'https://example.com/bg80', 6, 'Legacy admin note',
                    1
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO bookings (
                    id, user_id, string_id, racket_brand, racket_model, requested_tension,
                    status
                ) VALUES (
                    'booking-1', 'user-1', 'legacy-bg80-id', 'Yonex', 'Astrox 88D', 25,
                    'awaiting_dropoff'
                )
                """
            )
        )

    command.upgrade(config, "head")

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    assert "strings" in table_names
    assert "inventory_items" in table_names
    assert "string_recommendation_matrix" in table_names

    with engine.begin() as connection:
        string_row = (
            connection.execute(
                text(
                    """
                SELECT catalog_id, display_name, official_performance_status,
                       tension_min_lbs, tension_max_lbs
                FROM strings
                WHERE catalog_id = 'yonex-bg80'
                """
                )
            )
            .mappings()
            .one()
        )
        assert string_row["display_name"] == "Yonex BG80"
        assert string_row["official_performance_status"] == "pending_manual_fill"
        assert string_row["tension_min_lbs"] == 23
        assert string_row["tension_max_lbs"] == 28

        booking_row = (
            connection.execute(
                text("SELECT string_id FROM bookings WHERE id = 'booking-1'")
            )
            .mappings()
            .one()
        )
        assert booking_row["string_id"] == "yonex-bg80"

        inventory_row = (
            connection.execute(
                text(
                    """
                SELECT available_stock, selling_price, pricing_mode, availability_status
                FROM inventory_items
                WHERE catalog_id = 'yonex-bg80'
                """
                )
            )
            .mappings()
            .one()
        )
        assert inventory_row["available_stock"] == 6
        assert float(inventory_row["selling_price"]) == 45.0
        assert inventory_row["pricing_mode"] == "fixed_price"
        assert inventory_row["availability_status"] == "in_stock"

        matrix_rows = (
            connection.execute(
                text(
                    """
                SELECT COUNT(*) AS count
                FROM string_recommendation_matrix
                WHERE catalog_id = 'yonex-bg80'
                """
                )
            )
            .mappings()
            .one()
        )
        assert matrix_rows["count"] >= 12


def test_booking_drift_repair_migration_restores_missing_booking_columns(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "booking-drift-repair.sqlite"
    database_url = f"sqlite+pysqlite:///{db_path}"

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("AUTO_CREATE_SCHEMA", "false")
    get_settings.cache_clear()

    config = make_alembic_config(database_url)
    command.upgrade(config, "20260414_0017")

    engine = create_engine(database_url)
    with engine.begin() as connection:
        existing_string = (
            connection.execute(
                text(
                    """
                    SELECT catalog_id
                    FROM strings
                    ORDER BY catalog_id
                    LIMIT 1
                    """
                )
            )
            .mappings()
            .one()
        )

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO users (
                    id, username, phone_number, password_hash, role, auth_provider
                ) VALUES (
                    'user-1', 'drift-user', '+60123335555',
                    'hashed', 'customer', 'local'
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO bookings (
                    id, user_id, string_id, racket_brand, racket_model,
                    requested_tension, status
                ) VALUES (
                    'booking-1', 'user-1', :string_id, 'Yonex',
                    'Astrox 88D', 25, 'awaiting_dropoff'
                )
                """
            ),
            {"string_id": existing_string["catalog_id"]},
        )

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE _bookings_repaired (
                    id VARCHAR(36) NOT NULL PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL,
                    string_id VARCHAR(120) NOT NULL,
                    racket_brand VARCHAR(100),
                    racket_model VARCHAR(100),
                    requested_tension NUMERIC(4, 1),
                    drop_off_datetime DATETIME,
                    notes TEXT,
                    status VARCHAR(30) NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY(string_id) REFERENCES strings (catalog_id)
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO _bookings_repaired (
                    id, user_id, string_id, racket_brand, racket_model,
                    requested_tension, drop_off_datetime, notes, status,
                    created_at, updated_at
                )
                SELECT
                    id, user_id, string_id, racket_brand, racket_model,
                    requested_tension, drop_off_datetime, notes, status,
                    created_at, updated_at
                FROM bookings
                """
            )
        )
        connection.execute(text("DROP TABLE bookings"))
        connection.execute(text("ALTER TABLE _bookings_repaired RENAME TO bookings"))
        connection.execute(text("CREATE INDEX ix_bookings_status ON bookings (status)"))
        connection.execute(
            text("CREATE INDEX ix_bookings_string_id ON bookings (string_id)")
        )
        connection.execute(
            text("CREATE INDEX ix_bookings_user_id ON bookings (user_id)")
        )

        version_row = (
            connection.execute(text("SELECT version_num FROM alembic_version"))
            .mappings()
            .one()
        )
        assert version_row["version_num"] == "20260414_0017"

        booking_row = (
            connection.execute(
                text(
                    """
                    SELECT id, user_id, string_id, status
                    FROM bookings
                    ORDER BY created_at
                    LIMIT 1
                    """
                )
            )
            .mappings()
            .one()
        )

    inspector = inspect(engine)
    columns = {item["name"] for item in inspector.get_columns("bookings")}
    assert "expected_completion_datetime" not in columns
    assert "collection_datetime" not in columns
    assert "cancellation_reason" not in columns
    assert "completion_summary" not in columns

    command.upgrade(config, "head")

    inspector = inspect(engine)
    columns = {item["name"] for item in inspector.get_columns("bookings")}
    assert "expected_completion_datetime" in columns
    assert "collection_datetime" in columns
    assert "cancellation_reason" in columns
    assert "completion_summary" in columns

    with engine.begin() as connection:
        version_row = (
            connection.execute(text("SELECT version_num FROM alembic_version"))
            .mappings()
            .one()
        )
        assert version_row["version_num"] == "20260726_0025"

        repaired_row = (
            connection.execute(
                text(
                    """
                    SELECT id, user_id, string_id, status,
                           expected_completion_datetime, collection_datetime,
                           cancellation_reason, completion_summary
                    FROM bookings
                    WHERE id = :booking_id
                    """
                ),
                {"booking_id": booking_row["id"]},
            )
            .mappings()
            .one()
        )
        assert repaired_row["user_id"] == booking_row["user_id"]
        assert repaired_row["string_id"] == booking_row["string_id"]
        assert repaired_row["status"] == booking_row["status"]
        assert repaired_row["expected_completion_datetime"] is None
        assert repaired_row["collection_datetime"] is None
        assert repaired_row["cancellation_reason"] is None
        assert repaired_row["completion_summary"] is None


def test_latest_migrations_adopt_auto_created_schema_drift(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "auto-created-schema-drift.sqlite"
    database_url = f"sqlite+pysqlite:///{db_path}"

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("AUTO_CREATE_SCHEMA", "false")
    get_settings.cache_clear()

    config = make_alembic_config(database_url)
    command.upgrade(config, "20260423_0018")

    from app.adapters.persistence.sqlalchemy import models  # noqa: F401
    from app.adapters.persistence.sqlalchemy.base import Base

    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    assert "payments" in inspector.get_table_names()
    assert "notification_preferences" not in {
        item["name"] for item in inspector.get_columns("profiles")
    }
    assert "racket_id" not in {
        item["name"] for item in inspector.get_columns("bookings")
    }
    assert "channel" not in {
        item["name"] for item in inspector.get_columns("booking_updates")
    }

    command.upgrade(config, "head")

    inspector = inspect(engine)
    assert "notification_preferences" in {
        item["name"] for item in inspector.get_columns("profiles")
    }
    assert "racket_id" in {item["name"] for item in inspector.get_columns("bookings")}
    assert "channel" in {
        item["name"] for item in inspector.get_columns("booking_updates")
    }

    with engine.begin() as connection:
        version = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()
    assert version == "20260726_0025"
