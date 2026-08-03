from __future__ import annotations

import csv
from datetime import UTC
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy import func
from sqlalchemy import select

from app.adapters.persistence.sqlalchemy.models import RecommendationFeatureDefinition
from app.adapters.persistence.sqlalchemy.models import StringRecommendationMatrix
from app.adapters.persistence.sqlalchemy.models import StringCatalogItem
from app.adapters.persistence.sqlalchemy.recommendation_matrix_import import (
    import_recommendation_matrix_csv,
)
from app.adapters.persistence.sqlalchemy.recommendation_matrix_import import (
    recommendation_matrix_source_generated_at,
)
from app.adapters.persistence.sqlalchemy.recommendation_matrix_import import (
    recommendation_matrix_source_version,
)
from app.adapters.persistence.sqlalchemy.seed import ensure_catalog_seeded
from app.adapters.persistence.sqlalchemy.session import SessionLocal
from app.config.settings import BACKEND_ROOT
from app.config.settings import get_settings
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


def test_missing_nlp_workbook_keeps_backend_healthy(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        get_settings(),
        "recommendation_matrix_source_path",
        str(tmp_path / "missing.xlsx"),
    )
    with SessionLocal() as db:
        db.execute(
            delete(StringRecommendationMatrix).where(
                StringRecommendationMatrix.source_layer == "nlp_review"
            )
        )
        db.commit()
        ensure_catalog_seeded(db)
        db.commit()

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["recommendation_artifact"]["status"] == "catalog_fallback"


def test_health_reports_stale_persisted_matrix_when_source_digest_differs(
    monkeypatch,
    tmp_path,
) -> None:
    matrix_path = tmp_path / "different-matrix.csv"
    matrix_path.write_text("configured-source", encoding="utf-8")
    with SessionLocal() as db:
        rows = db.scalars(
            select(StringRecommendationMatrix).where(
                StringRecommendationMatrix.source_layer == "nlp_review"
            )
        ).all()
        assert rows
        for row in rows:
            row.source_version = "sha256:old-persisted-version"
        db.commit()

    monkeypatch.setattr(
        get_settings(),
        "recommendation_matrix_source_path",
        str(matrix_path),
    )
    response = client.get("/health")

    assert response.status_code == 200
    artifact = response.json()["recommendation_artifact"]
    assert artifact["status"] == "stale"
    assert artifact["source_version"] == "sha256:old-persisted-version"


def test_existing_catalog_does_not_depend_on_seed_source(monkeypatch, tmp_path) -> None:
    with SessionLocal() as db:
        before = db.execute(
            select(func.count()).select_from(StringCatalogItem)
        ).scalar_one()
        assert before > 0

        monkeypatch.setattr(
            get_settings(),
            "approved_strings_source_path",
            str(tmp_path / "missing.json"),
        )
        ensure_catalog_seeded(db)

        after = db.execute(
            select(func.count()).select_from(StringCatalogItem)
        ).scalar_one()
        assert after == before


def test_invalid_startup_matrix_rolls_back_partial_import(
    monkeypatch, tmp_path
) -> None:
    matrix_path = tmp_path / "invalid-startup-matrix.csv"
    matrix_path.write_text(
        "\n".join(
            [
                (
                    "string_name,brand,attack,comfort,control,durability,"
                    "elasticity,sound,string_movement,tension_retention"
                ),
                "BG80,Yonex,0.01,0.02,0.03,0.04,0.05,0.06,0.07,0.08",
                "Unknown,Unknown,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        get_settings(),
        "recommendation_matrix_source_path",
        str(matrix_path),
    )

    with SessionLocal() as db:
        repulsion = db.get(
            StringRecommendationMatrix,
            ("yonex-bg80", "repulsion", "nlp_review"),
        )
        assert repulsion is not None
        before_score = repulsion.normalized_score
        before_version = repulsion.source_version

        ensure_catalog_seeded(db)
        db.commit()
        db.refresh(repulsion)

        assert repulsion.normalized_score == before_score
        assert repulsion.source_version == before_version


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
        "elasticity",
        "string_movement",
        "tension_retention",
    }.issubset(nlp_feature_keys)

    nlp_entry = detail["matrix_by_source"]["nlp_review"][0]
    assert nlp_entry["source_version"]
    assert nlp_entry["source_generated_at"]
    assert nlp_entry["review_count_snapshot"] is not None
    assert {
        "value_for_money",
        "stability",
        "all_round",
        "attacking_fit",
        "control_fit",
    }.issubset(nlp_feature_keys)

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
            "elasticity",
            "string_movement",
            "tension_retention",
        }.issubset(aerobie_rows)
        assert {
            "value_for_money",
            "stability",
            "all_round",
            "attacking_fit",
            "control_fit",
        }.issubset(aerobie_rows)


