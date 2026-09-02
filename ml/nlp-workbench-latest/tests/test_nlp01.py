from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd
import pytest


WORKBENCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKBENCH / "src"))

from stringsense_nlp.annotation import ALLOWED_LABELS  # noqa: E402
from stringsense_nlp.annotation import annotation_template  # noqa: E402
from stringsense_nlp.annotation import build_gold_dataset  # noqa: E402
from stringsense_nlp.annotation import build_silver_assisted_draft  # noqa: E402
from stringsense_nlp.annotation import merge_annotations  # noqa: E402
from stringsense_nlp.annotation import stratified_sample  # noqa: E402
from stringsense_nlp.annotation import validate_annotation_frame  # noqa: E402
from stringsense_nlp.foundation import ASPECTS  # noqa: E402
from stringsense_nlp.foundation import build_clean_reviews  # noqa: E402
from stringsense_nlp.foundation import conservative_normalize  # noqa: E402
from stringsense_nlp.foundation import language_category  # noqa: E402
from stringsense_nlp.foundation import load_string_mappings  # noqa: E402
from stringsense_nlp.foundation import normalize_string_name  # noqa: E402
from stringsense_nlp.labeling import build_aspect_lexicon  # noqa: E402
from stringsense_nlp.labeling import build_normalizer  # noqa: E402
from stringsense_nlp.labeling import classify_review_aspect  # noqa: E402
from stringsense_nlp.labeling import split_into_clauses  # noqa: E402
from stringsense_nlp.review_html import build_review_payload  # noqa: E402
from stringsense_nlp.review_html import render_annotation_review_html  # noqa: E402


def _mapping_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "raw_name": "BG-80",
                "normalized_name": "bg80",
                "canonical_name": "Yonex BG80",
                "mapping_method": "exact",
                "confidence": 1.0,
                "review_status": "confirmed",
                "notes": "",
            },
            {
                "raw_name": "YONEX BG80",
                "normalized_name": "yonexbg80",
                "canonical_name": "Yonex BG80",
                "mapping_method": "brand_alias",
                "confidence": 1.0,
                "review_status": "confirmed",
                "notes": "",
            },
            {
                "raw_name": "80P",
                "normalized_name": "80p",
                "canonical_name": "Yonex BG80 POWER",
                "mapping_method": "short_alias",
                "confidence": 0.7,
                "review_status": "pending",
                "notes": "human review",
            },
        ]
    )


def test_conservative_cleaning_is_traceable_and_preserves_contrast() -> None:
    cleaned, transformations = conservative_normalize(
        "\ufeffＢＧ８０&nbsp;<b>很弹</b>，但是不耐打 https://example.com/a"
    )

    assert cleaned == "BG80 很弹,但是不耐打 <URL>"
    assert set(transformations) == {
        "unicode_nfkc",
        "html_unescape",
        "html_tags_removed",
        "url_replaced",
        "hidden_control_removed",
        "whitespace_collapsed",
    }
    assert language_category(cleaned) == "mixed_zh_en"


def test_nested_negative_phrase_wins_for_durability() -> None:
    result = classify_review_aspect(
        ["这个球线不耐用"],
        {
            "aspect_terms": {"耐用"},
            "positive_terms": {"耐用"},
            "negative_terms": {"不耐用"},
        },
    )

    assert result["label_text"] == "negative"


def test_nested_positive_phrase_wins_for_string_movement() -> None:
    result = classify_review_aspect(
        ["这个球线不跑线"],
        {
            "aspect_terms": {"跑线"},
            "positive_terms": {"不跑线"},
            "negative_terms": {"跑线"},
        },
    )

    assert result["label_text"] == "positive"


