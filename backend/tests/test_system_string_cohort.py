from __future__ import annotations

from dataclasses import replace

from fastapi.testclient import TestClient
from sqlalchemy import func
from sqlalchemy import select

from app.adapters.persistence.sqlalchemy.catalog_seed import seed_catalog_rows
from app.adapters.persistence.sqlalchemy.models import RecommendationScoreCache
from app.adapters.persistence.sqlalchemy.models import StringCatalogItem
from app.adapters.persistence.sqlalchemy.models import StringInventoryItem
from app.adapters.persistence.sqlalchemy.models import User
from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_catalog_repository import (
    SqlAlchemyCatalogRepository,
)
from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_recommendation_repository import (
    SqlAlchemyRecommendationRepository,
)
from app.adapters.persistence.sqlalchemy.session import SessionLocal
from app.config.settings import get_settings
from app.domain.recommendation.entities import RecommendationCandidateModel
from app.domain.recommendation.entities import RecommendationRequestModel
from app.domain.recommendation.scoring import ContentRecommendationScorer
from app.main import app


APPROVED_IDS = {
    "yonex-bg80",
    "yonex-bg65",
    "yonex-bg66-ultimax",
    "yonex-bg80-power",
    "yonex-exbolt-63",
    "yonex-aerobite",
    "victor-vbs-66-nano",
    "victor-vbs-68-power",
    "li-ning-no1",
    "li-ning-n65",
    "gosen-ryzonic-65",
    "kumpoo-js-63",
}
HIDDEN_ID = "yonex-exbolt-65"
client = TestClient(app)


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _login_admin() -> str:
    response = client.post(
        "/api/auth/login",
        json={"phone_number": "+60190000000", "password": "admin1234"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _register_customer() -> str:
    response = client.post(
        "/api/auth/register",
        json={
            "username": "cohort-player",
            "phone_number": "+60121112222",
            "password": "secret123",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_catalog_inventory_and_recommendations_only_expose_the_twelve_strings() -> None:
    customer_headers = _headers(_register_customer())
    admin_headers = _headers(_login_admin())

    player_catalog = client.get("/api/strings", headers=customer_headers)
    admin_inventory = client.get(
        "/api/admin/inventory/strings",
        headers=admin_headers,
    )

    assert player_catalog.status_code == 200
    assert admin_inventory.status_code == 200
    for response in (player_catalog, admin_inventory):
        payload = response.json()
        assert payload["total"] == 12
        assert {item["id"] for item in payload["items"]} == APPROVED_IDS

    with SessionLocal() as db:
        candidates = SqlAlchemyRecommendationRepository(
            db,
            APPROVED_IDS,
        ).list_active_candidates()
        assert {candidate.item.id for candidate in candidates} == APPROVED_IDS


def test_low_stock_is_sellable_but_out_of_stock_is_excluded() -> None:
    with SessionLocal() as db:
        inventory = db.execute(
            select(StringInventoryItem).where(
                StringInventoryItem.catalog_id == "yonex-bg80"
            )
        ).scalar_one()
        inventory.available_stock = 3
        inventory.availability_status = "low_stock"
        user_id = db.execute(select(User.id)).scalars().first()
        assert user_id is not None
        db.add(
            RecommendationScoreCache(
                user_id=user_id,
                catalog_id="yonex-bg80",
                algorithm_version="inventory-filter-test",
                final_score=0.9,
                rank_position=1,
                rationale={},
            )
        )
        db.flush()

        repository = SqlAlchemyRecommendationRepository(db, APPROVED_IDS)

        assert "yonex-bg80" in {
            candidate.item.id for candidate in repository.list_active_candidates()
        }
        assert (
            len(
                repository.get_cached_results(
                    user_id=user_id,
                    algorithm_version="inventory-filter-test",
                )
            )
            == 1
        )
        inventory.available_stock = 0
        inventory.availability_status = "out_of_stock"
        db.flush()

        assert "yonex-bg80" not in {
            candidate.item.id for candidate in repository.list_active_candidates()
        }
        assert (
            repository.get_cached_results(
                user_id=user_id,
                algorithm_version="inventory-filter-test",
            )
            == []
        )


def test_inactive_inventory_is_excluded_from_catalog_lookup() -> None:
    with SessionLocal() as db:
        inventory = db.execute(
            select(StringInventoryItem).where(
                StringInventoryItem.catalog_id == "yonex-bg80"
            )
        ).scalar_one()
        inventory.is_active = False
        inventory.available_stock = 8
        inventory.availability_status = "in_stock"
        db.flush()

        repository = SqlAlchemyCatalogRepository(db, APPROVED_IDS)

        assert repository.get_by_id("yonex-bg80") is None
        assert repository.get_by_id("yonex-bg80", include_inactive=True) is not None


def test_seed_contains_only_approved_strings() -> None:
    customer_headers = _headers(_register_customer())
    admin_headers = _headers(_login_admin())

    player_catalog = client.get("/api/strings", headers=customer_headers)
    assert player_catalog.status_code == 200
    assert HIDDEN_ID not in {item["id"] for item in player_catalog.json()["items"]}
    assert (
        client.get(
            f"/api/admin/inventory/strings/{HIDDEN_ID}",
            headers=admin_headers,
        ).status_code
        == 404
    )
    with SessionLocal() as db:
        assert db.get(StringCatalogItem, HIDDEN_ID) is None
        assert db.scalar(select(func.count()).select_from(StringCatalogItem)) == 12


def test_backend_and_nlp_read_the_same_versioned_cohort() -> None:
    cohort_path = get_settings().approved_string_cohort_path
    assert cohort_path.name == "approved_string_cohort_v1.csv"
    assert cohort_path.is_file()


def test_all_approved_strings_have_seeded_official_performance() -> None:
    settings = get_settings()
    rows = seed_catalog_rows(settings.approved_strings_path)["items"]
    approved_rows = {
        row["catalog"]["catalog_id"]: row
        for row in rows
        if row["catalog"]["catalog_id"] in APPROVED_IDS
    }

    assert set(approved_rows) == APPROVED_IDS
    assert all(
        row["catalog"]["official_performance_status"] == "manual_reviewed"
        and row["official_performance"]["status"] == "manual_reviewed"
        and all(
            row["official_performance"][field] is not None
            for field in (
                "feel",
                "repulsion_power",
                "durability",
                "hitting_sound",
                "shock_absorption",
                "control",
            )
        )
        for row in approved_rows.values()
    )

    feel_values = {
        catalog_id: row["official_performance"]["feel"]
        for catalog_id, row in approved_rows.items()
    }
    assert {"soft": 3, "medium": 7, "hard": 2} == {
        "soft": sum(value <= 4 for value in feel_values.values()),
        "medium": sum(4 < value <= 6.5 for value in feel_values.values()),
        "hard": sum(value > 6.5 for value in feel_values.values()),
    }


def test_feel_and_gauge_preferences_raise_matching_candidate_scores() -> None:
    with SessionLocal() as db:
        candidates = SqlAlchemyRecommendationRepository(
            db,
            APPROVED_IDS,
        ).list_active_candidates()
    by_id = {candidate.item.id: candidate for candidate in candidates}
    base_request = RecommendationRequestModel(
        user_id=None,
        skill_level="intermediate",
        playing_style="balanced",
        preferred_tension=25,
        frequency_per_week=2,
        preferred_feel="medium",
        preferred_gauge="no_preference",
        recent_goal="balanced",
        pref_attack=5,
        pref_comfort=5,
        pref_control=5,
        pref_durability=5,
        pref_elasticity=5,
        pref_sound=5,
        pref_string_movement=5,
        pref_tension_retention=5,
        pref_value_for_money=5,
        top_n=12,
    )

    for field, values in (
        ("preferred_feel", ("soft", "medium", "hard")),
        ("preferred_gauge", ("thin", "medium", "thick")),
    ):
        for value in values:
            preferred_request = (
                replace(base_request, preferred_feel=value)
                if field == "preferred_feel"
                else replace(base_request, preferred_gauge=value)
            )
            comparison_value = (
                next(candidate for candidate in values if candidate != value)
                if field == "preferred_feel"
                else "no_preference"
            )
            comparison_request = (
                replace(base_request, preferred_feel=comparison_value)
                if field == "preferred_feel"
                else base_request
            )
            preferred_results = ContentRecommendationScorer().score_candidates(
                candidates=candidates,
                request=preferred_request,
                top_n=len(candidates),
            )
            comparison_results = ContentRecommendationScorer().score_candidates(
                candidates=candidates,
                request=comparison_request,
                top_n=len(candidates),
            )
            preferred_scores = {
                row.result.catalog_id: row.result.score for row in preferred_results
            }
            comparison_scores = {
                row.result.catalog_id: row.result.score for row in comparison_results
            }
            matching_ids = {
                catalog_id
                for catalog_id, candidate in by_id.items()
                if _candidate_category(candidate, field) == value
            }

            assert matching_ids
            assert all(
                preferred_scores[catalog_id] > comparison_scores[catalog_id]
                for catalog_id in matching_ids
            )


def _candidate_category(candidate: RecommendationCandidateModel, field: str) -> str:
    item = candidate.item
    if field == "preferred_feel":
        official_performance = item.official_performance
        assert official_performance is not None
        feel = official_performance.feel
        assert feel is not None
        return "soft" if feel <= 4 else "medium" if feel <= 6.5 else "hard"
    gauge = item.gauge_main_mm
    assert gauge is not None
    return "thin" if gauge <= 0.64 else "medium" if gauge <= 0.67 else "thick"
