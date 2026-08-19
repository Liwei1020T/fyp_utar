#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


WORKBENCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKBENCH / "src"))

from stringsense_nlp.bert_inference import predict_one  # noqa: E402
from stringsense_nlp.bert_inference import run_inference_pipeline  # noqa: E402
from stringsense_nlp.bert_review import run_candidate_review  # noqa: E402
from stringsense_nlp.bert_review import run_recommendation_optimization  # noqa: E402
from stringsense_nlp.bert_review import run_threshold_sensitivity  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run frozen MacBERT offline inference")
    subparsers = parser.add_subparsers(dest="command", required=True)

    predict = subparsers.add_parser("predict", help="Predict one review/aspect input")
    predict.add_argument("--model-run-id", required=True)
    predict.add_argument("--string", dest="canonical_string_name", required=True)
    predict.add_argument("--aspect", required=True)
    predict.add_argument("--review-text", required=True)
    predict.add_argument("--source-review-id", default="")
    predict.add_argument("--device", choices=("auto", "cpu", "mps"), default="auto")

    run = subparsers.add_parser("run", help="Generate a run-scoped 12x9 candidate")
    run.add_argument("--run-id", required=True)
    run.add_argument("--model-run-id", required=True)
    run.add_argument("--dataset-run-id", required=True)
    run.add_argument("--batch-size", type=int, default=32)
    run.add_argument("--device", choices=("auto", "cpu", "mps"), default="auto")

    review = subparsers.add_parser(
        "review", help="Review an immutable candidate without promotion"
    )
    review.add_argument("--run-id", required=True)
    review.add_argument("--source-run-id", required=True)
    review.add_argument(
        "--decisions-path",
        type=Path,
        default=Path("config/macbert_operational_review_20260811_v1.csv"),
    )

    sensitivity = subparsers.add_parser(
        "sensitivity", help="Compare a lower threshold without replacing the pilot"
    )
    sensitivity.add_argument("--run-id", required=True)
    sensitivity.add_argument("--source-run-id", required=True)
    sensitivity.add_argument("--owner-confirmation-run-id", required=True)
    sensitivity.add_argument("--confidence-threshold", type=float, required=True)

    optimize = subparsers.add_parser(
        "optimize",
        help="Compare preference weights with read-only system catalog facts",
    )
    optimize.add_argument("--run-id", required=True)
    optimize.add_argument("--source-run-id", required=True)
    optimize.add_argument("--catalog-snapshot", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "predict":
            result = predict_one(
                args.model_run_id,
                args.canonical_string_name,
                args.aspect,
                args.review_text,
                source_review_id=args.source_review_id,
                device=args.device,
                start=WORKBENCH,
            )
        elif args.command == "run":
            result = run_inference_pipeline(
                args.run_id,
                args.model_run_id,
                args.dataset_run_id,
                batch_size=args.batch_size,
                device=args.device,
                start=WORKBENCH,
            )
        elif args.command == "review":
            decisions_path = args.decisions_path
            if not decisions_path.is_absolute():
                decisions_path = WORKBENCH / decisions_path
            result = run_candidate_review(
                args.run_id,
                args.source_run_id,
                decisions_path,
                start=WORKBENCH,
            )
        elif args.command == "sensitivity":
            result = run_threshold_sensitivity(
                args.run_id,
                args.source_run_id,
                args.owner_confirmation_run_id,
                args.confidence_threshold,
                start=WORKBENCH,
            )
        else:
            catalog_snapshot = args.catalog_snapshot
            if not catalog_snapshot.is_absolute():
                catalog_snapshot = WORKBENCH / catalog_snapshot
            result = run_recommendation_optimization(
                args.run_id,
                args.source_run_id,
                catalog_snapshot,
                start=WORKBENCH,
            )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
