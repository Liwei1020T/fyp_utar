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
        string_row = connection.execute(
            text(
                """
                SELECT catalog_id, display_name, official_performance_status
                FROM strings
                WHERE catalog_id = 'yonex-bg80'
                """
            )
        ).mappings().one()
        assert string_row["display_name"] == "Yonex BG80"
        assert string_row["official_performance_status"] == "pending_manual_fill"

        booking_row = connection.execute(
            text("SELECT string_id FROM bookings WHERE id = 'booking-1'")
        ).mappings().one()
        assert booking_row["string_id"] == "yonex-bg80"

        inventory_row = connection.execute(
            text(
                """
                SELECT available_stock, selling_price
                FROM inventory_items
                WHERE catalog_id = 'yonex-bg80'
                """
            )
        ).mappings().one()
        assert inventory_row["available_stock"] == 6
        assert float(inventory_row["selling_price"]) == 45.0

        matrix_rows = connection.execute(
            text(
                """
                SELECT COUNT(*) AS count
                FROM string_recommendation_matrix
                WHERE catalog_id = 'yonex-bg80'
                """
            )
        ).mappings().one()
        assert matrix_rows["count"] >= 12
