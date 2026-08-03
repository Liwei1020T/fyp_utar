from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd


WORKBENCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKBENCH / "src"))

from stringsense_nlp.boundary import RUN_SCHEMA_VERSION  # noqa: E402
from stringsense_nlp.boundary import artifact_records  # noqa: E402
from stringsense_nlp.boundary import assert_inputs_unchanged  # noqa: E402
from stringsense_nlp.boundary import create_stage_directory  # noqa: E402
from stringsense_nlp.boundary import fingerprint_inputs  # noqa: E402
from stringsense_nlp.boundary import fingerprint_protected_assets  # noqa: E402
from stringsense_nlp.boundary import run_root  # noqa: E402
from stringsense_nlp.boundary import runtime_versions  # noqa: E402
from stringsense_nlp.boundary import sha256_file  # noqa: E402
from stringsense_nlp.boundary import utc_now  # noqa: E402
from stringsense_nlp.boundary import validate_run_id  # noqa: E402
from stringsense_nlp.boundary import write_json_exclusive  # noqa: E402
from stringsense_nlp.foundation import ASPECTS  # noqa: E402
from stringsense_nlp.review_html import build_review_payload  # noqa: E402
from stringsense_nlp.review_html import render_annotation_review_html  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an offline StringSense annotation-review HTML"
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    validate_run_id(args.run_id)
    draft_path = args.draft.resolve()
    evidence_path = args.evidence.resolve()
    draft = pd.read_csv(draft_path, dtype=str, keep_default_na=False)
    evidence = pd.read_csv(evidence_path, dtype=str, keep_default_na=False)
    payload = build_review_payload(
        draft,
        evidence,
        ASPECTS,
        args.run_id,
        sha256_file(draft_path),
        sha256_file(evidence_path),
    )
    html = render_annotation_review_html(payload)

    inputs_before = fingerprint_inputs(WORKBENCH)
    protected_before = fingerprint_protected_assets(WORKBENCH)
    stage_dir = create_stage_directory(WORKBENCH, args.run_id, "nlp01")
    root = run_root(WORKBENCH, args.run_id)
    html_path = stage_dir / "annotation_review.html"
    with html_path.open("x", encoding="utf-8") as handle:
        handle.write(html)
    summary_path = stage_dir / "annotation_review_summary.json"
    summary = {
        "schema_version": "stringsense.annotation-review-html.v1",
        "run_id": args.run_id,
        "created_at": utc_now(),
        "reviews": len(draft),
        "label_cells": len(evidence),
        "flagged_label_cells": int(
            evidence["needs_manual_review"].isin(("1", "true", "True")).sum()
        ),
        "source": {
            "draft": {"path": str(draft_path), "sha256": sha256_file(draft_path)},
            "evidence": {
                "path": str(evidence_path),
                "sha256": sha256_file(evidence_path),
            },
        },
        "offline_single_file": True,
        "human_review_status": "pending",
        "gold_dataset_created": False,
        "promotion": {"status": "not_promoted"},
    }
    write_json_exclusive(summary_path, summary)
    artifacts = artifact_records((html_path, summary_path), root)
    manifest = {
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": args.run_id,
        "stage": "nlp01",
        "task": "offline_annotation_review_html",
        "status": "completed",
        "created_at": utc_now(),
        "inputs": inputs_before,
        "protected_assets": protected_before,
        "source_files": summary["source"],
        "runtime_versions": runtime_versions(("pandas",)),
        "artifacts": artifacts,
        "promotion": {
            "status": "not_promoted",
            "requires_human_approval": True,
            "canonical_artifact_modified": False,
        },
    }
    stage_manifest = stage_dir / "manifest.json"
    write_json_exclusive(stage_manifest, manifest)
    write_json_exclusive(
        root / "run_manifest.json",
        {
            **manifest,
            "stage_manifest": "nlp01/manifest.json",
            "stage_manifest_sha256": sha256_file(stage_manifest),
        },
    )
    assert_inputs_unchanged(inputs_before, fingerprint_inputs(WORKBENCH))
    assert_inputs_unchanged(protected_before, fingerprint_protected_assets(WORKBENCH))
    print(
        json.dumps(
            {
                "run_id": args.run_id,
                "annotation_review_html": str(html_path),
                "summary": summary,
                "promotion": manifest["promotion"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