@pytest.mark.parametrize(
    ("text", "aspect", "expected_label"),
    (
        ("耐用", "durability", "positive"),
        ("不耐用", "durability", "negative"),
        ("耐打", "durability", "positive"),
        ("不耐打", "durability", "negative"),
        ("跑线", "string_movement", "negative"),
        ("不跑线", "string_movement", "positive"),
        ("移位", "string_movement", "mentioned"),
        ("不移位", "string_movement", "positive"),
        ("震手", "comfort", "negative"),
        ("不震手", "comfort", "positive"),
        ("弹性好", "elasticity", "positive"),
        ("不太弹", "elasticity", "negative"),
        ("容易断", "durability", "negative"),
        ("不容易断", "durability", "positive"),
        ("掉磅快", "tension_retention", "negative"),
        ("不容易掉磅", "tension_retention", "positive"),
    ),
)
def test_silver_matching_regression_cases(
    text: str,
    aspect: str,
    expected_label: str,
) -> None:
    dictionary = pd.read_csv(WORKBENCH / "data/domain_dictionary_optimized_v8.csv")
    rules = pd.read_csv(WORKBENCH / "data/normalization_rules_v8.csv")
    normalize = build_normalizer(rules)
    lexicon = build_aspect_lexicon(dictionary)

    normalized = normalize(text)
    result = classify_review_aspect(
        split_into_clauses(normalized),
        lexicon[aspect],
    )

    assert result["label_text"] == expected_label


@pytest.mark.parametrize("value", ("BG80", "BG-80", "BG 80", "ｂｇ８０"))
def test_string_name_normalizer_handles_case_space_symbol_and_width(value: str) -> None:
    assert normalize_string_name(value) == "bg80"


def test_mapping_config_supports_brand_alias_and_keeps_low_confidence_pending(
    tmp_path: Path,
) -> None:
    path = tmp_path / "mapping.csv"
    _mapping_frame().to_csv(path, index=False)

    mappings = load_string_mappings(path)

    assert (
        mappings.loc[mappings["raw_name"] == "YONEX BG80", "review_status"].item()
        == "confirmed"
    )
    assert (
        mappings.loc[mappings["raw_name"] == "80P", "review_status"].item() == "pending"
    )


def test_cleaning_keeps_duplicates_and_assigns_one_split_group() -> None:
    raw = {
        "strings": [
            {
                "name": "BG-80",
                "brand": "Yonex",
                "eid": 1,
                "reviews": [
                    {"review_id": "1", "content": "很弹，但是不耐打"},
                    {"review_id": "2", "content": "很弹，但是不耐打"},
                ],
            }
        ]
    }

    clean, invalid, duplicates, groups, summary = build_clean_reviews(
        raw, _mapping_frame()
    )

    assert invalid.empty
    assert len(clean) == 2
    assert len(duplicates) == 2
    assert len(groups) == 1
    assert clean["split_group_id"].nunique() == 1
    assert clean["split"].nunique() == 1
    assert set(clean["cleaning_status"]) == {"included_duplicate"}
    assert summary["exact_normalized_text_duplicates"]["extra_records"] == 1


def _sampling_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    languages = {2: "mixed_zh_en", 6: "mixed_zh_en", 9: "en_only"}
    reviews = pd.DataFrame(
        [
            {
                "review_id": f"R{index}",
                "cleaning_status": "included",
                "canonical_string_name": "Yonex BG80"
                if index <= 4
                else "Victor VBS-68",
                "language": languages.get(index, "zh_only"),
                "is_comparison": index == 3,
                "is_code_mixed": index in {2, 6},
                "raw_string_name": "BG-80" if index <= 4 else "VBS-68",
                "raw_text": f"review {index}",
                "normalized_text": f"review {index}",
            }
            for index in range(1, 10)
        ]
    )
    silver = pd.DataFrame(
        [
            {
                "review_id": f"R{index}",
                "aspect": aspect,
                "label_text": "positive" if index % 2 else "not_mentioned",
            }
            for index in range(1, 10)
            for aspect in ASPECTS
        ]
    )
    return reviews, silver


def test_sampling_and_blind_templates_are_deterministic() -> None:
    reviews, silver = _sampling_frames()

    first = stratified_sample(
        reviews, silver, sample_size=7, seed=42, per_string_floor=2
    )
    second = stratified_sample(
        reviews, silver, sample_size=7, seed=42, per_string_floor=2
    )
    template = annotation_template(first, ASPECTS, "A")

    assert first["review_id"].tolist() == second["review_id"].tolist()
    assert set(first["language"]) == {"zh_only", "mixed_zh_en", "en_only"}
    assert not any("silver" in column for column in template.columns)
    assert all(template[f"{aspect}_label"].eq("").all() for aspect in ASPECTS)


