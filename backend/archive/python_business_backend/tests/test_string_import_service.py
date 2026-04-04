import json
from pathlib import Path

from sqlalchemy import select

from app.db.models import String
from app.db.models import StringTag
from app.db.session import SessionLocal
from app.services.string_service import string_service


def test_import_jsonl_populates_strings_and_tags(tmp_path: Path):
    from app.services.string_import_service import import_strings_jsonl

    string_service.reset()
    dataset_path = tmp_path / "badminton_strings_recommender.jsonl"
    rows = [
        {
            "id": "bg80-src",
            "eid": 101,
            "name": "BG-80",
            "brand": "YONEX",
            "series": "BG",
            "rating": 4.6,
            "rating_5_scale": 4.6,
            "price": 39.9,
            "want_count": 120,
            "used_count": 95,
            "review_count_total": 88,
            "gauge": "0.68mm",
            "material": "High polymer nylon",
            "color": "Yellow",
            "top_tags": ["弹性好", "控球好", "声音清脆"],
            "tags": [
                {"name": "耐打", "votes": 332},
                {"name": "性价比高", "votes": 247},
            ],
            "popularity_signal": 92,
            "source_url": "https://example.com/bg80",
            "feature_text": "弹性好，控球好，声音清脆",
        },
        {
            "id": "exbolt63-src",
            "eid": 102,
            "name": "Exbolt 63",
            "brand": "YONEX",
            "series": "Exbolt",
            "rating": 4.4,
            "rating_5_scale": 4.4,
            "price": 0,
            "want_count": 80,
            "used_count": 60,
            "review_count_total": 47,
            "gauge": "竖线0.67mm、横线0.61mm",
            "material": "Forged fiber",
            "color": "White",
            "top_tags": ["弹性好", "声音清脆"],
            "tags": [{"name": "性价比高", "votes": 366}],
            "popularity_signal": 78,
            "source_url": "https://example.com/exbolt63",
            "feature_text": "弹性好，声音清脆",
        },
    ]
    dataset_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows),
        encoding="utf-8",
    )

    summary = import_strings_jsonl(dataset_path)

    with SessionLocal() as db:
        strings = (
            db.execute(
                select(String)
                .where(String.external_id.in_(["bg80-src", "exbolt63-src"]))
                .order_by(String.external_id)
            )
            .scalars()
            .all()
        )
        tags = (
            db.execute(
                select(StringTag).order_by(StringTag.votes.desc(), StringTag.tag_name)
            )
            .scalars()
            .all()
        )

    assert summary["imported_count"] == 2
    assert len(strings) == 2
    assert strings[0].gauge_raw == "0.68mm"
    assert float(strings[0].gauge_mm) == 0.68
    assert strings[0].brand_en == "YONEX"
    assert strings[0].repulsion_score is not None
    assert strings[0].control_score is not None
    assert strings[0].value_score is not None
    assert strings[1].price is None
    assert strings[1].gauge_raw == "竖线0.67mm、横线0.61mm"
    assert strings[1].gauge_mm is None
    assert any(tag.tag_name == "耐打" and tag.votes == 332 for tag in tags)
    assert any(tag.tag_name == "性价比高" and tag.votes == 366 for tag in tags)
