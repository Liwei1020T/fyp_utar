from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import sys

import pandas as pd


WORKBENCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKBENCH / "src"))

from stringsense_nlp.annotation import build_gold_dataset  # noqa: E402
from stringsense_nlp.annotation import build_silver_assisted_draft  # noqa: E402
from stringsense_nlp.annotation import merge_annotations  # noqa: E402
from stringsense_nlp.annotation import validate_annotation_frame  # noqa: E402
from stringsense_nlp.boundary import artifact_records  # noqa: E402
from stringsense_nlp.boundary import assert_inputs_unchanged  # noqa: E402
from stringsense_nlp.boundary import assert_zero_leakage  # noqa: E402
from stringsense_nlp.boundary import create_stage_directory  # noqa: E402
from stringsense_nlp.boundary import deterministic_split  # noqa: E402
from stringsense_nlp.boundary import fingerprint_inputs  # noqa: E402
from stringsense_nlp.boundary import fingerprint_protected_assets  # noqa: E402
from stringsense_nlp.boundary import leakage_report  # noqa: E402
from stringsense_nlp.boundary import review_text_group_id  # noqa: E402
from stringsense_nlp.boundary import run_root  # noqa: E402
from stringsense_nlp.boundary import sha256_file  # noqa: E402
from stringsense_nlp.boundary import utc_now  # noqa: E402
from stringsense_nlp.boundary import validate_run_id  # noqa: E402
from stringsense_nlp.boundary import write_json_exclusive  # noqa: E402
from stringsense_nlp.foundation import ASPECTS  # noqa: E402
from stringsense_nlp.foundation import run_nlp01  # noqa: E402


DEFAULT_MAPPING = WORKBENCH / "config/string_name_aliases.csv"
DEFAULT_GUIDELINE = WORKBENCH / "annotation_guideline.md"


