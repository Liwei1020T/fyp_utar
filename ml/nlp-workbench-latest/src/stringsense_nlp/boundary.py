from __future__ import annotations

from datetime import UTC, datetime
import hashlib
from importlib import metadata
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping


RUN_SCHEMA_VERSION = "stringsense.nlp-experiment.v1"
RUN_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{2,79}$")
READ_ONLY_INPUTS = {
    "raw_reviews": Path("data/archive_latest/badminton_strings_data.json"),
    "domain_dictionary": Path("data/domain_dictionary_optimized_v8.csv"),
    "normalization_rules": Path("data/normalization_rules_v8.csv"),
}
SOURCE_ARCHIVE = Path("data/archive_latest.zip")
CANONICAL_BACKEND_ARTIFACT = Path(
    "output/latest_practical_string_feature_matrix_v9_v8dict.xlsx"
)


def resolve_workbench(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    candidates = (current, current / "ml" / "nlp-workbench-latest")
    marker = READ_ONLY_INPUTS["raw_reviews"]
    for candidate in candidates:
        if (candidate / marker).is_file():
            return candidate
    raise FileNotFoundError(
        "Cannot locate ml/nlp-workbench-latest from the current directory"
    )


def validate_run_id(run_id: str) -> str:
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError(
            "run_id must be 3-80 characters using letters, numbers, '.', '_' or '-'"
        )
    return run_id


def run_root(workbench: Path, run_id: str) -> Path:
    return workbench / "output" / "runs" / validate_run_id(run_id)


def create_stage_directory(workbench: Path, run_id: str, stage: str) -> Path:
    if stage not in {"labeling", "pipeline"}:
        raise ValueError(f"Unsupported experiment stage: {stage}")
    root = run_root(workbench, run_id)
    root.mkdir(parents=True, exist_ok=True)
    stage_dir = root / stage
    stage_dir.mkdir(exist_ok=False)
    return stage_dir


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fingerprint_inputs(workbench: Path) -> dict[str, dict[str, object]]:
    fingerprints: dict[str, dict[str, object]] = {}
    for name, relative_path in READ_ONLY_INPUTS.items():
        path = workbench / relative_path
        if not path.is_file():
            raise FileNotFoundError(f"Required input is missing: {path}")
        fingerprints[name] = {
            "path": relative_path.as_posix(),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
    return fingerprints


def fingerprint_protected_assets(workbench: Path) -> dict[str, dict[str, object]]:
    fingerprints: dict[str, dict[str, object]] = {}
    archive_path = workbench / SOURCE_ARCHIVE
    if not archive_path.is_file():
        raise FileNotFoundError(f"Protected source archive is missing: {archive_path}")
    archive_stat = archive_path.stat()
    fingerprints["source_archive"] = {
        "path": SOURCE_ARCHIVE.as_posix(),
        "verification": "metadata-only; archive content intentionally not opened",
        "bytes": archive_stat.st_size,
        "modified_ns": archive_stat.st_mtime_ns,
        "inode": archive_stat.st_ino,
    }

    latest_csvs = sorted(
        path
        for path in (workbench / "data").glob("*_latest.csv")
        if not path.name.startswith("._")
    )
    protected_files = [
        *latest_csvs,
        workbench / CANONICAL_BACKEND_ARTIFACT,
    ]
    for path in protected_files:
        if not path.is_file():
            raise FileNotFoundError(f"Protected NLP asset is missing: {path}")
        relative_path = path.relative_to(workbench)
        fingerprints[relative_path.as_posix()] = {
            "path": relative_path.as_posix(),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
    return fingerprints


def assert_inputs_unchanged(
    before: Mapping[str, Mapping[str, object]],
    after: Mapping[str, Mapping[str, object]],
) -> None:
    if before != after:
        raise RuntimeError("A protected NLP input changed during the experiment run")


def review_text_group_id(normalized_text: str) -> str:
    if not normalized_text.strip():
        raise ValueError("Cannot create a split group for blank review text")
    return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()


def deterministic_split(group_id: str) -> str:
    bucket = int(hashlib.sha256(group_id.encode("utf-8")).hexdigest()[:16], 16) % 100
    if bucket < 80:
        return "train"
    if bucket < 90:
        return "val"
    return "test"


def leakage_report(frame: Any) -> dict[str, object]:
    required = {"sample_id", "split", "review_id", "review_text", "split_group_id"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Dataset is missing leakage-audit columns: {missing}")

    def crossing_count(column: str) -> int:
        return int((frame.groupby(column, dropna=False)["split"].nunique() > 1).sum())

    return {
        "rows": int(len(frame)),
        "split_counts": {
            str(key): int(value)
            for key, value in frame["split"].value_counts().sort_index().items()
        },
        "review_cross_partition_count": crossing_count("review_id"),
        "text_cross_partition_count": crossing_count("review_text"),
        "group_cross_partition_count": crossing_count("split_group_id"),
        "duplicate_sample_id_count": int(frame["sample_id"].duplicated().sum()),
    }


def assert_zero_leakage(report: Mapping[str, object]) -> None:
    guarded_counts = (
        "review_cross_partition_count",
        "text_cross_partition_count",
        "group_cross_partition_count",
        "duplicate_sample_id_count",
    )
    failures = {key: report[key] for key in guarded_counts if report.get(key) != 0}
    if failures:
        raise RuntimeError(f"Dataset leakage validation failed: {failures}")


def artifact_records(paths: Iterable[Path], root: Path) -> list[dict[str, object]]:
    records = []
    for path in sorted(paths):
        records.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )
    return records


def runtime_versions(packages: Iterable[str]) -> dict[str, str]:
    versions: dict[str, str] = {}
    for package in packages:
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = "not-installed"
    return versions


def write_json_exclusive(path: Path, payload: Mapping[str, object]) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload
