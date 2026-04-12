from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.adapters.persistence.sqlalchemy.models import RecommendationFeatureDefinition
from app.adapters.persistence.sqlalchemy.models import StringRecommendationMatrix
from app.adapters.persistence.sqlalchemy.recommendation_matrix_import import (
    import_recommendation_matrix_csv,
)
from app.adapters.persistence.sqlalchemy.seed import ensure_catalog_seeded
from app.adapters.persistence.sqlalchemy.session import SessionLocal
from app.config.settings import BACKEND_ROOT
from app.main import app


client = TestClient(app)


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def login_admin() -> str:
    response = client.post(
        "/api/auth/login",
        json={
            "phone_number": "+60190000000",
            "password": "admin1234",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_ensure_catalog_seeded_preserves_live_sound_feature_key() -> None:
    with SessionLocal() as db:
        db.merge(
            RecommendationFeatureDefinition(
                feature_key="sound",
                feature_label="Sound",
                feature_group="catalog_aspect",
                data_type="score",
                min_value=0,
                max_value=1,
                description="Legacy sound key.",
                is_active=True,
            )
        )
        db.add(
            StringRecommendationMatrix(
                catalog_id="yonex-bg80",
                feature_key="sound",
                source_layer="manual_rule",
                raw_value=0.91,
                normalized_score=0.91,
                confidence=0.8,
                evidence_note="legacy-row",
                source_ref="legacy://sound",
            )
        )
        db.commit()

        ensure_catalog_seeded(db)
        db.commit()

        assert db.get(RecommendationFeatureDefinition, "sound") is not None
        sound_row = db.get(
            StringRecommendationMatrix,
            ("yonex-bg80", "sound", "manual_rule"),
        )
        assert sound_row is not None
        assert float(sound_row.normalized_score or 0) == pytest.approx(0.91)


def test_admin_can_inspect_and_reimport_recommendation_matrix() -> None:
    admin_token = login_admin()

    detail_response = client.get(
        "/api/admin/strings/yonex-bg80/recommendation-matrix",
        headers=headers(admin_token),
    )
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["catalog_id"] == "yonex-bg80"
    assert detail["official_performance"]["status"] == "pending_manual_fill"
    assert "nlp_review" in detail["matrix_by_source"]
    assert detail["effective_scores"]["sound"] == pytest.approx(0.8931, abs=1e-4)

    nlp_feature_keys = {
        item["feature_key"] for item in detail["matrix_by_source"]["nlp_review"]
    }
    assert {
        "repulsion",
        "comfort",
        "control",
        "durability",
        "sound",
    }.issubset(nlp_feature_keys)
    assert {
        "value_for_money",
        "elasticity",
        "string_movement",
        "tension_retention",
        "stability",
        "all_round",
        "attacking_fit",
        "control_fit",
        "beginner_fit",
    }.isdisjoint(nlp_feature_keys)

    import_response = client.post(
        "/api/admin/recommendation-matrix/import",
        headers=headers(admin_token),
    )
    assert import_response.status_code == 200
    report = import_response.json()
    assert report["matched_strings"] == 33
    assert report["unmatched_strings"] == 0
    assert report["inserted_entries"] == 0
    assert report["updated_entries"] == 0


def test_latest_v9_workbook_import_matches_catalog() -> None:
    matrix_path = (
        BACKEND_ROOT
        / "../ml/nlp-workbench-latest/output/latest_practical_string_feature_matrix_v9_v8dict.xlsx"
    )
    assert matrix_path.exists()

    with SessionLocal() as db:
        report = import_recommendation_matrix_csv(db, matrix_path)

        assert report.total_csv_rows == 33
        assert report.matched_strings == 33
        assert report.unmatched_strings == 0
        assert report.source_layer == "nlp_review"

        aerobie_rows = {
            row.feature_key
            for row in db.query(StringRecommendationMatrix)
            .filter(
                StringRecommendationMatrix.catalog_id == "yonex-aerobite",
                StringRecommendationMatrix.source_layer == "nlp_review",
            )
            .all()
        }
        assert {
            "repulsion",
            "comfort",
            "control",
            "durability",
            "sound",
        }.issubset(aerobie_rows)
        assert {
            "value_for_money",
            "elasticity",
            "string_movement",
            "tension_retention",
            "stability",
            "all_round",
            "attacking_fit",
            "control_fit",
            "beginner_fit",
        }.isdisjoint(aerobie_rows)