def _annotation_run_manifest(
    run_id: str,
    task: str,
    input_paths: list[Path],
    output_paths: list[Path],
    before: dict[str, dict[str, object]],
    protected: dict[str, dict[str, object]],
) -> dict[str, object]:
    root = run_root(WORKBENCH, run_id)
    return {
        "schema_version": "stringsense.nlp-annotation-run.v1",
        "run_id": run_id,
        "stage": "nlp01",
        "task": task,
        "status": "completed",
        "created_at": utc_now(),
        "inputs": [
            {
                "path": str(path),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for path in input_paths
        ],
        "protected_inputs": before,
        "protected_assets": protected,
        "artifacts": artifact_records(output_paths, root),
        "promotion": {
            "status": "not_promoted",
            "requires_human_approval": True,
            "canonical_artifact_modified": False,
        },
    }


def prepare(args: argparse.Namespace) -> dict[str, object]:
    validate_run_id(args.run_id)
    run_ids = (
        [args.run_id]
        if args.repeat == 1
        else [f"{args.run_id}-r1", f"{args.run_id}-r2"]
    )
    results = [
        run_nlp01(
            run_id,
            args.mapping.resolve(),
            args.guideline.resolve(),
            sample_size=args.sample_size,
            seed=args.seed,
            start=WORKBENCH,
        )
        for run_id in run_ids
    ]
    output: dict[str, object] = {"runs": results}
    if len(results) == 2:
        reproducible = (
            results[0]["summary_signature"] == results[1]["summary_signature"]
            and results[0]["csv_hashes"] == results[1]["csv_hashes"]
        )
        report = {
            "schema_version": "stringsense.nlp01-reproducibility.v1",
            "created_at": utc_now(),
            "run_ids": run_ids,
            "statistics_match": (
                results[0]["summary_signature"] == results[1]["summary_signature"]
            ),
            "csv_hashes_match": results[0]["csv_hashes"] == results[1]["csv_hashes"],
            "reproducible": reproducible,
            "signatures": [
                {
                    "run_id": result["run_id"],
                    "summary_signature": result["summary_signature"],
                    "csv_hashes": result["csv_hashes"],
                }
                for result in results
            ],
            "promotion": {"status": "not_promoted"},
        }
        report_root = WORKBENCH / "output/runs" / f"{args.run_id}-reproducibility"
        report_root.mkdir(parents=True, exist_ok=False)
        report_path = report_root / "reproducibility_report.json"
        write_json_exclusive(report_path, report)
        output["reproducibility_report"] = str(report_path)
        output["reproducible"] = reproducible
        if not reproducible:
            raise RuntimeError("NLP-01 repeated runs produced different results")
    return output


def validate_file(args: argparse.Namespace) -> dict[str, object]:
    frame = pd.read_csv(args.input, dtype=str, keep_default_na=False)
    return validate_annotation_frame(frame, ASPECTS, args.require_complete)


def draft(args: argparse.Namespace) -> dict[str, object]:
    validate_run_id(args.run_id)
    template = pd.read_csv(args.template, dtype=str, keep_default_na=False)
    silver = pd.read_csv(args.silver, dtype=str, keep_default_na=False)
    assistant_draft, evidence = build_silver_assisted_draft(template, silver, ASPECTS)
    validation = validate_annotation_frame(
        assistant_draft, ASPECTS, require_complete=True
    )
    before = fingerprint_inputs(WORKBENCH)
    protected = fingerprint_protected_assets(WORKBENCH)
    stage_dir = create_stage_directory(WORKBENCH, args.run_id, "nlp01")
    paths = [
        stage_dir / "assistant_annotation_draft.csv",
        stage_dir / "assistant_annotation_evidence.csv",
        stage_dir / "assistant_annotation_summary.json",
    ]
    assistant_draft.to_csv(paths[0], index=False, encoding="utf-8-sig")
    evidence.to_csv(paths[1], index=False, encoding="utf-8-sig")
    summary = {
        "schema_version": "stringsense.ai-assisted-annotation-draft.v1",
        "run_id": args.run_id,
        "created_at": utc_now(),
        "reviews": len(assistant_draft),
        "label_cells": len(evidence),
        "suggested_label_distribution": {
            str(key): int(value)
            for key, value in evidence["suggested_label"].value_counts().items()
        },
        "validation": validation,
        "annotation_provenance": "automatic_silver_conversion_not_human",
        "human_review_status": "pending",
        "gold_dataset_created": False,
        "promotion": {"status": "not_promoted"},
    }
    write_json_exclusive(paths[2], summary)
    manifest = _annotation_run_manifest(
        args.run_id,
        "ai_silver_assisted_annotation_draft",
        [args.template, args.silver],
        paths,
        before,
        protected,
    )
    write_json_exclusive(stage_dir / "manifest.json", manifest)
    write_json_exclusive(
        run_root(WORKBENCH, args.run_id) / "run_manifest.json", manifest
    )
    assert_inputs_unchanged(before, fingerprint_inputs(WORKBENCH))
    assert_inputs_unchanged(protected, fingerprint_protected_assets(WORKBENCH))
    return {
        "run_id": args.run_id,
        "assistant_annotation_draft": str(paths[0]),
        "evidence": str(paths[1]),
        "summary": summary,
    }


def merge(args: argparse.Namespace) -> dict[str, object]:
    validate_run_id(args.run_id)
    annotator_a = pd.read_csv(args.annotator_a, dtype=str, keep_default_na=False)
    annotator_b = pd.read_csv(args.annotator_b, dtype=str, keep_default_na=False)
    merged, disagreements, agreement, adjudication = merge_annotations(
        annotator_a, annotator_b, ASPECTS
    )
    before = fingerprint_inputs(WORKBENCH)
    protected = fingerprint_protected_assets(WORKBENCH)
    stage_dir = create_stage_directory(WORKBENCH, args.run_id, "nlp01")
    paths = [
        stage_dir / "merged_annotations.csv",
        stage_dir / "disagreement_report.csv",
        stage_dir / "agreement_report.json",
        stage_dir / "adjudication_template.csv",
    ]
    merged.to_csv(paths[0], index=False, encoding="utf-8-sig")
    disagreements.to_csv(paths[1], index=False, encoding="utf-8-sig")
    write_json_exclusive(paths[2], agreement)
    adjudication.to_csv(paths[3], index=False, encoding="utf-8-sig")
    manifest = _annotation_run_manifest(
        args.run_id,
        "merge_and_agreement",
        [args.annotator_a, args.annotator_b],
        paths,
        before,
        protected,
    )
    write_json_exclusive(stage_dir / "manifest.json", manifest)
    write_json_exclusive(
        run_root(WORKBENCH, args.run_id) / "run_manifest.json", manifest
    )
    assert_inputs_unchanged(before, fingerprint_inputs(WORKBENCH))
    assert_inputs_unchanged(protected, fingerprint_protected_assets(WORKBENCH))
    return {
        "run_id": args.run_id,
        "agreement": agreement,
        "disagreements": len(disagreements),
        "adjudication_template": str(paths[3]),
        "gold_dataset_created": False,
    }


def adjudicate(args: argparse.Namespace) -> dict[str, object]:
    validate_run_id(args.run_id)
    adjudicated = pd.read_csv(args.input, dtype=str, keep_default_na=False)
    gold = build_gold_dataset(adjudicated)
    gold.insert(
        2,
        "split_group_id",
        gold["normalized_text"].map(review_text_group_id),
    )
    gold.insert(3, "split", gold["split_group_id"].map(deterministic_split))
    audit_frame = gold.rename(columns={"normalized_text": "review_text"}).copy()
    audit_frame["sample_id"] = (
        audit_frame["annotation_id"] + "_" + audit_frame["aspect"]
    )
    leakage = leakage_report(audit_frame)
    assert_zero_leakage(leakage)
    before = fingerprint_inputs(WORKBENCH)
    protected = fingerprint_protected_assets(WORKBENCH)
    stage_dir = create_stage_directory(WORKBENCH, args.run_id, "nlp01")
    gold_path = stage_dir / "gold_dataset.csv"
    gold.to_csv(gold_path, index=False, encoding="utf-8-sig")
    gold_manifest_path = stage_dir / "gold_manifest.json"
    gold_manifest = {
        "schema_version": "stringsense.gold-dataset.v1",
        "run_id": args.run_id,
        "created_at": utc_now(),
        "source": {
            "path": str(args.input),
            "sha256": sha256_file(args.input),
        },
        "rows": len(gold),
        "reviews": int(gold["review_id"].nunique()),
        "aspects": sorted(gold["aspect"].unique()),
        "leakage": leakage,
        "provenance": "independent human annotations plus completed adjudication",
        "promotion": {"status": "not_promoted"},
    }
    write_json_exclusive(gold_manifest_path, gold_manifest)
    manifest = _annotation_run_manifest(
        args.run_id,
        "adjudicated_gold_export",
        [args.input],
        [gold_path, gold_manifest_path],
        before,
        protected,
    )
    write_json_exclusive(stage_dir / "manifest.json", manifest)
    write_json_exclusive(
        run_root(WORKBENCH, args.run_id) / "run_manifest.json", manifest
    )
    assert_inputs_unchanged(before, fingerprint_inputs(WORKBENCH))
    assert_inputs_unchanged(protected, fingerprint_protected_assets(WORKBENCH))
    return {
        "run_id": args.run_id,
        "gold_dataset": str(gold_path),
        "reviews": gold_manifest["reviews"],
        "leakage": leakage,
        "promotion": {"status": "not_promoted"},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="StringSense NLP-01 data foundation tools"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument(
        "--run-id", default=datetime.now(UTC).strftime("nlp01-%Y%m%dT%H%M%SZ")
    )
    prepare_parser.add_argument("--repeat", type=int, choices=(1, 2), default=1)
    prepare_parser.add_argument("--sample-size", type=int, default=450)
    prepare_parser.add_argument("--seed", type=int, default=42)
    prepare_parser.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING)
    prepare_parser.add_argument("--guideline", type=Path, default=DEFAULT_GUIDELINE)
    prepare_parser.set_defaults(handler=prepare)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--input", type=Path, required=True)
    validate_parser.add_argument("--require-complete", action="store_true")
    validate_parser.set_defaults(handler=validate_file)

    draft_parser = subparsers.add_parser("draft")
    draft_parser.add_argument("--run-id", required=True)
    draft_parser.add_argument("--template", type=Path, required=True)
    draft_parser.add_argument("--silver", type=Path, required=True)
    draft_parser.set_defaults(handler=draft)

    merge_parser = subparsers.add_parser("merge")
    merge_parser.add_argument("--run-id", required=True)
    merge_parser.add_argument("--annotator-a", type=Path, required=True)
    merge_parser.add_argument("--annotator-b", type=Path, required=True)
    merge_parser.set_defaults(handler=merge)

    adjudicate_parser = subparsers.add_parser("adjudicate")
    adjudicate_parser.add_argument("--run-id", required=True)
    adjudicate_parser.add_argument("--input", type=Path, required=True)
    adjudicate_parser.set_defaults(handler=adjudicate)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = args.handler(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
