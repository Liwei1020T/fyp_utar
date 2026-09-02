from __future__ import annotations

import csv

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy import func
from sqlalchemy import select

from app.adapters.persistence.sqlalchemy.models import RecommendationFeatureDefinition
from app.adapters.persistence.sqlalchemy.models import RecommendationScoreCache
from app.adapters.persistence.sqlalchemy.models import StringRecommendationMatrix
from app.adapters.persistence.sqlalchemy.models import StringCatalogItem
from app.adapters.persistence.sqlalchemy.models import User
from app.adapters.persistence.sqlalchemy.recommendation_matrix_import import (
    import_recommendation_matrix_csv,
)
from app.adapters.persistence.sqlalchemy.catalog_seed import approved_catalog_ids
from app.adapters.persistence.sqlalchemy.seed import ensure_catalog_seeded
from app.adapters.persistence.sqlalchemy.session import SessionLocal
from app.config.settings import BACKEND_ROOT
from app.config.settings import get_settings
from app.domain.catalog.errors import RecommendationMatrixArtifactError
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
                evidence_note="legacy-row",
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


def test_health_reports_imported_matrix_row_count_without_metadata() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    artifact = response.json()["recommendation_artifact"]
    assert artifact == {"status": "imported", "rows": 108}


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

        ensure_catalog_seeded(db)
        db.commit()
        db.refresh(repulsion)

        assert repulsion.normalized_score == before_score


def test_admin_can_inspect_and_reimport_recommendation_matrix() -> None:
    admin_token = login_admin()

    detail_response = client.get(
        "/api/admin/strings/yonex-bg80/recommendation-matrix",
        headers=headers(admin_token),
    )
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["catalog_id"] == "yonex-bg80"
    assert detail["official_performance"]["status"] == "manual_reviewed"
    assert "nlp_review" in detail["matrix_by_source"]
    assert detail["effective_scores"]["sound"] == pytest.approx(0.9562, abs=1e-4)

    nlp_feature_keys = {
        item["feature_key"] for item in detail["matrix_by_source"]["nlp_review"]
    }
    assert nlp_feature_keys == {
        "repulsion",
        "comfort",
        "control",
        "durability",
        "sound",
        "elasticity",
        "string_movement",
        "tension_retention",
        "value_for_money",
    }

    nlp_entry = detail["matrix_by_source"]["nlp_review"][0]
    assert not {
        "confidence",
        "source_ref",
        "source_version",
        "source_generated_at",
        "review_count_snapshot",
    }.intersection(nlp_entry)

    import_response = client.post(
        "/api/admin/recommendation-matrix/import",
        headers=headers(admin_token),
    )
    assert import_response.status_code == 200
    report = import_response.json()
    assert report["matched_strings"] == 12
    assert report["unmatched_strings"] == 0
    assert report["inserted_entries"] == 0
    assert report["updated_entries"] == 0


def test_latest_macbert_workbook_import_matches_approved_cohort() -> None:
    matrix_path = (
        BACKEND_ROOT
        / "../ml/nlp-workbench-latest/output/latest_macbert_review_matrix_system12.xlsx"
    )
    if not matrix_path.exists():
        pytest.skip("protected local MacBERT matrix is not available")

    with SessionLocal() as db:
        report = import_recommendation_matrix_csv(db, matrix_path)

        assert report.total_csv_rows == 12
        assert report.matched_strings == 12
        assert report.unmatched_strings == 0
        assert report.source_layer == "nlp_review"

        imported_catalog_ids = set(
            db.scalars(
                select(StringRecommendationMatrix.catalog_id)
                .where(StringRecommendationMatrix.source_layer == "nlp_review")
                .distinct()
            )
        )
        assert imported_catalog_ids == set(
            approved_catalog_ids(get_settings().approved_string_cohort_path)
        )

        bg80_sound = db.get(
            StringRecommendationMatrix,
            ("yonex-bg80", "sound", "nlp_review"),
        )
        assert bg80_sound is not None
        assert float(bg80_sound.raw_value or 0) == pytest.approx(4.8247, abs=1e-4)
        assert float(bg80_sound.normalized_score or 0) == pytest.approx(
            0.9562, abs=1e-4
        )

        aerobie_rows = {
            row.feature_key
            for row in db.query(StringRecommendationMatrix)
            .filter(
                StringRecommendationMatrix.catalog_id == "yonex-aerobite",
                StringRecommendationMatrix.source_layer == "nlp_review",
            )
            .all()
        }
        assert aerobie_rows == {
            "repulsion",
            "comfort",
            "control",
            "durability",
            "sound",
            "elasticity",
            "string_movement",
            "tension_retention",
            "value_for_money",
        }


