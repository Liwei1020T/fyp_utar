from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd
import pytest


WORKBENCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKBENCH / "src"))

from stringsense_nlp.boundary import assert_zero_leakage  # noqa: E402
from stringsense_nlp.boundary import create_stage_directory  # noqa: E402
from stringsense_nlp.boundary import deterministic_split  # noqa: E402
from stringsense_nlp.boundary import fingerprint_protected_assets  # noqa: E402
from stringsense_nlp.boundary import leakage_report  # noqa: E402
from stringsense_nlp.boundary import review_text_group_id  # noqa: E402
from stringsense_nlp.boundary import validate_run_id  # noqa: E402
from stringsense_nlp.labeling import build_normalizer  # noqa: E402
from stringsense_nlp.pipeline import build_review_frame  # noqa: E402


NOTEBOOKS = (
    "stringsense_absa_labeling_notebook_latest.ipynb",
    "stringsense_complete_absa_pipeline_notebook_latest.ipynb",
)


def test_identical_review_text_and_all_aspects_inherit_one_split() -> None:
    text = "same normalized review"
    group_id = review_text_group_id(text)
    split = deterministic_split(group_id)
    frame = pd.DataFrame(
        [
            {
                "sample_id": f"R{review}_{aspect}",
                "split": split,
                "split_group_id": group_id,
                "review_id": f"R{review}",
                "review_text": text,
            }
            for review in (1, 2)
            for aspect in ("attack", "control")
        ]
    )

    report = leakage_report(frame)

    assert_zero_leakage(report)
    assert report["review_cross_partition_count"] == 0
    assert report["text_cross_partition_count"] == 0


def test_leakage_gate_rejects_one_review_in_two_partitions() -> None:
    frame = pd.DataFrame(
        [
            {
                "sample_id": "R1_attack",
                "split": "train",
                "split_group_id": "group-a",
                "review_id": "R1",
                "review_text": "same review",
            },
            {
                "sample_id": "R1_control",
                "split": "test",
                "split_group_id": "group-a",
                "review_id": "R1",
                "review_text": "same review",
            },
        ]
    )

    with pytest.raises(RuntimeError, match="leakage validation failed"):
        assert_zero_leakage(leakage_report(frame))


def test_stage_directory_is_create_once(tmp_path: Path) -> None:
    first = create_stage_directory(tmp_path, "run-001", "labeling")

    assert first.is_dir()
    with pytest.raises(FileExistsError):
        create_stage_directory(tmp_path, "run-001", "labeling")


def test_protected_asset_snapshot_does_not_open_source_archive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data_dir = tmp_path / "data"
    output_dir = tmp_path / "output"
    data_dir.mkdir()
    output_dir.mkdir()
    archive_path = data_dir / "archive_latest.zip"
    archive_path.write_bytes(b"do-not-open")
    (data_dir / "example_latest.csv").write_text("value\n1\n", encoding="utf-8")
    (output_dir / "latest_practical_string_feature_matrix_v9_v8dict.xlsx").write_bytes(
        b"canonical"
    )
    original_open = Path.open

    def guarded_open(path: Path, *args: object, **kwargs: object):
        if path == archive_path:
            raise AssertionError("The protected source archive must never be opened")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)

    snapshot = fingerprint_protected_assets(tmp_path)

    assert snapshot["source_archive"]["verification"].startswith("metadata-only")
    assert "sha256" not in snapshot["source_archive"]
    assert "data/example_latest.csv" in snapshot
    assert "output/latest_practical_string_feature_matrix_v9_v8dict.xlsx" in snapshot


def test_review_frame_reads_raw_price_and_treats_zero_as_missing() -> None:
    raw_data = {
        "strings": [
            {
                "name": "Known price",
                "brand": "Demo",
                "price": 68,
                "reviews": [{"review_id": "1", "content": "good"}],
            },
            {
                "name": "Unknown price",
                "brand": "Demo",
                "price": 0,
                "reviews": [{"review_id": "2", "content": "fine"}],
            },
        ]
    }
    normalize_text = build_normalizer(pd.DataFrame(columns=["pattern", "replacement"]))

    frame = build_review_frame(raw_data, normalize_text)

    assert frame.loc[frame["string_name"] == "Known price", "price_rm"].iloc[0] == 68
    assert pd.isna(
        frame.loc[frame["string_name"] == "Unknown price", "price_rm"].iloc[0]
    )


@pytest.mark.parametrize("notebook_name", NOTEBOOKS)
def test_notebook_cells_have_stable_unique_ids(notebook_name: str) -> None:
    with (WORKBENCH / notebook_name).open("r", encoding="utf-8") as handle:
        notebook = json.load(handle)

    cell_ids = [cell.get("id") for cell in notebook["cells"]]

    assert all(cell_ids)
    assert len(cell_ids) == len(set(cell_ids))


@pytest.mark.parametrize("run_id", ("..", "bad/id", "has spaces"))
def test_run_id_rejects_unsafe_paths(run_id: str) -> None:
    with pytest.raises(ValueError):
        validate_run_id(run_id)