def test_silver_draft_is_complete_but_cannot_be_merged_as_human_gold() -> None:
    reviews, silver = _sampling_frames()
    silver["needs_manual_review"] = silver["label_text"].eq("mentioned").astype(int)
    sample = stratified_sample(
        reviews, silver, sample_size=2, seed=7, per_string_floor=1
    )
    human = annotation_template(sample, ASPECTS, "A")
    draft, evidence = build_silver_assisted_draft(human, silver, ASPECTS)

    validation = validate_annotation_frame(draft, ASPECTS, require_complete=True)
    assert validation["complete"]
    assert not validation["human_annotation_eligible"]
    assert len(evidence) == 2 * len(ASPECTS)
    with pytest.raises(ValueError, match="cannot be merged as human Gold"):
        merge_annotations(draft, draft, ASPECTS)


def _completed_template(annotator_id: str) -> pd.DataFrame:
    reviews, silver = _sampling_frames()
    sample = stratified_sample(
        reviews, silver, sample_size=2, seed=7, per_string_floor=1
    )
    frame = annotation_template(sample, ASPECTS, annotator_id)
    for aspect in ASPECTS:
        frame[f"{aspect}_label"] = ["positive", "negative"]
    if annotator_id == "B":
        frame.loc[0, "sound_label"] = "mixed"
    return frame


def test_annotation_validation_merge_agreement_and_gold_gate() -> None:
    annotator_a = _completed_template("A")
    annotator_b = _completed_template("B")

    assert validate_annotation_frame(annotator_a, ASPECTS, require_complete=True)[
        "complete"
    ]
    merged, disagreements, agreement, adjudication = merge_annotations(
        annotator_a, annotator_b, ASPECTS
    )

    assert len(merged) == 2 * len(ASPECTS)
    assert len(disagreements) == 1
    assert agreement["overall"]["agreement"] < 1
    with pytest.raises(ValueError, match="resolved_label"):
        build_gold_dataset(adjudication)
    adjudication.loc[adjudication["resolved_label"] == "", "resolved_label"] = (
        "positive"
    )
    gold = build_gold_dataset(adjudication)
    assert set(gold["gold_label"]).issubset(ALLOWED_LABELS)


def test_workbench_mapping_covers_every_raw_parent_string() -> None:
    with (WORKBENCH / "data/archive_latest/badminton_strings_data.json").open(
        encoding="utf-8"
    ) as handle:
        raw = json.load(handle)
    mappings = load_string_mappings(WORKBENCH / "config/string_name_aliases.csv")
    confirmed = set(
        mappings.loc[mappings["review_status"] == "confirmed", "normalized_name"]
    )

    assert {normalize_string_name(item["name"]) for item in raw["strings"]}.issubset(
        confirmed
    )


def test_nlp01_notebook_has_stable_unique_cell_ids() -> None:
    with (WORKBENCH / "stringsense_nlp01_foundation_notebook.ipynb").open(
        encoding="utf-8"
    ) as handle:
        notebook = json.load(handle)
    cell_ids = [cell.get("id") for cell in notebook["cells"]]

    assert all(cell_ids)
    assert len(cell_ids) == len(set(cell_ids))


def test_annotation_review_html_is_offline_and_escapes_embedded_script() -> None:
    reviews, silver = _sampling_frames()
    silver["needs_manual_review"] = 0
    sample = stratified_sample(
        reviews, silver, sample_size=2, seed=7, per_string_floor=1
    )
    template = annotation_template(sample, ASPECTS, "A")
    draft, evidence = build_silver_assisted_draft(template, silver, ASPECTS)
    draft.loc[0, "raw_text"] = "safe </script><script>alert(1)</script>"
    payload = build_review_payload(
        draft, evidence, ASPECTS, "html-test", "draft-hash", "evidence-hash"
    )

    html = render_annotation_review_html(payload)

    assert "https://" not in html
    assert r"<\/script><script>alert(1)<\/script>" in html
    assert "automatic_silver_conversion_not_human" in html
    assert "annotation_review.html" not in html
