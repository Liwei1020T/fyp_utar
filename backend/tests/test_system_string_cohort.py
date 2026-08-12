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
from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_recommendation_repository import (
    SqlAlchemyRecommendationRepository,
)
from app.adapters.persistence.sqlalchemy.session import SessionLocal
from app.config.settings import get_settings
from app.domain.recommendation.entities import RecommendationCandidateModel
from app.domain.recommendation.entities import RecommendationRequestModel
from app.domain.recommendation.scoring import Fyp1ContentRecommendationScorer
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
    admin_catalog = client.get("/api/admin/strings", headers=admin_headers)
    admin_inventory = client.get(
        "/api/admin/inventory/strings",
        headers=admin_headers,
    )

    assert player_catalog.status_code == 200
    assert admin_catalog.status_code == 200
    assert admin_inventory.status_code == 200
    for response in (player_catalog, admin_catalog, admin_inventory):
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


def test_other_strings_are_hidden_but_preserved_for_history() -> None:
    customer_headers = _headers(_register_customer())
    admin_headers = _headers(_login_admin())

    assert (
        client.get(f"/api/strings/{HIDDEN_ID}", headers=customer_headers).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/admin/inventory/strings/{HIDDEN_ID}",
            headers=admin_headers,
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/admin/inventory/strings/{HIDDEN_ID}/movements",
            headers=admin_headers,
        ).status_code
        == 404
    )
    create_hidden = client.post(
        "/api/admin/strings",
        headers=admin_headers,
        json={"brand": "Yonex", "model_name": "EXBOLT 65"},
    )
    assert create_hidden.status_code == 400

    with SessionLocal() as db:
        assert db.get(StringCatalogItem, HIDDEN_ID) is not None
        assert db.scalar(select(func.count()).select_from(StringCatalogItem)) == 33


def test_backend_and_nlp_read_the_same_versioned_cohort() -> None:
    cohort_path = get_settings().approved_string_cohort_path
    assert cohort_path.name == "approved_string_cohort_v1.csv"
    assert cohort_path.is_file()


def test_all_approved_strings_have_a_seeded_feel_category() -> None:
    settings = get_settings()
    rows = seed_catalog_rows(settings.approved_strings_path)["items"]
    feel_values = {
        row["catalog"]["catalog_id"]: row["official_performance"]["feel"]
        for row in rows
        if row["catalog"]["catalog_id"] in APPROVED_IDS
    }

    assert set(feel_values) == APPROVED_IDS
    assert {"soft": 3, "medium": 7, "hard": 2} == {
        "soft": sum(value <= 4 for value in feel_values.values()),
        "medium": sum(4 < value <= 6.5 for value in feel_values.values()),
        "hard": sum(value > 6.5 for value in feel_values.values()),
    }


def test_feel_and_gauge_preferences_surface_a_match_near_the_top() -> None:
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
            request = (
                replace(base_request, preferred_feel=value)
                if field == "preferred_feel"
                else replace(base_request, preferred_gauge=value)
            )
            results = Fyp1ContentRecommendationScorer().score_candidates(
                candidates=candidates,
                request=request,
                top_n=5,
            )
            top_categories = set()
            for row in results:
                catalog_id = row.result.catalog_id
                assert catalog_id is not None
                top_categories.add(_candidate_category(by_id[catalog_id], field))
            assert value in top_categories


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