def test_changed_matrix_import_invalidates_cache() -> None:
    matrix_path = (
        BACKEND_ROOT
        / "../ml/nlp-workbench-latest/output/latest_macbert_review_matrix_system12.xlsx"
    )
    with SessionLocal() as db:
        row = db.get(
            StringRecommendationMatrix,
            ("yonex-bg80", "repulsion", "nlp_review"),
        )
        assert row is not None
        row.normalized_score = 0
        user_id = db.execute(select(User.id)).scalars().first()
        assert user_id is not None
        db.add(
            RecommendationScoreCache(
                user_id=user_id,
                catalog_id="yonex-bg80",
                algorithm_version="stale-matrix-test",
                final_score=0.9,
                rank_position=1,
                rationale={},
            )
        )
        db.commit()

        report = import_recommendation_matrix_csv(db, matrix_path)
        db.commit()
        db.refresh(row)

        assert report.updated_entries >= 1
        assert float(row.normalized_score or 0) > 0
        assert (
            db.scalar(select(func.count()).select_from(RecommendationScoreCache)) == 0
        )


def test_unchanged_matrix_import_preserves_cache() -> None:
    matrix_path = (
        BACKEND_ROOT
        / "../ml/nlp-workbench-latest/output/latest_macbert_review_matrix_system12.xlsx"
    )

    with SessionLocal() as db:
        user_id = db.execute(select(User.id)).scalars().first()
        assert user_id is not None
        db.add(
            RecommendationScoreCache(
                user_id=user_id,
                catalog_id="yonex-bg80",
                algorithm_version="current-matrix-test",
                final_score=0.9,
                rank_position=1,
                rationale={},
            )
        )
        db.commit()

        report = import_recommendation_matrix_csv(db, matrix_path)
        db.commit()

        assert report.inserted_entries == 0
        assert report.updated_entries == 0
        assert (
            db.scalar(select(func.count()).select_from(RecommendationScoreCache)) == 1
        )


def test_matrix_import_fully_replaces_stale_nlp_rows(tmp_path) -> None:
    matrix_path = tmp_path / "next-practical-matrix.csv"
    matrix_path.write_text(
        "\n".join(
            [
                (
                    "string_name,brand,attack,comfort,control,durability,"
                    "elasticity,sound,string_movement,tension_retention,"
                    "value_for_money"
                ),
                "BG80,Yonex,0.8,0.6,0.7,0.5,0.8,0.9,0.4,0.6,0.7",
            ]
        ),
        encoding="utf-8",
    )

    with SessionLocal() as db:
        db.add(
            StringRecommendationMatrix(
                catalog_id="yonex-bg80",
                feature_key="attacking_fit",
                source_layer="nlp_review",
                normalized_score=0.5,
            )
        )
        db.flush()
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
        assert float(repulsion.normalized_score or 0) == pytest.approx(0.8)


def test_macbert_matrix_rejects_catalog_id_outside_catalog(tmp_path) -> None:
    matrix_path = tmp_path / "unknown-macbert-matrix.csv"
    matrix_path.write_text(
        "catalog_id,canonical_string_name,attack,comfort,control,durability,"
        "elasticity,sound,string_movement,tension_retention,value_for_money\n"
        "unknown-string,Unknown String,5,5,5,5,5,5,5,5,5\n",
        encoding="utf-8",
    )

    with SessionLocal() as db:
        with pytest.raises(
            RecommendationMatrixArtifactError,
            match="1 unmatched catalog rows",
        ):
            import_recommendation_matrix_csv(db, matrix_path)


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