def test_matrix_import_refreshes_stale_source_generated_at() -> None:
    matrix_path = (
        BACKEND_ROOT
        / "../ml/nlp-workbench-latest/output/latest_practical_string_feature_matrix_v9_v8dict.xlsx"
    )
    expected_generated_at = recommendation_matrix_source_generated_at(matrix_path)
    assert expected_generated_at is not None

    with SessionLocal() as db:
        row = db.get(
            StringRecommendationMatrix,
            ("yonex-bg80", "repulsion", "nlp_review"),
        )
        assert row is not None
        row.source_generated_at = datetime(2000, 1, 1, tzinfo=UTC)
        db.commit()

        report = import_recommendation_matrix_csv(db, matrix_path)
        db.commit()
        db.refresh(row)

        assert report.updated_entries >= 1
        actual_generated_at = row.source_generated_at
        assert actual_generated_at is not None
        if actual_generated_at.tzinfo is None:
            actual_generated_at = actual_generated_at.replace(tzinfo=UTC)
        assert abs((actual_generated_at - expected_generated_at).total_seconds()) < 1e-6


def test_matrix_import_fully_replaces_stale_nlp_rows(tmp_path) -> None:
    matrix_path = tmp_path / "next-practical-matrix.csv"
    matrix_path.write_text(
        "\n".join(
            [
                (
                    "string_name,brand,attack,comfort,control,durability,"
                    "elasticity,sound,string_movement,tension_retention,"
                    "beginner_fit_score"
                ),
                "BG80,Yonex,0.8,0.6,0.7,0.5,0.8,0.9,0.4,0.6,0.7",
            ]
        ),
        encoding="utf-8",
    )

    with SessionLocal() as db:
        stale = db.get(
            StringRecommendationMatrix,
            ("yonex-bg80", "attacking_fit", "nlp_review"),
        )
        assert stale is not None

        report = import_recommendation_matrix_csv(db, matrix_path)
        db.commit()

        assert report.matched_strings == 1
        assert (
            db.get(
                StringRecommendationMatrix,
                ("yonex-bg80", "attacking_fit", "nlp_review"),
            )
            is None
        )
        repulsion = db.get(
            StringRecommendationMatrix,
            ("yonex-bg80", "repulsion", "nlp_review"),
        )
        assert repulsion is not None
        assert repulsion.source_version == recommendation_matrix_source_version(
            matrix_path
        )
        assert repulsion.source_generated_at is None


def test_matrix_import_rejects_missing_artifact(tmp_path) -> None:
    with SessionLocal() as db:
        with pytest.raises(FileNotFoundError, match="artifact is missing"):
            import_recommendation_matrix_csv(db, tmp_path / "missing.xlsx")


def test_manual_import_rejects_malformed_existing_artifact(
    monkeypatch, tmp_path
) -> None:
    matrix_path = tmp_path / "malformed-matrix.csv"
    matrix_path.write_text(
        "string_name,brand,attack,comfort,control,durability,elasticity,sound,"
        "string_movement,tension_retention\n"
        "BG80,Yonex,not-a-number,0.2,0.3,0.4,0.5,0.6,0.7,0.8\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        get_settings(),
        "recommendation_matrix_source_path",
        str(matrix_path),
    )

    response = client.post(
        "/api/admin/recommendation-matrix/import",
        headers=headers(login_admin()),
    )

    assert response.status_code == 400
    assert "invalid numeric value" in response.json()["error"]["message"]


def test_manual_import_rejects_csv_field_over_stdlib_limit(
    monkeypatch, tmp_path
) -> None:
    matrix_path = tmp_path / "oversized-field-matrix.csv"
    matrix_path.write_text("x" * 100, encoding="utf-8")
    monkeypatch.setattr(
        get_settings(),
        "recommendation_matrix_source_path",
        str(matrix_path),
    )
    original_limit = csv.field_size_limit()
    csv.field_size_limit(16)
    try:
        response = client.post(
            "/api/admin/recommendation-matrix/import",
            headers=headers(login_admin()),
        )
    finally:
        csv.field_size_limit(original_limit)

    assert response.status_code == 400
    assert "artifact" in response.json()["error"]["message"]
